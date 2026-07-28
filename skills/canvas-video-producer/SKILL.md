---
name: canvas-video-producer
description: Plan, generate, poll, download, evaluate, and recut coherent AI video clips through a Canvas-compatible asynchronous video API. Use for text-to-video, image-to-video, Seedance-style multimodal references, first/last-frame animation, model and cost selection, one-shot paid submissions, task_id polling, generated-video quality review, music synchronization, or multi-clip anime/action production.
---

# Canvas Video Producer

Create short AI-video shots as part of an edited production, not as a single
overloaded generation. Treat story, reference roles, paid API calls, polling,
download, and final editing as separate gates.

## Core rule

Generate one readable action per clip. For a sequence such as
`draw -> charge -> clash -> break -> aftermath`, plan three to five short clips
and edit them together. Do not ask one 15-second request to invent the entire
sequence unless continuity matters more than pacing.

## Workflow

1. Read [references/production.md](references/production.md). Write the causal
   beat sequence and assign one subject, action, camera move, and endpoint to
   each shot.
2. Read [references/prompting.md](references/prompting.md). Keep ordinary clip
   prompts compact. Explicitly assign every reference a role.
3. Inspect available models before choosing one:

   ```bash
   python3 scripts/canvas_video.py models --type video
   ```

4. Prepare references and run a non-billable preflight:

   ```bash
   python3 scripts/canvas_video.py preflight \
     --model MODEL_DB_ID \
     --prompt-file shot-01.txt \
     --seconds 5 --aspect-ratio 16:9 \
     --reference-image hero.png \
     --reference-image environment.png
   ```

5. Show the user the exact model, estimated/known price, duration, prompt, and
   uploaded filenames before a paid request. Require explicit confirmation when
   the model or charge changed.
6. Submit exactly once and save the receipt immediately:

   ```bash
   CANVAS_API_KEY=... python3 scripts/canvas_video.py submit \
     --confirm-submit \
     --receipt work/shot-01-receipt.json \
     --model MODEL_DB_ID \
     --prompt-file shot-01.txt \
     --seconds 5 --aspect-ratio 16:9 \
     --reference-image hero.png
   ```

7. If a `task_id` exists, never resubmit because polling timed out. Poll the
   same task and download on success:

   ```bash
   CANVAS_API_KEY=... python3 scripts/canvas_video.py wait \
     --receipt work/shot-01-receipt.json \
     --output output/shot-01.mp4
   ```

8. Read [references/quality.md](references/quality.md). Inspect a contact sheet
   and watch the result before accepting it.
9. For music-led action, use `$cc-animation-montage` after generation to analyze
   onsets, align impacts, add sound design, normalize delivery, and verify the
   final MP4.

## Safety and billing

- Read the API key only from `CANVAS_API_KEY`; never put it in prompts, source
  files, receipts, shell history, or final responses.
- Use the database model ID, not a display name.
- A successful response containing `task_id` is the commit point. Record it
  before polling.
- Treat `queued`, `pending`, `processing`, and `running` as nonterminal.
- Treat transient HTTP errors, timeouts, and database-overload messages as
  polling failures, not generation failures.
- Treat only an explicit terminal `failed` status as failed. Report any refund
  object exactly.
- Download successful CDN results immediately; links may expire.
- Do not switch models, shorten duration, or spend a second charge without new
  user approval.

## Resource routing

- Read [references/production.md](references/production.md) before planning
  multi-shot, action, anime, MV, or long-form work.
- Read [references/prompting.md](references/prompting.md) before writing or
  revising a generation prompt.
- Read [references/canvas-api.md](references/canvas-api.md) when adding API
  fields, interpreting responses, or troubleshooting models and billing.
- Read [references/quality.md](references/quality.md) before accepting,
  regenerating, or salvaging an output.
- Use `scripts/canvas_video.py` for models, preflight, submission, polling, and
  download. Do not rewrite ad-hoc curl loops for paid jobs.

## Completion gate

Finish only when:

- every paid submission has a saved receipt and unique task ID;
- every terminal result is downloaded locally;
- the file decodes completely and its duration/resolution are reported;
- subject identity, action continuity, camera intent, and endpoint are reviewed;
- weak outputs are either rejected or deliberately recut;
- the final music edit places major impacts on salient musical events.
