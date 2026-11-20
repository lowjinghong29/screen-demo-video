"""Record the desktop at native resolution with ffmpeg's ddagrab, or grab one frame.

    python record.py start rec/take.mp4 [--max 1800] [--screen 0] [--fps 30]
    python record.py stop
    python record.py frame shot.png [--screen 0]

The capture is a fragmented MP4 with a keyframe every second, so the file still plays after the
recorder is killed and at most the last second is lost. Wait two seconds after the last action
before stopping.
"""
import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

STATE = Path(tempfile.gettempdir()) / "screen-demo-video-record.json"


def grab(screen, fps):
    return ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-f", "lavfi",
            "-i", f"ddagrab=output_idx={screen}:framerate={fps}:draw_mouse=1"]


def running(pid):
    out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
                         capture_output=True, text=True).stdout
    return out.lower().startswith('"ffmpeg')   # never kill a reused PID that is not our recorder


def start(a):
    if STATE.exists() and running(json.loads(STATE.read_text())["pid"]):
        sys.exit("a recording is already running: python record.py stop")
    out = Path(a.path).resolve()
    if out.exists():
        sys.exit(f"refusing to overwrite an existing take: {out}")
    out.parent.mkdir(parents=True, exist_ok=True)
    log = open(out.with_suffix(".log"), "wb")
    p = subprocess.Popen(
        grab(a.screen, a.fps) + [
            "-t", str(a.max), "-vf", "hwdownload,format=bgra,crop=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-g", str(a.fps),
            "-pix_fmt", "yuv420p", "-movflags", "+frag_keyframe+empty_moov+default_base_moof", str(out)],
        stdin=subprocess.DEVNULL, stdout=log, stderr=log,
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
    time.sleep(2)
    if p.poll() is not None:
        sys.exit("recorder failed to start:\n" + out.with_suffix(".log").read_text(errors="replace")[-1500:])
    STATE.write_text(json.dumps({"pid": p.pid, "out": str(out)}))
    print(f"recording -> {out}  (stops by itself after {a.max}s; set --max well beyond the take)")


def stop(_):
    if not STATE.exists():
        sys.exit("no recording is running")
    st = json.loads(STATE.read_text())
    if running(st["pid"]):
        subprocess.run(["taskkill", "/PID", str(st["pid"]), "/T", "/F"], capture_output=True)
        time.sleep(1)
    else:
        print("recorder had already stopped (hit --max?)")
    STATE.unlink()
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
                        "-of", "default=nw=1", st["out"]], capture_output=True, text=True)
    print(f"saved {st['out']}\n{d.stdout.strip() or d.stderr.strip()}")


def frame(a):
    out = Path(a.path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    # rgb24 drops the alpha channel: with it, the pointer's bounding box shows as a white square
    r = subprocess.run(grab(a.screen, 1) + ["-frames:v", "1", "-update", "1",
                                            "-vf", "hwdownload,format=bgra,format=rgb24", "-y", str(out)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(r.stderr[-1500:])
    print(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("start"); s.add_argument("path"); s.add_argument("--max", type=int, default=1800)
    s.add_argument("--screen", type=int, default=0); s.add_argument("--fps", type=int, default=30)
    s.set_defaults(fn=start)
    sub.add_parser("stop").set_defaults(fn=stop)
    f = sub.add_parser("frame"); f.add_argument("path"); f.add_argument("--screen", type=int, default=0)
    f.set_defaults(fn=frame)
    args = ap.parse_args()
    args.fn(args)
