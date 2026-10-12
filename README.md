# Arabic video starter

Create an Arabic video with your coding agent, Sawtak Arabi narration and Remotion.
Give the agent this repository, your brief, dialect and brand assets:

> Use https://github.com/SawtakArabi/arabic-video-starter to create a vertical product
> advertisement for my brief with Saudi Najdi narration from Sawtak Arabi. Read the
> repository's agent instructions and dialect guide. Keep one voice across scenes,
> time the video from the recordings, and return the MP4 and editable project.

The agent can generate narration through the official
[arabic-voiceover skill](https://github.com/SawtakArabi/skill), or use recordings
from an already connected Sawtak Arabi MCP. Speech generation uses your Sawtak
balance. A coding or rendering environment runs Remotion to create the video.

Three editable vertical video drafts share one ordinary Remotion composition.
Each has original SVG artwork, its own identity and a concrete brief.

| Example | Config | Brief and editable scene plan | Dialect guide |
|---|---|---|---|
| Saudi Najdi product advertisement: fictional Luma mug | `configs/najdi.json` | [Saudi ad](briefs/saudi-ad.md) | [Saudi Najdi](dialects/saudi-najdi.md) |
| Egyptian Cairene explainer: a three-step paper-planning routine | `configs/egyptian.json` | [Egyptian explainer](briefs/egyptian-explainer.md) | [Egyptian Cairene](dialects/eg-cairene.md) |
| Emirati property concept: an imagined two-bedroom home | `configs/emirati.json` | [Emirati property](briefs/emirati-property.md) | [Emirati](dialects/ae.md) |

The JSON files supply draft Arabic narration, independent display copy, dialect
metadata, one voice, images, logo and colors. All voices start unset. These are
draft scripts; narration is not included. Review the wording and recordings
with someone familiar with the intended dialect before publishing. The property
example is explicitly fictional and is not an offer for sale.

This is an ordinary Remotion project. It uses the actual pinned `remotion`,
`@remotion/cli`, `@remotion/media` and `@remotion/fonts` packages. Speech goes
through the installed **arabic-voiceover skill's unchanged `scripts/generate.py`**,
which uses the official OpenAI SDK. `scripts/prepare.py` names/reuses scene files,
accepts existing WAVs, invokes that helper when needed, measures audio and writes
Remotion input props.

## Dialect guidance for agents

Before drafting or adapting narration, read the [dialect index](dialects/README.md)
and the file for the requested variety. The directory contains 23 dialect guides
with Arabic grammar, vocabulary and examples. [AGENTS.md](AGENTS.md) and
[CLAUDE.md](CLAUDE.md) direct coding agents to
these references. The guides inform the scene scripts; only the finished script
is sent to speech generation. Preserve supplied wording unless adaptation is requested.

## Clone the project

Use Node 22+, Python 3.10+, and a Linux rendering machine with the libraries
required by [Remotion's Linux guide](https://www.remotion.dev/docs/miscellaneous/linux-dependencies).
Install dependencies and render on your own local or remote rendering machine.

Your agent can clone this public repository directly. To set it up yourself, run:

```bash
git clone https://github.com/SawtakArabi/arabic-video-starter.git
cd arabic-video-starter
npm ci
```

The original source and illustrations use the included MIT license. Remotion
and installed fonts keep their own terms; read [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
Keep generated recordings, private receipts and environment settings out of Git;
the supplied `.gitignore` excludes them.

## First render without credentials

This preview uses standard Python `wave` to create silence and the preparation
script's existing imported-WAV support. It does not install the speech skill,
call an API, submit narration or consume credits. Run it **on the rendering
machine** after `npm ci`. Source configs remain unchanged; preview copies live
under ignored `build/` and carry a visible synthetic notice.

```bash
python3 - <<'PY_PREVIEW'
import json
from pathlib import Path
import subprocess
import sys
import wave

root = Path.cwd()
(root / "build").mkdir(exist_ok=True)
audio = root / "public/audio/silent-preview.wav"
audio.parent.mkdir(parents=True, exist_ok=True)
if not audio.exists():
    with wave.open(str(audio), "wb") as wav:
        wav.setparams((1, 2, 24000, 0, "NONE", "not compressed"))
        wav.writeframes(bytes(7200 * 2))
with wave.open(str(audio), "rb") as wav:
    if ((wav.getnchannels(), wav.getsampwidth(), wav.getframerate(),
         wav.getnframes(), wav.getcomptype()) != (1, 2, 24000, 7200, "NONE")
            or wav.readframes(7201) != bytes(7200 * 2)):
        raise SystemExit("Existing preview WAV is not the expected silence; keep it and use a new filename.")
for name in ("najdi", "egyptian", "emirati"):
    config = json.loads((root / f"configs/{name}.json").read_text())
    config["voice"] = "synthetic-silence"
    config["notice"] = "SILENT PREVIEW / NOT NARRATION"
    for scene in config["scenes"]:
        scene["audio"] = "audio/silent-preview.wav"
    source = root / f"build/{name}-preview-source.json"
    source.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    subprocess.run([sys.executable, "scripts/prepare.py", str(source),
                    "--helper", "build/no-speech-helper",
                    "--output", f"build/{name}-preview.json"], check=True)
PY_PREVIEW
npm run typecheck
npm test
npm run render -- out/najdi-preview.mp4 --props=build/najdi-preview.json
npm run render -- out/egyptian-preview.mp4 --props=build/egyptian-preview.json
npm run render -- out/emirati-preview.mp4 --props=build/emirati-preview.json
```

Each supplied config has a four-second minimum scene hold, so this silent
preview is 12 seconds. It checks the visual/edit/render path; it says nothing
about pronunciation or whether real speech will fit that duration. Remotion
may download its browser on first use; keep that download on the rendering
machine. The commands refuse to overwrite existing MP4s: use new output names
for revisions. Studio uses the same props, for example
`npm run studio -- --props=build/egyptian-preview.json` through an SSH tunnel.

## Add actual narration

Keep the selected brief and its [dialect guide](dialects/README.md) open while editing.
Use already accepted WAVs as
[described below](#use-existing-narration-wavs), or explicitly generate
paid narration through the unchanged skill. The silent-preview config is
only for previewing; use the original `configs/*.json` for actual speech.

1. Follow the [released skill setup](https://sawtakarabi.ai/docs/agent-skill)
   to install `arabic-voiceover` in your agent and locate its directory.
   Set the path below to that existing installation. Keep the helper unchanged.

   ```bash
   export VOICEOVER_SKILL="$HOME/.agents/skills/arabic-voiceover"
   export SAWTAK_VOICEOVER_HELPER="$VOICEOVER_SKILL/scripts/generate.py"
   python3 -m venv .venv
   .venv/bin/python -m pip install -r "$VOICEOVER_SKILL/requirements.txt"
   ```

2. Configure `SAWTAK_API_KEY` using your execution environment's secret field or
   a hidden shell prompt. Get a key from [API Keys](https://sawtakarabi.ai/dashboard/api-keys).
   Never put it in a config, source file, command argument or chat. The default
   endpoint is Sawtak's public API; generation consumes your own Sawtak credits.
   An explicitly configured `SAWTAK_API_BASE_URL` overrides that endpoint.

   ```bash
   .venv/bin/python "$SAWTAK_VOICEOVER_HELPER" doctor
   mkdir -p build
   .venv/bin/python "$SAWTAK_VOICEOVER_HELPER" voices --dialect eg-cairene --limit 25 > build/voices.json
   ```

   Open `build/voices.json` in an editor and choose an actual returned ID with
   `status: ready`. Follow `next_cursor` with `--after` if needed. For the other
   configs, use exact catalog codes `ae` (Emirati) or `saudi-najdi`. A dialect
   filter is metadata, not a pronunciation guarantee. The **voice** determines
   pronunciation; the config label is not sent as an unsupported API field.

3. Edit `configs/egyptian.json` and set `voice` to that ID. Keep one voice across
   its scenes. The alternative configs are `emirati.json` and `najdi.json`.
   Edit each scene's `script` without changing its stable `id`; `title` and
   `caption` are independent display copy, not word-aligned subtitles.

   ```bash
   .venv/bin/python scripts/prepare.py configs/egyptian.json
   npm run studio -- --props=build/egyptian.json
   npm run render -- out/egyptian.mp4 --props=build/egyptian.json
   ```

   Open Studio through an SSH tunnel when using a remote machine. The render
   uses one browser worker by default to limit CPU/memory. Remotion may download
   its browser on first use; do that on the rendering machine only. The command
   refuses to overwrite an existing MP4; choose another output name for revisions.

## Revise just one scene

Change the `script` in the second scene, then run the same prepare command and
render to `out/egyptian-v2.mp4`. Its log should show `reused: true` for scenes one
and three, and `reused: false` only for scene two. Filenames hash text, voice,
dialect, endpoint and speech settings. Changing only images, colors, titles or
captions never regenerates speech. Reverting to earlier text reuses its file.

Completed audio, the helper's JSON receipt and source text remain under
`public/audio/`. Do not commit this directory or publish it as a website: it
contains scripts and operation metadata. Back it up with your editable project.
The final MP4 needs none of those sidecars. `build/*.json` is generated timing
data; change source configs rather than hand-editing it.

## Use existing narration WAVs

If your agent already has Sawtak Arabi MCP connected, it can generate each scene
there, wait for completion and retrieve the recording with `get_voiceover`.
Save each available WAV in the project before its download link expires, then
use the file-import path below. MCP supplies narration; the coding environment
runs this project's renderer. If a completed request has no saved recording,
inspect that request and report the missing audio rather than automatically
starting another paid take.

Copy accepted narration WAVs to the rendering machine's `public/audio/` directory.
These can be your own recordings or finalized speech outputs you have permission
to use. Keep the files on disk rather than depending on temporary download URLs.
Set the config's top-level `voice` to the selected Sawtak voice ID, or an informative
narrator label such as `my-accepted-narrator` for your own recordings; the supplied
configs start with `voice: null`. In each imported scene, add a relative `audio` filename:

```json
"audio": "audio/accepted-scene-two.wav"
```

Run the same preparation and rendering commands. A scene with `audio` uses that
file, measures its duration and never calls the speech helper. It needs no API key
or skill receipt. Other scenes keep their normal file reuse/generation behavior.
Every supplied audio file is checked before any scene can generate paid speech.

Use complete 24 kHz mono PCM16 WAVs. Keep the config's script and voice metadata
consistent with the selected take; file validation cannot verify spoken words or
voice identity. Editing the script does not change an explicitly supplied WAV.
For a revision, save the new take under a new filename and update that scene's
`audio` field. A failed render can reuse the same accepted files without synthesis.
For speech generated through the API, confirm that its operation completed and
that its reported PCM byte count agrees with the saved recording. A valid WAV
header alone cannot establish that the server delivered the entire utterance.
See [stream completion](https://sawtakarabi.ai/docs/streaming). The starter checks
file integrity; it does not independently query or certify a generation outcome.

Preparation never overwrites recordings and stops on partial, `started`,
`streaming` or unknown outcomes. Read the sidecar and use the skill's `inspect
<operation-id>` command before deciding whether to generate again. A missing
operation is unknown, not evidence of a free failure. Do not delete sidecars to
force an automatic retry. Successful earlier scenes stay reusable after an error.

## Timing, assets and typography

Every clip is validated as nonempty 24 kHz mono PCM16 WAV, including its payload
length. Scene duration is the measured WAV duration rounded **up** to frames,
plus a lead and tail pause, with a four-second minimum visual hold in these
configs. They use 30 fps. Long speech extends the scene; it is never truncated or sped
up. For a fixed duration brief, revise the script and only regenerate changed
scenes. The workflow does not create word timestamps or certify spoken content.

`src/Video.tsx` is the editable composition: stock `Series.Sequence` orders scenes,
`Sequence` offsets narration, and `Audio` plays it. Arabic uses browser shaping,
`lang="ar"`, RTL direction and right alignment, with no manual letter reversal.
Keep titles short (about two lines) and captions to two or three lines; preview
all scenes after copy changes. Long content can exceed the fixed vertical layout.

Place your images and logo inside `public/` and reference relative paths in the
config. The supplied SVGs are original editable illustrations, not customer assets
or product photographs. Their shapes need no external font or image download.
`brand.category` edits the short English header, and `notice` edits the footer;
keep the property example's fictional-home disclosure in a real narrated version. Brand colors accept six-digit hex. The font is
**Noto Sans Arabic**, distributed under **SIL Open Font License 1.1** by the
pinned Fontsource package. Preparation copies its font files and license into
`public/fonts/`; no proprietary Sawtak font is included. `loadFont()` blocks the
render until those local fonts are ready.

## Verification and reuse references

Run `npm run typecheck` and `npm test` in the starter directory. The tests protect unchanged
clip reuse, single-scene revisions, uncertain-outcome refusal and truncated WAV
rejection. Probe each finished MP4 with `ffprobe` and inspect the beginning,
scene boundaries and ending; a successful encode does not prove pronunciation.

Primary APIs used unchanged:
[Series](https://www.remotion.dev/docs/series),
[Audio](https://www.remotion.dev/docs/media/audio),
[calculateMetadata](https://www.remotion.dev/docs/calculate-metadata),
[local font loader](https://www.remotion.dev/docs/fonts-api/load-font), and
[renderer CLI](https://www.remotion.dev/docs/cli/render).
Remotion is source available under its [own license](https://github.com/remotion-dev/remotion/blob/v4.0.534/LICENSE.md),
not a blanket OSI license; review its company-size terms for your use. The font
package retains its separate OFL license. Version pins are explicit and the
lockfile records the resolved dependency graph.
