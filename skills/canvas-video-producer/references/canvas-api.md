# Canvas-compatible video API

## Contents

1. Environment
2. Endpoints
3. Inputs
4. Response states
5. Model selection
6. Recovery rules

## Environment

```bash
export CANVAS_API_KEY="..."
export CANVAS_API_BASE="https://api.canvas.12646464.xyz"
```

`CANVAS_API_BASE` is optional. Never store the key in a project file.

## Endpoints

- `GET /v1/models`: list models.
- `POST /v1/videos`: create one paid asynchronous video task.
- `GET /v1/videos/{task_id}`: query an existing task.

Local references use multipart form data. Remote URLs use JSON fields.

## Inputs

Common fields:

- `model`: database model ID;
- `prompt`;
- `aspect_ratio`;
- `seconds`;
- `resolution`.

Multipart reference fields:

- `reference_images` (repeatable);
- `reference_videos` (repeatable);
- `reference_audios` (repeatable);
- `first_frame_image`;
- `last_frame_image`;
- `input_reference` for MIME-based mixed uploads.

Do not set multipart `Content-Type` manually; the client must create its
boundary.

Provider capability limits vary by model. A common Seedance full-reference
profile accepts up to 9 images, 3 videos, 3 audio files, and 12 files total.
Treat model metadata as authoritative.

## Response states

Successful submission includes a model object, charge/balance values, and a
task ID nested under `data` or `data.task`.

Nonterminal states:

- `queued`
- `pending`
- `processing`
- `running`

Success states:

- `succeeded`
- `completed`

Failure:

- `failed`

Success URLs may appear as `video_url`, `result_url`, `url`, `resultVideoUrl`,
or the first item in `urls`.

## Model selection

Compare:

- database ID;
- known price per task or second;
- resolution;
- supported duration;
- image/video/audio reference limits;
- first/last-frame capability;
- native audio;
- queue reliability.

Cheaper prompt-only or image-reference channels are suitable for isolated
shots. Use full multimodal channels when reference video or music timing is
essential.

## Recovery rules

- Invalid key/model/parameter before a task ID: correct once after user review.
- Balance or activation failure: stop; do not silently reduce specifications.
- Timeout or database overload while polling: wait and retry the same task.
- Terminal failure: report error, upstream error, and refund object.
- Successful CDN URL: download immediately and verify locally.
