# Synthetic narration quality

## Generation order

1. Inspect candidate reference clips.
2. Estimate median fundamental frequency when timbres differ substantially.
3. Generate a 10-second hook test.
4. Compare naturalness, intelligibility, sibilance, breath noise, sentence endings, and fatigue.
5. Synthesize short segments at the model's native sample rate.
6. Assemble segments with digital silence.
7. Apply only necessary global timing and gain changes.

## CosyVoice direction

Request:

- clean studio narration;
- no breath, inhale, gasp, panting, or exaggerated air noise;
- direct silence between sentences;
- varied but controlled sentence endings;
- conversational explanation, not news, trailer, recitation, or marketing delivery;
- clear numbers and restrained emphasis.

Short segments reduce unwanted generated breaths and make individual regeneration cheap.

## Processing guardrails

Keep an untouched raw master.

Safe defaults:

- preserve native sample rate;
- small `atempo` correction, usually 0.95-1.15;
- simple gain reduction when peaks approach 0 dBFS;
- PCM WAV master, then AAC only during video assembly.

Avoid by default:

- hard noise gates;
- aggressive spectral denoising;
- upsampling that adds no information;
- strong high-pass/low-pass filtering;
- multistage loudness normalization;
- heavy compression or limiting.

These processes can turn breaths into pumping, create sharp consonants, or add metallic artifacts. If breath or sibilance is part of the generated voice, regenerate the segment or change the reference timbre before using corrective processing.

## Timeline after speed changes

If the final audio uses `atempo=S`, divide every segment start and end time by `S`, then set the timeline duration from the processed audio probe. Do not reuse the raw timeline.

## Final audio checks

- Listen to the hook, the densest number sentence, and the final line.
- Check for breathing between segments and harsh “s”, “sh”, “x”, and “q” sounds.
- Probe peak level and confirm no clipping.
- Verify the video mux did not resample unnecessarily.
- Keep music absent or at least 15-20 dB below narration unless it materially improves the story.
