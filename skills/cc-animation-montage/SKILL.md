---
name: cc-animation-montage
description: Source, license-audit, edit, credit, and verify short animation mashups with FFmpeg and Pillow. Use for anime-style or animated montage/AMV requests that require finding reusable footage, checking Creative Commons compatibility, creating beat-driven edits, normalizing mixed media, generating title and attribution cards, or exporting a verified MP4 plus credits.
---

# CC Animation Montage

Build a publishable montage from authorized, public-domain, or Creative Commons animation. Treat provenance, license compatibility, edit quality, and output verification as one workflow.

## Defaults

Use these when the user does not specify them:

- Duration: 30 seconds
- Canvas: 1920x1080, 16:9
- Frame rate: 30 fps
- Codec: H.264 video and AAC stereo audio
- Edit: 0.8-second title, 1.5-2.5-second action cuts, 2-second credit card

Do not describe open animation as footage from commercial anime franchises. Use franchise footage only when the user supplies it and confirms authorization.

## Workflow

1. Confirm the target duration, aspect ratio, mood, and platform when they materially change the edit. Otherwise use the defaults.
2. Read [references/licensing.md](references/licensing.md) before sourcing or combining third-party media.
3. Prefer official project pages and exact official release assets. Record title, creator, source page, exact asset URL, license/version, and access date.
4. Audit every downloaded video and audio file, including embedded cover art and metadata:

   ```bash
   python3 scripts/audit_media.py --hash /absolute/path/to/media
   ```

5. If a web page and embedded metadata disagree, use the more restrictive terms until an authoritative source resolves the conflict. Replace incompatible media instead of silently weakening the final license.
6. Create broad and fine contact sheets before selecting clips:

   ```bash
   python3 scripts/contact_sheet.py input.mp4 sheet.jpg --interval 10
   python3 scripts/contact_sheet.py input.mp4 action.jpg --start 120 --duration 60 --interval 2
   ```

7. Select short clips with clear motion, readable silhouettes, and visual contrast. Alternate projects and shot scales. Avoid dialogue-heavy, credit, logo, or empty establishing shots unless intentionally used.
8. Copy [references/manifest-example.json](references/manifest-example.json), replace all placeholder paths and attribution lines, then build:

   ```bash
   python3 scripts/build_montage.py /absolute/path/to/manifest.json
   ```

9. Run the independent verifier and inspect the generated contact sheet plus first/last frames:

   ```bash
   python3 scripts/verify_video.py output.mp4 \
     --duration 30 --fps 30 --width 1920 --height 1080
   ```

10. Deliver the MP4 and `CREDITS.txt`. State the final license and any use restriction plainly.

## Editing Rules

- Re-encode every segment before concatenation. Normalize resolution, frame rate, sample aspect ratio, pixel format, and color metadata.
- Use `yuv420p`, `SAR 1:1`, BT.709 primaries/transfer/matrix, and limited (`tv`) range for ordinary 1080p exports.
- Do not stream-copy clips with differing color metadata. FFmpeg may reconfigure filters at boundaries and reset timestamps, dropping the title or shortening the export.
- Mute source dialogue by default. Use one independently compatible music/effects track unless the user requests source audio.
- Prefer hard cuts for high-energy edits. Use brief fades only for the title, ending, or a deliberate tonal change.
- Keep action cuts near a regular musical subdivision, then break the pattern for major impacts.
- Render exactly `duration * fps` video frames. Generate audio separately at the target duration, then mux the two streams.

## Resource Routing

- Read [references/licensing.md](references/licensing.md) for source selection, compatibility checks, and attribution format.
- Read [references/manifest-example.json](references/manifest-example.json) when creating a new build manifest.
- Use `scripts/audit_media.py` immediately after each download.
- Use `scripts/contact_sheet.py` for visual indexing.
- Use `scripts/build_montage.py` for deterministic construction.
- Use `scripts/verify_video.py` after every final render.

## Completion Gate

Do not call the edit complete until all of these are true:

- The final file decodes without FFmpeg errors.
- Duration, frame count, resolution, and frame rate match the target.
- Video is H.264/yuv420p with BT.709 limited-range metadata.
- Audio is present, not clipped, and ends cleanly.
- Title and credit cards render and fit the frame.
- `CREDITS.txt` names every video and audio source with creator, URL, and license.
- The final license is compatible with all incorporated media.
