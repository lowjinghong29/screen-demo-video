# Security

This skill lets an AI agent see the screen, move the mouse and type. That deserves plain words
about what it can do, what is checked, and what is not.

## What it can do on the computer

| Part | Can | Cannot |
|---|---|---|
| `desktop.py` | read the UI tree, click, type, scroll, press shortcuts, switch and resize windows | run PowerShell or any program path, read or write files, read the clipboard, edit the registry, kill processes, write a screenshot to a path |
| `record.py` | record the desktop to a file you name, grab one frame, stop its own ffmpeg | overwrite an existing take, stop a process that is not its own ffmpeg |
| `cut.py` | read the recordings and the shot list, write inside the project folder | delete anything outside the project folder (its work folder is checked before it is cleared) |

The refusals in `desktop.py` are enforced in the client, before the driver starts, and are
covered by `scripts/selfcheck.py`. The driver also runs with user control on and the strict
policy: the user's mouse or keyboard takes the desktop back, a consent dialog appears before a
control period, and `Ctrl+Alt+Shift+Backspace` always works.

The agent running this skill still has its own tools, such as a shell. This skill does not widen
them, and it does not narrow them either.

## What leaves the computer

Nothing while filming, cutting or reviewing. Recordings, narration text and videos stay local.

Downloads happen only during setup, and only after the user agrees:

| What | From | Checked how |
|---|---|---|
| Voice dependencies (94 packages) | PyPI, and one spaCy model from GitHub releases | exact versions and SHA-256 hashes in `requirements-voice.txt`, installed with `--require-hashes` |
| Kokoro voice model, about 330 MB, on the first video | Hugging Face, `hexgrad/Kokoro-82M` | fetched by the `kokoro` library; not hash-pinned by this repository |
| Windows-MCP desktop driver | GitHub, pinned to one full commit hash in `desktop.py` | the commit is fixed; its own dependencies are resolved at install time and are not hash-pinned |
| ffmpeg, uv | winget | winget's own package verification |

Telemetry is switched off for Windows-MCP and for the Hugging Face client.

Cursorful is installed by the user from the Chrome Web Store. It renders locally. Its share-link
and cloud features upload video, and this skill tells the agent never to use them without the
user's say.

## What to keep in mind

- **A screen recording shows whatever was on screen.** Other tabs, notifications, people's names,
  messages and figures can all end up in a take. The skill filters, frames and covers them, and reviews every
  shot, but watch the video yourself before sharing it.
- **Use test data.** The skill forbids real payments, posts, sends and deletes unless asked for
  by name, and tells the agent to undo test records. A sandbox account makes that rule easy to keep.
- **Text on screen can be hostile.** The skill tells the agent to treat it as data and never as
  instructions.
- **Covering data** uses solid boxes, because blurred text can sometimes be recovered.
- **Media never belongs in git.** `.gitignore` excludes video, audio and image files and the
  project work folders.

## Changing the pins

Raise the Windows-MCP commit in `scripts/desktop.py` only after reading the upstream diff. Rebuild
`requirements-voice.txt` only from an environment you installed and tested yourself, with
`uv pip compile --generate-hashes`.

## Reporting a problem

Open an issue in this repository, or contact the repository owner directly. Do not include
recordings or screenshots that show private data.
