# Licensing Checklist

This is a conservative production checklist, not legal advice.

## Source Policy

- Prefer public domain, CC0, CC BY, and a single compatible CC BY-SA version.
- Reject CC BY-ND material because editing, synchronization, cropping, and color work create adaptations.
- Use CC BY-NC material only when the user explicitly accepts noncommercial-only distribution and every combined license is compatible.
- Do not infer permission from public availability, an official trailer label, or a download button.
- Verify the exact work and exact release, not only the project homepage.
- Record the license URL and access date. Save a page capture or quoted license text when practical.

## Compatibility Gate

1. List every video, image, font, sound effect, and music source.
2. Inspect the downloaded file metadata with `scripts/audit_media.py`.
3. Compare embedded metadata with the official source page.
4. Treat a disagreement as a blocker and use the stricter license until resolved.
5. Avoid mixing ShareAlike works with different or uncertain adapter-license requirements.
6. Prefer replacing a questionable music track; audio metadata often reveals NC terms omitted from a project soundtrack page.
7. Determine the final license only after the source set is fixed.

## Attribution Fields

For every source, include:

- Work title
- Creator/producer
- Exact release used
- Official project page
- Exact asset URL when available
- License name, version, and URL
- Modifications, such as trimming, speed changes, scaling, color adjustment, and synchronization

## CREDITS.txt Template

```text
TITLE
Export details

VIDEO SOURCES

1. Work title
   Creator: ...
   License: Creative Commons ...
   Official page: https://...
   Release used: https://...
   Changes: trimmed, resized, color adjusted, synchronized

AUDIO

Track or mix title
Creator: ...
License: ...
Official page: https://...
Release used: https://...

REMIX LICENSE

This remix is distributed under ... . No endorsement by the original
creators is implied.
```
