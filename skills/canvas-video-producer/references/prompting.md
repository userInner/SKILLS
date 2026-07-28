# Seedance-style prompting

## Contents

1. Compact prompt formula
2. Reference roles
3. Camera language
4. Action prompts
5. Failure patterns

## Compact prompt formula

Prefer roughly 300–500 useful characters for an ordinary short clip:

`subject lock + starting state + primary action + camera + endpoint + style + avoid`

Add timed sections only when the video is a single continuous event. A longer
prompt is not automatically more controllable.

## Reference roles

Assign references explicitly and in upload order:

- `Image 1: character identity and costume`
- `Image 2: environment and palette`
- `Image 3: exact first frame`
- `Video 1: camera and movement only`
- `Audio 1: rhythm and impact timing`

When the upstream supports `@Image1` syntax, use the exact aliases exposed by
that provider. Otherwise describe roles by ordinal position.

## Camera language

Use one dominant move and at most one secondary move:

- tracking push-in;
- low-angle lateral follow;
- orbit plus slow push;
- rapid dolly toward impact;
- static wide with environmental motion.

Avoid stacking zoom, orbit, crane, handheld shake, roll, and whip-pan in one
short shot. Add shake and flashes in editing when exact timing matters.

## Action prompt example

```text
Image 1 defines the same adult flame warrior and costume; Image 2 defines the
storm bridge. Start in a low stance. He draws the burning ring blade, then
launches left-to-right as the dragon fires one cyan bolt. Low-angle tracking
camera, cloth and embers react naturally. End one frame before collision with
both attacks converging at center. Premium theatrical animation. No redesign,
duplicates, text, logo, or slideshow motion.
```

## Failure patterns

- Six keyframes plus six timed actions in one request: produces interpolation.
- Repeating “cinematic, epic, 8K”: adds little control.
- Conflicting camera commands: causes spatial drift.
- Multiple identity references without roles: causes face/costume blending.
- Exact beat instructions without audio input: usually ignored.
- Asking the model to cut like an editor: produces soft morphs instead of cuts.
