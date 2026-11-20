"""End-to-end self-check that never touches the desktop.

    python selfcheck.py        about two minutes; needs ffmpeg and the voice environment

It builds a synthetic recording, cuts a narrated video from it with the real voice, and proves the
parts that have gone wrong before: a zoom that silently does not animate, a hide box that hides
nothing, a shot that outruns its source, dead audio, and the safety refusals.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import desktop  # noqa: E402
import drive    # noqa: E402

PY = sys.executable


def sh(*cmd, ok=True):
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if ok and p.returncode != 0:
        sys.exit(f"FAILED {[str(c) for c in cmd[:4]]}\n{p.stdout[-1500:]}\n{p.stderr[-1500:]}")
    return p


def gray(video, t, crop=None):
    """One frame as small grayscale bytes, so frames can be compared by number."""
    vf = (f"crop={crop}," if crop else "") + "scale=64:36,format=gray"
    return subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", str(video), "-vf", vf,
                           "-frames:v", "1", "-f", "rawvideo", "-"], capture_output=True).stdout


def diff(a, b):
    return sum(abs(x - y) for x, y in zip(a, b)) / max(len(a), 1)


def mean(a):
    return sum(a) / max(len(a), 1)


def passed(name, cond, detail=""):
    print(f"  {'PASS' if cond else 'FAIL'}  {name}  {detail}")
    if not cond:
        sys.exit("SELFCHECK FAILED")


def main():
    # pure logic first: no ffmpeg, no voice
    steps = drive.build([["click", 500, 400]])
    moves = [s for s in steps if isinstance(s, list) and s[0] == "Move"]
    passed("cursor glides to the click", len(moves) > 5 and moves[-1][1]["loc"] == [500, 400]
           and steps[-1] == ["Click", {"loc": [500, 400]}], f"{len(moves)} moves")
    for bad in (("PowerShell", {}), ("App", {"mode": "launch_executable"}), ("Snapshot", {"save_path": "x.png"})):
        try:
            desktop.check(*bad)
        except SystemExit:
            continue
        passed(f"desktop driver refuses {bad[0]}", False)
    desktop.check("Click", {"loc": [1, 2]})
    passed("desktop driver refuses shell, launch_executable and save_path", True)

    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        sh("ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=white:s=2880x1800:r=30:d=12",
           "-vf", "drawgrid=w=160:h=160:t=6:c=black", "-c:v", "libx264", "-preset", "ultrafast",
           "-pix_fmt", "yuv420p", base / "src.mp4")
        cfg = {"out": "demo.mp4", "sources": {"main": "src.mp4"}, "shots": [
            {"src": "main", "in": 1, "say": "This is a self check of the screen demo cutter.",
             "caption": "Zoom moves", "target": [400, 300], "zoom": 1.5},
            {"src": "main", "in": 2, "say": "Private data is covered with a solid box.",
             "caption": "It's hidden: box, 100% solid", "hide": [[2000, 200, 400, 300]], "speed": 2},
            {"src": "main", "in": 10.5, "say": "And the last shot holds its final frame.", "caption": "Hold"}]}
        shots = base / "shots.json"

        shots.write_text(json.dumps(dict(cfg, work="..")), encoding="utf-8")
        r = sh(PY, HERE / "cut.py", shots, ok=False)
        passed("cut.py refuses a work folder outside the project", r.returncode != 0 and "inside the project" in r.stderr)
        silent = dict(cfg, shots=[dict(s, say="") for s in cfg["shots"]])
        shots.write_text(json.dumps(silent), encoding="utf-8")
        r = sh(PY, HERE / "cut.py", shots, ok=False)
        passed("cut.py refuses a video with no narration", r.returncode != 0 and "no narration" in r.stderr)

        shots.write_text(json.dumps(cfg), encoding="utf-8")
        print("  cutting a three-shot video with the real voice ...", flush=True)
        sh(PY, HERE / "cut.py", shots)
        out = base / "demo.mp4"
        tl = json.loads((base / "cut" / "timeline.json").read_text(encoding="utf-8"))
        s0, s1, s2 = (s["start"] for s in tl["shots"])

        size = sh("ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,duration",
                  "-of", "csv=p=0", out).stdout.strip().split(",")
        passed("output is 1920x1080", size[:2] == ["1920", "1080"], "x".join(size[:2]))
        passed("picture lasts the whole timeline (a shot past its source holds its frame)",
               abs(float(size[2]) - tl["total"]) < 0.3, f"{float(size[2]):.1f}s of {tl['total']:.1f}s")

        moved = diff(gray(out, s0 + 0.6), gray(out, s0 + 3.6))
        still = diff(gray(out, s2 + 0.6), gray(out, s2 + 3.0))
        passed("zoom animates", moved > 2.0, f"frame difference {moved:.1f}")
        passed("a shot without zoom stays still", still < 0.5, f"frame difference {still:.2f}")

        patch = "100:100:1420:180"   # inside the hide box once 2880 px is scaled to 1920
        open_, boxed = mean(gray(out, s0 + 0.6, patch)), mean(gray(out, s1 + 2.0, patch))
        passed("hide box covers its area", boxed < 40 < 150 < open_, f"brightness {open_:.0f} -> {boxed:.0f}")

        r = sh(PY, HERE / "review.py", "final", shots, ok=False)
        print("\n".join("    " + l for l in r.stdout.strip().splitlines() if "PASS" in l or "FAIL" in l))
        passed("review.py final passes (sound present, levelled, no dead gap)", r.returncode == 0)
        sh(PY, HERE / "review.py", "beats", base / "src.mp4", "--out", base / "beats.png")
        sh(PY, HERE / "review.py", "grid", base / "src.mp4", "3", "--out", base / "grid.png")
        passed("review.py beats and grid write their sheets",
               (base / "beats.png").stat().st_size > 1000 and (base / "grid.png").stat().st_size > 1000)
    print("SELFCHECK OK")


if __name__ == "__main__":
    main()
