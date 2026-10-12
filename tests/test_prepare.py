import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave

SPEC = importlib.util.spec_from_file_location("prepare", Path(__file__).parents[1] / "scripts/prepare.py")
prepare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prepare)


class RecordingReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patch = patch.object(prepare, "ROOT", self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)
        self.config = {"voice": "voice-1", "dialect": "eg-cairene", "fps": 30,
                       "lead_seconds": 0.2, "tail_seconds": 0.4, "min_scene_seconds": 0,
                       "brand": {}, "scenes": [dict(id=x, script="text " + x, title=x,
                       caption="caption", image="image.svg") for x in ["one", "two", "three"]]}
        self.base = "https://speech.example.test/v1"

    def complete(self, scene, duration=1.01):
        path = prepare.audio_path(self.config, scene, self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(path), "wb") as wav:
            wav.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
            wav.writeframes(b"\0\0" * int(duration * 24000))
        path.with_suffix(".json").write_text(json.dumps({"state": "completed", "voice": "voice-1", "settings": prepare.SETTINGS}))
        return path

    def test_only_changed_narration_gets_new_path(self):
        before = [prepare.audio_path(self.config, s, self.base) for s in self.config["scenes"]]
        self.config["scenes"][0]["title"] = "new display title"
        self.config["scenes"][1]["script"] += " revised"
        after = [prepare.audio_path(self.config, s, self.base) for s in self.config["scenes"]]
        self.assertEqual(before[0], after[0])
        self.assertNotEqual(before[1], after[1])
        self.assertEqual(before[2], after[2])
        self.assertNotEqual(after[0], prepare.audio_path(self.config, self.config["scenes"][0], "https://api.sawtakarabi.ai/v1"))

    def test_completed_reuse_never_invokes_helper_and_rounds_up(self):
        for scene in self.config["scenes"]:
            self.complete(scene)
        output = self.root / "props.json"
        with patch.dict(prepare.os.environ, {"SAWTAK_API_BASE_URL": self.base}), patch.object(prepare.subprocess, "run") as run:
            prepare.prepare(self.config, self.root / "missing-helper.py", output)
            run.assert_not_called()
        props = json.loads(output.read_text())
        self.assertEqual(props["scenes"][0]["durationInFrames"], 6 + 31 + 12)
        self.assertEqual(props["scenes"][0]["audioSeconds"], 1.01)

    def test_unknown_recording_cannot_trigger_new_submission(self):
        path = prepare.audio_path(self.config, self.config["scenes"][0], self.base)
        path.parent.mkdir(parents=True)
        path.with_suffix(".json").write_text('{"state":"started"}')
        with patch.dict(prepare.os.environ, {"SAWTAK_API_BASE_URL": self.base}), patch.object(prepare.subprocess, "run") as run:
            with self.assertRaisesRegex(ValueError, "Uncertain"):
                prepare.prepare(self.config, self.root / "helper.py", self.root / "props.json")
            run.assert_not_called()

    def test_truncated_completed_wav_is_rejected(self):
        path = self.complete(self.config["scenes"][0])
        path.write_bytes(path.read_bytes()[:-2])
        with self.assertRaisesRegex(ValueError, "truncated"):
            prepare.measure_completed(path, "voice-1")

    def test_absolute_public_asset_is_rejected_before_speech(self):
        asset = self.root / "public" / "logo.svg"
        asset.parent.mkdir(parents=True)
        asset.write_text("<svg/>")
        self.assertEqual(prepare.public_asset("logo.svg"), "logo.svg")
        with self.assertRaisesRegex(ValueError, "relative"):
            prepare.public_asset(str(asset))

    def test_explicit_wavs_need_no_skill_receipts_or_generation(self):
        for scene in self.config["scenes"]:
            path = self.complete(scene, duration=1.01)
            path.with_suffix(".json").unlink()
            scene["audio"] = path.relative_to(self.root / "public").as_posix()
        output = self.root / "props.json"
        with patch.object(prepare.subprocess, "run") as run:
            prepare.prepare(self.config, self.root / "missing-helper.py", output)
            run.assert_not_called()
        props = json.loads(output.read_text())
        self.assertEqual(props["scenes"][1]["audio"], self.config["scenes"][1]["audio"])
        self.assertEqual(props["scenes"][1]["durationInFrames"], 49)

    def test_bad_imported_later_scene_prevents_earlier_paid_submission(self):
        scene = self.config["scenes"][2]
        path = self.complete(scene)
        path.write_bytes(path.read_bytes()[:-2])
        scene["audio"] = path.relative_to(self.root / "public").as_posix()
        with patch.object(prepare.subprocess, "run") as run:
            with self.assertRaisesRegex(ValueError, "truncated"):
                prepare.prepare(self.config, self.root / "helper.py", self.root / "props.json")
            run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
