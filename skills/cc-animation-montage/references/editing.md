# Narrative and Music Editing

Use this reference after the source license set is known and before writing the manifest.

## Coherence First

- Build one event, not a catalog of attractive shots.
- Assign each project a stable story function. For example, one project supplies awakening and the hero, another supplies the threat, and a third supplies pursuit and aftermath.
- Prefer two or three compatible sources over many unrelated ones.
- Reject footage whose genre, finish level, character behavior, or visual language changes the premise. An idol stage, comedy insert, dialogue scene, or rough animatic usually breaks a battle narrative.
- Keep a deliberate color arc. A useful action progression is cool awakening, warm threat, saturated pursuit, hot impact, then cool aftermath.

## Music Selection

- Audition music before committing to the edit. Genre compatibility is more important than nominal intensity.
- Prefer licensed music from the same animation release when it fits. The original edit provides useful evidence about the intended visual rhythm, and short passages can retain exact source audio/video synchronization.
- If using source audio, attribute it separately in `CREDITS.txt` even when the video entry names the same release.
- Choose a section with a readable beginning, escalation, peak, and exit. Do not select only the loudest 30 seconds.
- Treat tempo estimates as hints. Layered arrangements can produce plausible half-time, full-time, and double-time BPM values.
- Use `scripts/analyze_music.py` to locate energy changes and salient onsets. Group events into phrases; do not cut at every printed timestamp.

## Phrase Storyboard

Write the story before exact source timecodes. A compact structure is:

| Phrase | Story role | Visual requirement |
| --- | --- | --- |
| Entry | Awakening | face, hand, rune, transformation, or first light |
| Build | Threat | portal, silhouette, arrival, or target reveal |
| Lift | Launch | weapon draw, gaze, leap, or forward motion |
| Drive | Clash | attack and reaction with consistent screen direction |
| Peak | Impact | beam, collision, explosion, or white flash |
| Exit | Aftermath | energy decay, empty space, falling motion, or cool color reset |

Each shot must answer at least one question: what caused this, what is the target, who reacts, or what changed?

## Match Cuts

- Shape: rune -> lens -> portal -> targeting reticle.
- Direction: left-to-right flight -> projectile -> target moving the same way.
- Gaze: character looks screen-right -> reveal the threat on screen-right.
- Action: weapon raise -> firing frame -> impact frame.
- Color: purple charge -> magenta portal -> orange collision -> blue decay.
- Light: end one style on a white flash and enter the next style from white or a bright core.

Use a flash to bridge styles only when it is motivated by an impact or transformation. A flash cannot repair unrelated story content.

## Frame-Aligned Timing

1. Choose the audio excerpt start.
2. Convert a desired cut to a timeline frame with `round((cut_time - audio_start) * fps)`.
3. Derive each manifest duration from adjacent frame boundaries: `(next_frame - current_frame) / fps`.
4. Sum the rounded title, action, and credit frames. Require the total to equal `duration * fps` before rendering.
5. Preserve a source video's exact audio sync by starting its visual clip at `audio_start + timeline_offset` and keeping `speed` at `1.0`.

Use longer shots for setup and reveal. Accelerate only after the viewer understands the spatial relationship. Break a regular cutting pattern on the largest impact.

## Visual Review

- Inspect a 1-second contact sheet for story and color progression.
- Inspect a 0.5-second contact sheet for rapid-cut repetition, blank frames, and direction changes.
- Inspect exact cut-adjacent frames when a transition looks unclear.
- Rewatch without audio: the cause-and-effect sequence should still be understandable.
- Rewatch while ignoring subject matter: the musical phrases and impact accents should still be apparent.
