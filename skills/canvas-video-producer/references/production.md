# Multi-clip production

## Contents

1. Production strategy
2. Shot design
3. Reference preparation
4. Music-led action
5. Long-form assembly

## Production strategy

Use generation for motion and performance; use editing for pace and structure.
A model is better at one continuous action than at obeying six unrelated cuts.

For a 15-second action sequence, prefer:

| Clip | Duration | Narrative job |
| --- | ---: | --- |
| A | 3–5s | threat, draw, or launch |
| B | 3–5s | pursuit or convergence |
| C | 3–5s | collision, reaction, or aftermath |

Generate clips independently when the edit needs hard cuts. Use first/last
frames or video extension only when a seamless continuous shot is the goal.

## Shot design

For every clip, write:

- subject lock: face, costume, silhouette, weapon;
- scene lock: location, light direction, palette;
- starting state;
- one primary action;
- one reaction or environmental consequence;
- camera move with at most two axes;
- ending state that motivates the next shot.

Avoid asking for simultaneous transformation, combat choreography, location
change, dialogue, and multiple camera transitions in one short clip.

Maintain screen direction. If the hero launches left-to-right, keep the target
on the right until the collision or deliberately show a motivated reversal.

## Reference preparation

- Use a clean character reference for identity.
- Use a separate environment reference when the scene matters.
- Use first/last frames for a single transition, not as substitutes for a
  multi-shot storyboard.
- Use a reference video for movement or camera choreography.
- Use reference audio only when the selected model explicitly supports it.
- Resize oversized images and transcode large reference videos before upload.

Give each reference exactly one primary job. Too many near-duplicate keyframes
encourage interpolation and slideshow-like motion.

## Music-led action

Choose music before generating final action shots.

1. Identify phrase entry, lift, drop, peak, and exit.
2. Assign actions to hierarchy:
   - small onset: eye, hand, spark, cloth snap;
   - strong beat: draw, launch, cut, reaction;
   - drop/peak: collision, armor break, explosion;
   - release: landing, debris, energy decay.
3. Generate shots with enough handles before and after the intended impact.
4. Place exact cut and impact frames in the editor after generation.

Do not expect a prompt-only model without audio reference to land exact beats.

## Long-form assembly

For work longer than 15 seconds:

1. lock character and scene references;
2. generate one clip per narrative beat;
3. create a shot manifest with intended in/out frames;
4. reject identity or direction breaks before assembly;
5. edit, grade, sound-design, and verify with `$cc-animation-montage`.
