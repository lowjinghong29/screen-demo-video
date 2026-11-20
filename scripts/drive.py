"""Turn a short action list into desktop steps with human-looking cursor motion.

Usage:  python desktop.py glide '<action list>' ['[x,y]']     build and run in one go
        python drive.py '<action list>' ['[x,y]']             print the steps only

Actions:
  ["move", x, y]                 glide the cursor there
  ["click", x, y]                glide, settle, click
  ["scroll", x, y, "down", n]    glide, then wheel
  ["key", "ctrl+t"]
  ["type", x, y, "text", enter]  glide, click, type
  ["wait", 2.0]
"""
import json
import math
import sys

CUR = [1440, 900]      # assumed starting point; first glide corrects it anyway
STEPS = 16             # intermediate points per glide -> smooth travel


def ease(t):
    # ease-in-out cubic: slow start, quick middle, soft landing (how a hand moves)
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def glide(out, x, y):
    x0, y0 = CUR
    dist = math.hypot(x - x0, y - y0)
    if dist < 4:
        return
    n = max(6, min(STEPS, int(dist / 45) + 6))
    for i in range(1, n + 1):
        p = ease(i / n)
        out.append(["Move", {"loc": [round(x0 + (x - x0) * p), round(y0 + (y - y0) * p)]}])
    CUR[0], CUR[1] = x, y


def build(actions):
    out = []
    for a in actions:
        kind = a[0]
        if kind == "move":
            glide(out, a[1], a[2])
            out.append({"sleep": 0.6})
        elif kind == "click":
            glide(out, a[1], a[2])
            out.append({"sleep": 0.7})          # settle before pressing, like a person
            out.append(["Click", {"loc": [a[1], a[2]]}])
        elif kind == "scroll":
            glide(out, a[1], a[2])
            out.append({"sleep": 0.4})
            out.append(["Scroll", {"loc": [a[1], a[2]], "direction": a[3], "wheel_times": a[4]}])
        elif kind == "key":
            out.append(["Shortcut", {"shortcut": a[1]}])
        elif kind == "type":
            glide(out, a[1], a[2])
            out.append({"sleep": 0.5})
            out.append(["Type", {"loc": [a[1], a[2]], "text": a[3],
                                 "clear": True, "press_enter": bool(a[4])}])
        elif kind == "wait":
            out.append({"sleep": a[1]})
        else:
            raise SystemExit(f"unknown action {kind}")
    return out


if __name__ == "__main__":
    acts = json.loads(sys.argv[1])
    if len(sys.argv) > 2:                      # optional explicit start position
        CUR[0], CUR[1] = json.loads(sys.argv[2])
    print(json.dumps(build(acts)))
