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

Keep `instruct_text` short and primarily positive. Long lists of negative constraints can leak into generated speech, especially in later segments. A stable CosyVoice 3 pattern is:

`You are a helpful assistant. 请用自然、偏低沉的中文男声，语速中等偏快，干净克制地表达。<|endofprompt|>`

Do not remove `<|endofprompt|>`; it is the model's required separator. Express detailed quality requirements as validation criteria rather than packing all of them into `instruct_text`.

Qualify the result for:

- clean studio narration;
- no breath, inhale, gasp, panting, or exaggerated air noise;
- direct silence between sentences;
- varied but controlled sentence endings;
- conversational explanation, not news, trailer, recitation, or marketing delivery;
- clear numbers and restrained emphasis.

Short segments reduce unwanted generated breaths and make individual regeneration cheap.

## Instruction-leak check

Run ASR on every generated segment before assembly and compare it with the intended narration. Reject a segment when the transcript contains instruction-only phrases such as breath, background noise, clean pause, do not drag, recitation, marketing tone, or equivalent prompt fragments.

Also reject segments with unexplained extra speech, repeated clauses, or duration far outside the expected range. Archive rejected audio, regenerate only the affected segment with a shorter instruction, and rerun ASR. Do not rely on listening to only the hook: instruction leakage can begin in later segments.

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

- Confirm every segment passed ASR instruction-leak screening.
- Listen to the hook, the densest number sentence, and the final line.
- Check for breathing between segments and harsh “s”, “sh”, “x”, and “q” sounds.
- Probe peak level and confirm no clipping.
- Verify the video mux did not resample unnecessarily.
- Keep music absent or at least 15-20 dB below narration unless it materially improves the story.
