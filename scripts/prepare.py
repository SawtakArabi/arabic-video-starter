#!/usr/bin/env python3
"""Prepare measured Remotion props from existing WAVs or the unchanged skill CLI."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import wave

ROOT = Path(__file__).resolve().parents[1]
SETTINGS = {"model": "arabic-tts-1", "response_format": "pcm", "sample_rate": 24000,
            "enhance_pronunciation": True}


def public_asset(value):
    if not isinstance(value, str) or Path(value).is_absolute() or ".." in Path(value).parts:
        raise ValueError("Assets must use relative paths inside public/.")
    path = (ROOT / "public" / value).resolve()
    if not path.is_relative_to((ROOT / "public").resolve()) or not path.is_file():
        raise ValueError("Assets must be existing files inside public/.")
    return value


def read_config(path, voice):
    config = json.loads(path.read_text(encoding="utf-8"))
    config["voice"] = voice or config.get("voice")
    if not config["voice"] or not isinstance(config["voice"], str):
        raise ValueError("Set voice to one ready catalog ID, or pass --voice. See README.")
    if not isinstance(config.get("dialect"), str) or not config["dialect"]:
        raise ValueError("A catalog dialect code is required.")
    if config.get("fps", 30) not in (24, 25, 30, 60):
        raise ValueError("fps must be 24, 25, 30 or 60.")
    for key in ("lead_seconds", "tail_seconds", "min_scene_seconds"):
        value = config.get(key, {"lead_seconds": 0.2, "tail_seconds": 0.4, "min_scene_seconds": 3}[key])
        if not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 60:
            raise ValueError("Scene timing values must be finite seconds between 0 and 60.")
        config[key] = value
    public_asset(config["brand"]["logo"])
    for key in ("background", "ink", "accent"):
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", config["brand"][key]):
            raise ValueError("Brand colors must be six-digit hex colors.")
    if not 1 <= len(config["scenes"]) <= 30:
        raise ValueError("Use 1 to 30 scenes.")
    ids = set()
    for scene in config["scenes"]:
        if not re.fullmatch(r"[a-z0-9-]{1,48}", scene["id"]) or scene["id"] in ids:
            raise ValueError("Scene IDs must be unique lowercase letters, digits or hyphens.")
        ids.add(scene["id"])
        text = scene["script"]
        if not isinstance(text, str) or not text.strip() or len(text) > 10000 or any(len(w) > 400 for w in text.split()):
            raise ValueError("Each scene needs 1-10000 characters; words must be <=400 characters.")
        if not isinstance(scene["title"], str) or not isinstance(scene["caption"], str):
            raise ValueError("Each scene needs a title and caption.")
        public_asset(scene["image"])
        if "audio" in scene:
            public_asset(scene["audio"])
    return config


def audio_path(config, scene, base_url):
    # Only narration inputs belong here. Images, colors and display copy do not.
    content = {"text": scene["script"], "voice": config["voice"], "dialect": config["dialect"],
               "base_url": base_url.rstrip("/"), "settings": SETTINGS}
    digest = hashlib.sha256(json.dumps(content, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return ROOT / "public" / "audio" / f"{scene['id']}-{digest}.wav"


def measure_completed(path, voice):
    metadata = json.loads(path.with_suffix(".json").read_text())
    if metadata.get("state") != "completed" or metadata.get("voice") != voice or metadata.get("settings") != SETTINGS:
        raise ValueError("Recording is incomplete or does not match the selected voice/settings. Inspect the skill sidecar before another generation.")
    return measure_wav(path)


def measure_wav(path):
    with wave.open(str(path), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getcomptype()) != (1, 2, 24000, "NONE"):
            raise ValueError("Expected a finalized 24 kHz mono PCM16 WAV.")
        frames = wav.getnframes()
        if frames <= 0:
            raise ValueError("Recording has no audio frames.")
        # Read incrementally to detect a truncated payload without accumulating audio.
        actual = 0
        while chunk := wav.readframes(24000):
            actual += len(chunk)
        if actual != frames * 2:
            raise ValueError("Recording WAV is truncated. Do not regenerate automatically.")
        return frames / 24000


def copy_fonts():
    package = ROOT / "node_modules" / "@fontsource" / "noto-sans-arabic"
    target = ROOT / "public" / "fonts"
    files = [package / "files" / f"noto-sans-arabic-{subset}-{weight}-normal.woff2"
             for subset in ("arabic", "latin") for weight in ("500", "700")]
    files.append(package / "LICENSE")
    if not all(path.is_file() for path in files):
        raise ValueError("Install locked npm dependencies on the rendering machine first.")
    target.mkdir(parents=True, exist_ok=True)
    for path in files:
        shutil.copyfile(path, target / path.name)


def prepare(config, helper, output):
    base_url = os.environ.get("SAWTAK_API_BASE_URL", "https://api.sawtakarabi.ai/v1")
    fps = config.get("fps", 30)
    lead = math.ceil(config["lead_seconds"] * fps)
    tail = math.ceil(config["tail_seconds"] * fps)
    # Validate every supplied file before any scene can submit paid speech.
    imported = {
        scene["id"]: (ROOT / "public" / public_asset(scene["audio"]))
        for scene in config["scenes"] if "audio" in scene
    }
    imported_seconds = {key: measure_wav(path) for key, path in imported.items()}
    scenes = []
    for scene in config["scenes"]:
        path = imported.get(scene["id"]) or audio_path(config, scene, base_url)
        artifacts = [path, path.with_suffix(".json"), path.with_suffix(".partial.wav")]
        reused = any(p.exists() for p in artifacts)
        if scene["id"] in imported:
            # Explicitly selected files never invoke the synthesis helper or
            # pretend to have a skill receipt. Their script/voice are caller metadata.
            seconds = imported_seconds[scene["id"]]
        elif reused:
            # A partial file or started sidecar is not permission to submit again.
            if not path.exists() or not path.with_suffix(".json").exists() or path.with_suffix(".partial.wav").exists():
                raise ValueError(f"Uncertain existing recording for {scene['id']}; inspect its sidecar. No retry was made.")
        else:
            if not helper.is_file():
                raise ValueError("Set SAWTAK_VOICEOVER_HELPER to the installed skill's scripts/generate.py.")
            path.parent.mkdir(parents=True, exist_ok=True)
            text_path = path.with_suffix(".txt")
            text_path.write_text(scene["script"], encoding="utf-8")
            result = subprocess.run([sys.executable, str(helper), "generate", "--voice", config["voice"],
                                     "--text-file", str(text_path), "--output", str(path),
                                     "--enhance-pronunciation"], capture_output=True, text=True)
            if result.returncode:
                # Escape provider/skill diagnostics; never render Arabic in terminals.
                print(result.stderr.encode("ascii", "backslashreplace").decode(), file=sys.stderr)
                raise ValueError(f"Skill generation stopped for {scene['id']}. Successful clips were retained; no automatic retry.")
        if scene["id"] not in imported:
            seconds = measure_completed(path, config["voice"])
        duration = max(math.ceil(config["min_scene_seconds"] * fps), lead + math.ceil(seconds * fps) + tail)
        scenes.append({key: scene[key] for key in ("id", "title", "caption", "image") } | {
            "audio": path.relative_to(ROOT / "public").as_posix(), "audioStartFrame": lead,
            "durationInFrames": duration, "audioSeconds": seconds})
        print(json.dumps({"scene": scene["id"], "reused": reused, "audio_seconds": seconds,
                          "duration_frames": duration}, ensure_ascii=True))
    props = {"fps": fps, "width": 1080, "height": 1920, "brand": config["brand"], "scenes": scenes}
    if config.get("notice"):
        props["notice"] = config["notice"]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(props, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"props": str(output), "duration_seconds": sum(s["durationInFrames"] for s in scenes) / fps}, ensure_ascii=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    parser.add_argument("--voice", help="One ready voice ID from the skill's live catalog")
    parser.add_argument("--helper", type=Path, default=Path(os.environ.get("SAWTAK_VOICEOVER_HELPER", "~/.agents/skills/arabic-voiceover/scripts/generate.py")).expanduser())
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        config = read_config(args.config, args.voice)
        copy_fonts()
        prepare(config, args.helper.resolve(), args.output or ROOT / "build" / f"{args.config.stem}.json")
    except (ValueError, OSError, KeyError, TypeError, wave.Error) as exc:
        print(str(exc).encode("ascii", "backslashreplace").decode(), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
