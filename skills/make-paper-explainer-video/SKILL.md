---
name: make-paper-explainer-video
description: Research, fact-check, script, voice, visualize, render, and verify a sourced vertical video that explains a scientific paper. Use when Codex must turn a paper, preprint, DOI, arXiv link, PDF, or research topic into a Douyin/TikTok/Reels-style video; autonomously select a paper for a research-video series; replace generic stock footage with original paper pages, charts, methods, and annotations; or revise an existing paper explainer's claims, pacing, narration, or visuals.
---

# Make Paper Explainer Video

Produce a credible 9:16 research explainer whose substance and visuals come from the paper itself. Own the workflow from topic selection through the verified MP4 unless the user limits scope.

## Output contract

Deliver:

- a sourced script with one clear takeaway;
- a claim ledger linking every quantitative or causal statement to the paper;
- paper-page and chart visuals rather than decorative stock footage;
- synchronized narration, captions, and 1080x1920 video;
- an explicit limitation when the result is preliminary, narrow, correlational, or contested;
- a final MP4 plus a cover frame and source note.

Never present a preprint as peer-reviewed. Never translate EEG activity, correlation, model score, or self-report into IQ loss, brain damage, causation, or clinical diagnosis unless the study directly measured and supports that claim.

## Workflow

### 1. Select a paper with video potential

If the user did not choose a paper, search current primary sources and select one that has:

- a question understandable without specialist training;
- a counterintuitive or disputed public interpretation;
- at least one concrete experimental comparison or number;
- figures, tables, apparatus, or diagrams that can carry the visuals;
- limitations that materially change the conclusion.

Prefer the publisher, DOI landing page, arXiv, PubMed, an institutional publication page, or the authors' repository. Use secondary coverage only to identify public misconceptions or controversy.

Read [references/research-and-claims.md](references/research-and-claims.md) before researching or writing claims.

### 2. Acquire and inspect the complete paper

Download the PDF. Extract text for search, then render relevant pages for visual inspection. Do not rely on an abstract or news article when the full paper is available.

Use `scripts/prepare_paper.sh` when Poppler is available:

```bash
scripts/prepare_paper.sh paper.pdf work/paper "1,4,8,12"
```

Locate and inspect:

- title, authors, year, venue, and publication status;
- sample size, recruitment, assignment, conditions, and task;
- primary outcome and its unit;
- the strongest numeric comparison and its denominator;
- statistical uncertainty or significance;
- limitations and future-work sections;
- figures that directly support the narrative.

Render selected pages at 180-240 DPI. Visually verify labels, legends, axes, and captions before using them.

### 3. Build a claim ledger before the script

Record each intended statement as:

```text
claim | exact evidence | page/figure | safe wording | prohibited overclaim
```

Separate four levels:

1. The paper directly measured this.
2. The authors interpret the result this way.
3. A practical implication is plausible but not tested.
4. The study cannot answer this.

The video's most memorable line must not be stronger than the evidence.

### 4. Write for retention without becoming clickbait

Use this sequence unless the paper demands another structure:

1. **Misconception hook** - state the viral interpretation, then correct it.
2. **Study design** - who, what task, which groups, what instrument.
3. **One decisive result** - numerator and denominator, not a floating percentage.
4. **Meaning** - explain the measured construct in plain language.
5. **Boundary** - say what it does not prove.
6. **Secondary result** - add one result that deepens the story.
7. **Limitations** - show two or three concrete weaknesses.
8. **Actionable conclusion** - give behavior consistent with the evidence.

Target 45-75 seconds. Prefer eight compact narration segments. Put important numbers in separate sentences so the voice reads them clearly.

Read [references/story-and-visuals.md](references/story-and-visuals.md) before storyboarding or selecting a voice.

### 5. Storyboard from the PDF

Use the paper as the visual world:

- page 1 for the hook and publication-status stamp;
- method page for participants, apparatus, and conditions;
- original chart for the main result;
- original diagram or heatmap for mechanism or secondary evidence;
- limitations page for caveats;
- a clean two-step summary for the final action.

Crop and zoom into the relevant evidence. Add restrained red boxes, arrows, handwritten notes, ratios, and short Chinese labels. Keep the original figure visible long enough for the viewer to understand that the evidence is real.

Avoid generic office, phone, or laboratory stock unless the paper has no usable visual evidence and the user explicitly wants B-roll. Never invent a fake journal interface, fake chart, fake participant, or fake quote.

### 6. Generate or record narration

Prefer a human recording when supplied. Otherwise use the user's local voice system.

For CosyVoice:

- inspect available reference clips instead of assuming the default sounds good;
- estimate median fundamental frequency when choosing between markedly different timbres;
- synthesize segments separately, with natural pauses;
- direct the voice as a person explaining a paper to a friend, not a newsreader;
- avoid emphasizing every conclusion;
- use `atempo` for small global pace corrections without changing pitch;
- rebuild the visual timeline after any speed change.

Use `scripts/build_timeline.py` to assemble segment WAV files and create a timeline:

```bash
python3 scripts/build_timeline.py work/voice --output work/voice.wav \
  --timeline work/timeline.json --pause 0.12
```

### 7. Render the vertical video

Copy `assets/paper-video-template/video.html` into the project and adapt its scenes. Keep paths relative to the project so the template is portable.

Render deterministic frames with:

```bash
node scripts/render_frames.mjs \
  --work work/video \
  --html video.html \
  --timeline timeline.json \
  --fps 15
```

Assemble at 30 fps:

```bash
scripts/assemble_video.sh work/video/frames work/voice.wav output.mp4 15
```

Use hard cuts or short evidence-driven transitions. Do not add glowing gradients, synthetic AI orbs, fake dashboards, or constant motion. A page, a crop, and one decisive annotation are often enough.

### 8. Verify before delivery

Run:

```bash
scripts/validate_video.sh output.mp4
```

Also create a contact sheet containing the hook, method, main result, caveat, and final action. Inspect it visually.

Check:

- first frame is understandable without audio;
- captions do not cover chart labels or platform controls;
- every number matches its denominator and session;
- paper status and limitations are visible and spoken;
- narration is not clipped, metallic, overcompressed, or buried by music;
- final video is H.264/AAC, 1080x1920, 30 fps, and has fast-start metadata;
- source URLs are preserved in a project source note.

If the content still feels empty, do not add adjectives or stock footage. Return to the methods, denominators, measurement definition, comparison group, and limitations.
