"""Check that this computer can make a screen demo video, and print the exact fix for anything missing.

    python setup_check.py             everything except the desktop driver
    python setup_check.py --desktop   also start the desktop driver once (first run downloads it)

Nothing is installed by this script. Ask the user before running any fix it prints.
"""
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path.home() / ".screen-demo-video"
VOICE = HOME / "voice" / "Scripts" / "python.exe"
CURSORFUL_ID = "eihpmapodnppeemkhkbhikmggfojdkjd"
CURSORFUL_URL = f"https://chromewebstore.google.com/detail/cursorful/{CURSORFUL_ID}"
BROWSERS = {"Chrome": "Google/Chrome", "Edge": "Microsoft/Edge", "Brave": "BraveSoftware/Brave-Browser"}

ok_all = True


def line(ok, what, fix=""):
    global ok_all
    ok_all &= ok
    print(f"[{'ok' if ok else 'FIX'}] {what}" + (f"\n      -> {fix}" if fix and not ok else ""))


def note(what):
    print(f"[--] {what}")


def out_of(cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=120).stdout
    except (OSError, subprocess.TimeoutExpired):
        return ""


def voice_python():
    cfg = HOME / "config.json"
    if cfg.exists():
        own = json.loads(cfg.read_text(encoding="utf-8")).get("voice_python")
        if own and Path(own).exists():
            return Path(own)
    return VOICE


def main():
    win = platform.system() == "Windows"
    line(win, f"Windows ({platform.release()})", "this skill records with Windows APIs; it does not run on macOS or Linux")
    line(sys.version_info >= (3, 10), f"Python {platform.python_version()}", "winget install Python.Python.3.12")

    filters = out_of(["ffmpeg", "-hide_banner", "-filters"]) if shutil.which("ffmpeg") else ""
    missing = [f for f in ("ddagrab", "zoompan", "drawtext", "drawbox", "volumedetect") if f" {f} " not in filters]
    line(bool(filters) and not missing and bool(shutil.which("ffprobe")),
         "ffmpeg and ffprobe with the filters this skill uses" + (f" (missing: {missing})" if filters and missing else ""),
         "winget install Gyan.FFmpeg   (then open a new terminal)")
    line(bool(shutil.which("uv")), "uv (installs the voice and the desktop driver in their own sandboxes)",
         "winget install astral-sh.uv   (then open a new terminal)")
    line(Path("C:/Windows/Fonts/segoeuib.ttf").exists(), "caption font (Segoe UI Bold)",
         'set "font" in shots.json to another .ttf')

    vp = voice_python()
    has_voice = vp.exists() and subprocess.run([str(vp), "-c", "import kokoro, soundfile"],
                                               capture_output=True).returncode == 0
    line(has_voice, f"voice environment (Kokoro) at {vp}",
         f'uv venv --python 3.11 "{HOME / "voice"}"  &&  '
         f'uv pip install --python "{VOICE}" --require-hashes -r "{HERE.parent / "requirements-voice.txt"}"'
         "   (about 1 GB; the first video also downloads the 330 MB voice model)")

    local = Path(os.environ.get("LOCALAPPDATA", ""))
    found = [f"{name} / {p.parent.parent.name}" for name, sub in BROWSERS.items()
             for p in (local / sub / "User Data").glob(f"*/Extensions/{CURSORFUL_ID}")]
    if found:
        note(f"Cursorful extension installed in: {', '.join(found)}")
    else:
        note("Cursorful extension not found. For a web app, ask the user to install it themselves from the\n"
             f"      official listing only: {CURSORFUL_URL}\n"
             "      (free plan = non-commercial use; work videos need Cursorful Pro, or use record.py instead)")

    if "--desktop" in sys.argv:
        r = subprocess.run([sys.executable, str(HERE / "desktop.py"), "schema"], capture_output=True, text=True)
        line(r.returncode == 0 and "Click" in r.stdout, "desktop driver starts and lists its tools",
             (r.stderr or r.stdout).strip()[-400:] or "run again; the first start can time out while it builds")
    else:
        note("desktop driver not started (add --desktop to test it; the first run downloads Windows-MCP)")

    print("\nREADY" if ok_all else "\nNOT READY: fix the lines marked FIX, then run this again")
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
