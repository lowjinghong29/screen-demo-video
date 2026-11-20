"""Look at a recording or a finished cut without opening a player.

    python review.py beats <video> [--from S] [--to S] [--every S] [--out sheet.png]
        scene-change timestamps, plus one contact sheet of frames labelled with their second
    python review.py grid <video> <second> [--out grid.png] [--step 240]
        one frame with a pixel grid in the recording's own coordinates, to pick zoom targets and hide boxes
    python review.py final <shots.json>
        the midpoint of every shot on one sheet, plus audio health; exits 1 when a check fails
"""
import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

FONT = "C\\:/Windows/Fonts/segoeuib.ttf"


def ff(cmd):
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        sys.exit(f"FAILED: {' '.join(str(c) for c in cmd[:6])}\n{p.stderr.decode('utf-8', 'ignore')[-2000:]}")
    return p.stdout.decode("utf-8", "ignore"), p.stderr.decode("utf-8", "ignore")


def probe(path, entries, stream=None):
    cmd = ["ffprobe", "-v", "error"] + (["-select_streams", stream] if stream else [])
    out = ff(cmd + ["-show_entries", entries, "-of", "csv=p=0", str(path)])[0].strip()
    return out.splitlines()[0] if out else ""


def beats(a):
    dur = float(probe(a.video, "format=duration"))
    start, end = a.start, min(a.to or dur, dur)
    span = end - start
    every = a.every or max(1, math.ceil(span / 48))
    n = max(1, min(48, int(span // every) + 1))
    cols = min(8, n)
    out = Path(a.out or Path(a.video).with_suffix(".beats.png"))
    label = (f"drawtext=fontfile='{FONT}':text='%{{eif\\:t+{start}\\:d}}s':x=8:y=8:fontsize=30:"
             "fontcolor=white:box=1:boxcolor=black@0.75:boxborderw=6")
    ff(["ffmpeg", "-y", "-nostats", "-loglevel", "error", "-ss", str(start), "-t", str(span), "-i", str(a.video),
        "-vf", f"fps=1/{every},scale=480:-2,{label},tile={cols}x{math.ceil(n / cols)}",
        "-frames:v", "1", "-update", "1", str(out)])
    _, err = ff(["ffmpeg", "-nostats", "-ss", str(start), "-t", str(span), "-i", str(a.video),
                 "-vf", "select='gt(scene,0.25)',metadata=print:file=-", "-an", "-f", "null", "-"])
    cuts = [round(float(m) + start, 1) for m in re.findall(r"pts_time:([\d.]+)", err)]
    print(f"{a.video}: {dur:.1f}s, sheet every {every}s from {start}s -> {out}")
    print("scene changes (s):", cuts[:80] or "none above the threshold; UI changes are often subtle, read the sheet")


def grid(a):
    w, h = (int(v) for v in probe(a.video, "stream=width,height", "v:0").split(",")[:2])
    size = 34 if w >= 2400 else 22
    style = f"fontfile='{FONT}':fontsize={size}:fontcolor=yellow:box=1:boxcolor=black@0.7:boxborderw=4"
    vf = [f"drawgrid=w={a.step}:h={a.step}:t=2:c=yellow@0.55"]
    vf += [f"drawtext={style}:text='{x}':x={x + 6}:y=6" for x in range(0, w, a.step)]
    vf += [f"drawtext={style}:text='{y}':x=6:y={y + 6}" for y in range(a.step, h, a.step)]
    out = Path(a.out or Path(a.video).with_suffix(f".grid{int(a.second)}.png"))
    ff(["ffmpeg", "-y", "-nostats", "-loglevel", "error", "-ss", str(a.second), "-i", str(a.video),
        "-vf", ",".join(vf), "-frames:v", "1", "-update", "1", str(out)])
    print(f"{out}  ({w}x{h}; labels are pixels in the recording, use them directly for target and hide)")


def final(a):
    cfg_path = Path(a.shots).resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    work = cfg_path.parent / cfg.get("work", "cut")
    tl = work / "timeline.json"
    if not tl.exists():
        sys.exit("no timeline.json: run cut.py first")
    tl = json.loads(tl.read_text(encoding="utf-8"))
    video, shots = Path(tl["out"]), tl["shots"]
    for i, s in enumerate(shots):
        label = (f"drawtext=fontfile='{FONT}':text='{i:02d}':x=10:y=10:fontsize=36:"
                 "fontcolor=white:box=1:boxcolor=black@0.75:boxborderw=6")
        ff(["ffmpeg", "-y", "-nostats", "-loglevel", "error", "-ss", f"{s['start'] + s['dur'] / 2:.2f}",
            "-i", str(video), "-vf", f"scale=640:-2,{label}", "-frames:v", "1", "-update", "1",
            str(work / f"review_{i:02d}.png")])
    cols = min(4, len(shots))
    sheet = cfg_path.parent / "review.png"
    ff(["ffmpeg", "-y", "-nostats", "-loglevel", "error", "-start_number", "0", "-i", str(work / "review_%02d.png"),
        "-vf", f"tile={cols}x{math.ceil(len(shots) / cols)}", "-frames:v", "1", "-update", "1", str(sheet)])

    _, err = ff(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-vn",
                 "-af", "volumedetect,silencedetect=n=-45dB:d=2.5", "-f", "null", "-"])
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", err)
    peak = re.search(r"max_volume: (-?[\d.]+) dB", err)
    silences = re.findall(r"silence_start: ([\d.]+)", err)
    dur = float(probe(video, "format=duration"))
    has_audio = bool(probe(video, "stream=codec_name", "a:0"))
    checks = [
        ("has an audio track", has_audio, ""),
        ("length matches the shot list", abs(dur - tl["total"]) < 0.6, f"{dur:.1f}s vs {tl['total']:.1f}s"),
        ("voice is audible (mean -27..-14 dB)", bool(mean) and -27 <= float(mean[1]) <= -14, mean[1] if mean else "silent"),
        ("peaks are healthy (max -9..-0.3 dB)", bool(peak) and -9 <= float(peak[1]) <= -0.3, peak[1] if peak else "silent"),
        ("no silent gap over 2.5 s", not silences, f"gaps start at {silences}" if silences else ""),
    ]
    for i, s in enumerate(shots):
        print(f"  {i:02d} {s['start']:6.1f}s +{s['dur']:4.1f}s  {s['caption']}")
    ok = True
    for name, passed, note in checks:
        ok &= passed
        print(f"  {'PASS' if passed else 'FAIL'}  {name}  {note}")
    print(f"sheet: {sheet}\nNow LOOK at the sheet: sliced text, empty shots, a caption over the number it names, "
          "another window or a notification in frame, private data.")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("beats"); b.add_argument("video"); b.add_argument("--from", dest="start", type=float, default=0)
    b.add_argument("--to", type=float); b.add_argument("--every", type=float); b.add_argument("--out")
    b.set_defaults(fn=beats)
    g = sub.add_parser("grid"); g.add_argument("video"); g.add_argument("second", type=float)
    g.add_argument("--out"); g.add_argument("--step", type=int, default=240); g.set_defaults(fn=grid)
    f = sub.add_parser("final"); f.add_argument("shots"); f.set_defaults(fn=final)
    args = ap.parse_args()
    args.fn(args)
