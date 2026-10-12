# Arabic video starter agent guidance

Before drafting or adapting Arabic narration, read [the dialect index](dialects/README.md)
and the guide matching the user's requested dialect or the config's `dialect`.
Load only the relevant guide. The supplied examples use
[Saudi Najdi](dialects/saudi-najdi.md),
[Egyptian Cairene](dialects/eg-cairene.md) and [Emirati](dialects/ae.md).

Apply the guide to narration wording. Preserve approved scripts unless adaptation
is requested, and keep the user's preferred language for your own replies.
Choose forms of address and any foreign-language wording for the brief and audience.
Follow the index's guidance when a variety has no guide; do not silently
substitute another regional dialect.

Use the existing `arabic-voiceover` skill or accepted narration WAVs as described in
[README.md](README.md). Choose a real ready voice from the catalog, keep the same
voice across scenes, and send only the scene script to speech generation. The
dialect references are agent context; never append them to TTS input.

Keep accepted audio when revising other scenes or visuals. Measure actual audio
duration and listen before judging pronunciation or dialect suitability.

Keep these examples customer-facing: include narration guidance, runnable setup
instructions and sample assets. Keep internal testing notes, infrastructure
locations, research provenance and dataset statistics outside this directory.
