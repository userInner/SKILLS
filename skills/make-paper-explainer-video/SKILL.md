---
name: make-paper-explainer-video
description: Research, fact-check, script, voice, visualize, render, verify, and package a sourced vertical video that explains a scientific paper. Use when Codex must turn a paper, preprint, DOI, arXiv link, PDF, research topic, or participant-reported case into a Douyin, Xiaohongshu, WeChat Channels, TikTok, or Reels-style video; autonomously select a paper for a research-video series; replace generic AI or stock visuals with original paper pages, charts, cases, and annotations; improve a paper video's retention, narration, claims, pacing, cover, or platform copy; or prepare a multi-platform publishing package with AI-content disclosure.
---

# Make Paper Explainer Video

Produce a credible 9:16 research explainer whose claims and visual evidence come from the paper. Own the workflow from topic selection through the verified MP4 and publishing package unless the user limits scope.

## Output contract

Deliver:

- a sourced script with one clear takeaway and an evidence-led hook;
- a claim ledger for every number, causal statement, and participant case;
- paper-page, case, method, and chart visuals instead of decorative AI stock;
- synchronized narration, short captions, and a 1080x1920 H.264/AAC video;
- visible and spoken boundaries for preliminary, narrow, correlational, or self-reported evidence;
- a clean 9:16 cover, a 3:4 cover, and a source note;
- when publishing is in scope, platform-specific titles, descriptions, hashtags, first comments, and AI-content disclosure instructions.

Never present a preprint as peer-reviewed. Never translate EEG activity, correlation, model score, or self-report into IQ loss, brain damage, causation, or clinical diagnosis unless the study directly measured and supports that claim. Describe participant-reported examples as reported experiences, not independently verified events.

## Workflow

### 1. Select for evidence and story potential

If the user did not choose a paper, search current primary sources. Prefer a paper with:

- a question understandable without specialist training;
- a concrete person, task, artifact, mistake, or consequence;
- one counterintuitive comparison or strong public misconception;
- figures, tables, apparatus, quotes, or reported cases that can carry the visuals;
- limitations that materially narrow the conclusion.

Prefer the publisher, DOI page, official preprint, PubMed, institution page, or author repository. Use secondary coverage only to discover misconceptions.

Read [references/research-and-claims.md](references/research-and-claims.md) before researching or writing claims.

### 2. Inspect the complete paper

Download the full PDF. Extract searchable text and render relevant pages. Do not rely on an abstract or article when the paper is available.

```bash
scripts/prepare_paper.sh paper.pdf work/paper "1,4,8,12"
```

Locate and verify:

- title, authors, year, venue, license, and publication status;
- sample, recruitment, assignment, task, conditions, and exclusions;
- outcome definitions, denominators, effects, uncertainty, and significance;
- participant-reported examples and whether researchers independently observed them;
- limitations and future-work sections;
- visually useful pages, figures, tables, and exact evidence passages.

Render selected pages at 180-240 DPI and visually inspect labels, legends, axes, and captions.

### 3. Build a claim and case ledger

Record each intended statement as:

```text
claim | evidence | page/figure/participant | evidence type | safe wording | prohibited overclaim
```

Separate:

1. Direct measurement.
2. Participant self-report or reported experience.
3. Author interpretation.
4. Plausible but untested implication.
5. What the study cannot answer.

The most memorable line must not be stronger than the evidence.

### 4. Choose the story engine before writing

Prefer the first available structure:

1. **Case-first** - a specific person, concrete artifact, decision, and consequence. Use when the paper contains a vivid observed or participant-reported example.
2. **Misconception-first** - a popular claim that the paper did not actually test.
3. **Experiment-first** - a visually striking task, apparatus, or comparison.
4. **Result-first** - only when the number is immediately meaningful without setup.

Do not default to “sample size, method, result.” That often produces a video-shaped abstract.

Run an eight-second test: can a viewer describe the person/problem, stakes, or contradiction before the study details appear? If not, rewrite the opening.

