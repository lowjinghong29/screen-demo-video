# screen-demo-video

A Claude Code skill that makes a narrated product demo video of any app you can open on a Windows
screen. You name the app. Claude plans the story, records the real screen, drives the app with a
real mouse, cuts the video, adds an open-source voice-over and music, and reviews every shot.

It works for any kind of software: web apps and SaaS, websites, dashboards, desktop programs,
developer tools and terminals, internal tools, AI assistants, and mobile apps shown in an emulator
or browser preview.

## Use it

1. Open Claude Code on a Windows computer.
2. Paste this and fill in the blanks:

   > Use https://github.com/lowjinghong29/screen-demo-video to make a demo video of **[app or URL]**
   > showing **[what it should show]**.

3. Answer Claude's few questions, click the two consent buttons, and keep your hands off the
   mouse while it films.

### If you are Claude and were handed this link

```bash
git clone https://github.com/lowjinghong29/screen-demo-video "$HOME/.claude/skills/screen-demo-video"
# already there? update instead:
git -C "$HOME/.claude/skills/screen-demo-video" pull --ff-only
```

Then read `SKILL.md` in that folder from top to bottom and follow it from step 0. Do not skip the
rules at the top.

## Who does what

| You | Claude |
|---|---|
| Sign in to the app yourself | Checks the computer and installs what is missing, after asking |
| Install the Cursorful extension (web apps) | Studies the app and writes the story |
| Turn on Do Not Disturb | Starts and stops the recording |
| Click **Allow now** on the control dialog | Moves the mouse, clicks and types on camera |
| Keep hands off while it films | Cuts, zooms, captions, voice-over, music |
| Watch the result | Reviews every shot and the sound, then reports |

## What you need

- Windows 10 or 11, and Claude Code.
- About 2 GB of free disk space and an internet connection for the first setup.
- Claude installs these on request: ffmpeg, uv, the voice (Kokoro) and the desktop driver.
- You install Cursorful yourself, from its official Chrome Web Store page. Claude gives you the link.

## Costs and licences

| Piece | Licence | Cost |
|---|---|---|
| This repository | MIT | free |
| ffmpeg | LGPL / GPL | free |
| Kokoro-82M voice | Apache 2.0 | free, runs on your computer |
| Windows-MCP desktop driver | MIT | free |
| Built-in music | generated on the spot, no licence | free |
| Cursorful extension | proprietary | free for non-commercial use only. **Work videos need Cursorful Pro, US$79 per seat, one-time** (price seen in November 2026). |

No Cursorful Pro? Claude records with the built-in ffmpeg recorder instead, which is free and open
source. You lose Cursorful's follow-the-cursor zoom and keep sharp, planned zooms.

## Safety in short

- Claude asks before installing anything. The voice install is pinned to exact versions and
  checked by hash, and the desktop driver is pinned to one reviewed commit.
- The desktop driver can only look, click, type, scroll and switch windows. Shell, file, registry
  and clipboard tools are refused in code. Your own mouse or keyboard always takes control back,
  and `Ctrl+Alt+Shift+Backspace` does so at once.
- Claude never types passwords, never touches banking or password apps, and never presses Pay,
  Send, Post or Delete on real data unless you ask for exactly that.
- Recordings stay on your computer. Nothing is uploaded, and `.gitignore` keeps media out of git.
- Watch the video before you share it. A screen recording shows whatever was on screen.

More detail: [SECURITY.md](SECURITY.md).

## When something goes wrong

| Symptom | Fix |
|---|---|
| `setup_check.py` prints `FIX` | Run the command it shows, open a new terminal, check again |
| "desktop server exited before answering" | The first start downloads and builds the driver. Check the network and run it again |
| A hash error while installing the voice | Stop. Do not bypass the check. Open an issue on this repository |
| "the user is using the computer" | Let go of the mouse and keyboard, then ask Claude to continue |
| The video looks soft | Browser zoom was not 100%, or a shot zooms beyond 1.5 on a 2880 px recording |
| `review.py final` fails | Read the failed line, fix the shot list, cut again |

## Layout

```
SKILL.md                    the workflow Claude follows
scripts/setup_check.py      readiness check with exact fixes
scripts/desktop.py          real mouse and keyboard, allow-listed
scripts/drive.py            human-looking cursor motion
scripts/record.py           native-resolution screen recorder
scripts/review.py           beat sheet, pixel grid, final review
scripts/cut.py              the editor: zoom, captions, voice, music
scripts/tts_kokoro.py       the voice
scripts/selfcheck.py        end-to-end proof that never touches the desktop
references/                 craft notes, Cursorful facts, driver reference, example shot list
requirements-voice.txt      exact, hash-checked voice dependencies
```

## Licence

MIT. See [LICENSE](LICENSE). Third-party tools keep their own licences and are not included here.
