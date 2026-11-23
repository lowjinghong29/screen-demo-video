# Craft: story, narration, sound

What makes a screen demo read as made by a person who knows the product.

## Shape of the video

Aim for 45 to 90 seconds and 6 to 10 shots.

1. **Hook.** One sentence on the starting screen: what this is and who it is for.
2. **Input.** What the user gives it: the file, the form, the question.
3. **Action.** The moment the product does its work. Skip the waiting with a new shot or `speed: 2`.
4. **Proof.** The result where it actually lands: the saved record, the shared page, the sent
   report, the passing build. Plan this shot first. It is the one that got cut off twice on the
   real run.
5. **Close.** One line on what that means for the viewer.

One idea per shot. Show the real thing happening, never a description of it.

The same five beats fit any product. Only what counts as input, action and proof changes:

| Kind of app | Input | Action | Proof |
|---|---|---|---|
| Productivity or team tool | a new task, note or message | it is organised, assigned or shared | a teammate's view shows it |
| Dashboard or analytics | a question or a filter | the chart or table answers | the number that matters, in view |
| E-commerce or booking | a product or a date | add to cart, check out on test data | the confirmation page |
| Document or data processing | an uploaded file | the app reads or converts it | the result, opened or exported |
| Developer tool or CLI | a command or a config | it builds, tests or deploys | the green result or the running app |
| Design or media tool | a blank canvas or an asset | a few strokes or one effect | the finished piece |
| AI assistant or chatbot | a plain question | the answer arrives | the answer put to use |
| Onboarding or tutorial | the empty first screen | the first setup steps | the app ready to use |

## Narration

- **Measure, never count.** Speech length is taken from the real audio by `cut.py`. Word counts
  lie: a figure such as "14,199.76" is spoken three to four times longer than it looks, and a
  script timed by word count overlapped on 35 of 57 lines. Keep long numbers and codes out of
  short shots. Say "about fourteen thousand" and let the caption or the screen carry the digits.
- **Anchor every line to its event.** The line plays while its click or page change is on screen.
  Narration written for a block of scenes, laid over a moving take, reads as out of sync.
- **Fewer, longer shots** beat many short ones.
- Speak to "you", in the present tense, one or two short sentences. If a line needs "and" to join
  two ideas, it is two shots.
- Write for the ear. Spell a product name the way it is said, and avoid abbreviations a voice
  will stumble on. If a word sounds wrong, change the spelling in `say`, not the caption.
- Each shot lasts its line plus 0.85 s, and the line starts 0.35 s after the shot appears. A
  shorter shot than 4 s needs `"min"`.

## Captions

Captions carry the story for people watching without sound.

- A statement, not a label: "Everyone sees the same plan", not "Board screen".
- Six words or fewer.
- If a caption covers the number it talks about, move it with `"caption_y"` in `shots.json`
  (distance from the bottom edge, default 140).

## Zoom (recordings made with record.py)

- Give a `target` pixel read from `review.py grid`. Never guess a fraction.
- Stay at or below recording width divided by output width. On a 2880 px recording cut to 1920,
  that is 1.5. Above it the picture is upscaled and goes soft.
- 1.15 to 1.3 suits most shots. Leave zoom out for an overview.
- A shot holds still for 1.5 s, then eases in over 1.6 s (`"hold"` and `"ramp"` in `shots.json`).

Cursorful exports already contain their zooms. Do not zoom them again.

## Voice

The voice is Kokoro-82M: open source (Apache 2.0) and fully local once its model is downloaded.
The narration text never leaves the computer.

| `voice` | Notes |
|---|---|
| `af_heart` | default; female; the highest grade in the model's own voice list (A) |
| `af_bella` | female (A-) |
| `af_nicole` | female (B-) |
| `am_michael`, `am_fenrir`, `am_puck` | the highest-graded male voices (C+) |

Grades are the model authors' own, from its `VOICES.md`. Avoid `am_adam` (graded F+). The first letter is the language: `a` American English, `b` British
English. This skill installs English only. `"rate"` between 0.9 and 1.1 changes the pace.

## Music

- `"music": "pad"` (default) generates a soft four-chord pad on the spot, so it carries no licence.
- `"music": "track.mp3"` uses your own file, looped under the whole video. Use only a track the
  user has the right to use for this purpose, and write its title, author, source and licence in a
  `CREDITS.txt` beside the video.
- `"music": "none"` leaves the voice alone.
- `"music_under"` is how many dB the music sits below the voice. 26 is the default. Go to 30 if
  the music fights the voice, 22 if it disappears.

## Sound that passes review

Nobody listens while the video is cut, so the levels are set by measurement and checked the same
way: voice peaking at -3 dB, average level between about -21 and -24 dB, and no silent gap longer
than 2.5 s. `review.py final` fails the cut when these are off.

## Privacy in frame

Prefer filming a filtered view. When something private is still visible, cover it with `hide`.
The box is solid on purpose: blurred text can sometimes be read back.