Read [references/story-and-visuals.md](references/story-and-visuals.md) before scripting or storyboarding.

### 5. Write for retention and accuracy

Target 50-80 seconds. Use 8-12 compact narration segments.

- Establish a person, problem, or misconception before listing methodology.
- Reveal only the numbers needed to understand the conclusion; usually two or three are enough.
- Keep numerators and denominators together.
- State “reported,” “associated,” or “caused” according to the evidence type.
- Put the main caveat immediately after the main result.
- End with a concrete decision rule, question, or workflow supported by the evidence.

If the script reads like an abstract, do not improve it with adjectives. Rebuild it around a case, decision, error boundary, or consequence from the paper.

### 6. Storyboard from evidence

Use one evidence object per shot:

- exact case paragraph or quote crop for a case-led hook;
- title page and venue/status stamp after the hook has established interest;
- method page only when necessary to interpret the result;
- original table or figure for the main relationship;
- limitations paragraph for the caveat;
- clean cards for the final practical rule.

Crop and zoom until the relevant text is legible. Add restrained boxes, arrows, handwritten notes, ratios, and short Chinese labels. Do not invent fake participants, quotes, journals, charts, or interfaces.

### 7. Generate and qualify narration

Prefer a human recording when supplied. Otherwise use the user's local voice system.

When synthetic narration is used, read [references/audio-quality.md](references/audio-quality.md).

For CosyVoice:

- inspect reference clips and compare median pitch before choosing a timbre;
- generate a 10-second hook test when changing voice or direction;
- synthesize short segments and create pauses with digital silence;
- explicitly request clean studio narration without breath, gasps, or exaggerated sentence endings;
- preserve a raw master at the model's native sample rate;
- use only small `atempo` corrections and rebuild the timeline after any speed change;
- regenerate a bad segment instead of using aggressive noise gates or denoising.

```bash
python3 scripts/build_timeline.py work/voice --output work/voice.wav \
  --timeline work/timeline.json --pause 0.12
```

### 8. Render, cover, and validate

Copy `assets/paper-video-template/video.html` and adapt the scenes.

```bash
node scripts/render_frames.mjs \
  --work work/video --html video.html --timeline timeline.json --fps 15

scripts/assemble_video.sh work/video/frames work/voice.wav output.mp4 15
scripts/validate_video.sh output.mp4
```

Use hard cuts or short evidence-driven transitions. Avoid glowing gradients, AI faces, fake dashboards, decorative particles, and constant motion.

Render a cover state with captions and source footer hidden. Export a clean 9:16 cover and derive a 3:4 cover:

```bash
scripts/make_covers.sh clean-cover-frame.jpg output/cover
```

Create a contact sheet covering the hook, case, main result, caveat, action, and final frame. Inspect it visually.

### 9. Package for publishing when requested

Read [references/publishing-cn.md](references/publishing-cn.md) for Douyin, Xiaohongshu, and WeChat Channels packaging.

Before using platform limits or policy claims, verify current official rules or the live publishing UI. If audio, video, images, or text are AI-generated or synthesized, disclose that fact in the copy and select the platform's current AI-content declaration.

Prepare uploads and form fields without publishing them unless the user authorizes account actions. Treat the final public-submit action as a separate confirmation point.

### 10. Final quality gate

Check:

- the first eight seconds create curiosity without overstating evidence;
- a human situation or clear contradiction appears before dense data when the paper supports one;
- every number, case, and quote maps to the ledger;
- captions avoid chart labels and platform controls;
- publication status and limitations are visible and spoken;
- narration has no breath artifacts, harsh sibilance, clipping, metallic denoising, or needless resampling;
- video is H.264/AAC, 1080x1920, 30 fps, fast-start, and visually sharp;
- covers remain legible at feed size and the 3:4 crop loses no key line;
- platform copy preserves evidence boundaries and includes required AI disclosure.

If the result still feels unwatchable, do not add more animation. Rewrite the first 20 seconds around a concrete case, a consequential error, or a decision the viewer recognizes.
