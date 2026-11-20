"""Cut a screen recording into a narrated demo video.

    python cut.py shots.json

Per shot: trim -> optional speed-up -> solid boxes over private data -> crop to the output shape ->
ease a zoom toward one target pixel -> burn a caption -> scale. Then join the shots, lay the
voice-over on one timeline, level a music bed under it, and write the final MP4.

Every shot lasts as long as its spoken line plus a breath (or its "min"), measured from the real
audio, so narration can never run into the next shot.

shots.json (see references/shots-example.json):

  out                      output file, relative to this JSON              default demo.mp4
  width, height, fps       output format                                   default 1920 1080 30
  sources {"main": path}   named recordings a shot can point at
  crop [x,y,w,h]           part of the recording to keep, in its pixels    default: largest top-left
                                                                           area with the output shape
  voice, rate              Kokoro voice id and speed (local, open source)  default af_heart, 1.0
  music                    "pad" (generated here), a file path, or "none"  default pad
  music_under              dB the music sits below the voice               default 26
  shots[]
    src, in                which source, and the second the shot starts at
    say                    the narration line: one idea
    caption                on-screen text: a short statement
    min                    shortest shot length in seconds                 default 4
    target [x,y], zoom     pixel to centre on, and how far to push in      default no zoom
    speed                  play the source this many times faster          default 1
    hide [[x,y,w,h], ...]  solid boxes over data that must not be shown
"""

import hashlib
import json
import math
import re
import shutil
import struct
import subprocess
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = Path.home() / ".screen-demo-video"
BREATH = 0.85   # silence after a line before the next shot
LEAD = 0.35     # let the shot land before its line starts


def run(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, **kw)
    if p.returncode != 0:
        sys.exit(f"FAILED: {' '.join(str(c) for c in cmd[:6])}\n"
                 f"{p.stderr.decode('utf-8', 'ignore')[-2500:]}")
    return p


def probe(path, entries, stream=None):
    cmd = ["ffprobe", "-v", "error"] + (["-select_streams", stream] if stream else [])
    out = run(cmd + ["-show_entries", entries, "-of", "csv=p=0", str(path)]).stdout.decode().strip()
    return out.splitlines()[0] if out else ""


def dur_of(path):
    return float(probe(path, "format=duration"))


def size_of(path):
    w, h = probe(path, "stream=width,height", "v:0").split(",")[:2]
    return int(w), int(h)


def levels(path, limit=None):
    """(mean, max) volume in dB. The cut is levelled by measurement, because nobody is listening."""
    cmd = ["ffmpeg", "-hide_banner", "-nostats"] + (["-t", str(limit)] if limit else [])
    err = run(cmd + ["-i", str(path), "-vn", "-af", "volumedetect", "-f", "null", "-"]).stderr.decode("utf-8", "ignore")
    mean = re.search(r"mean_volume: (-?[\d.]+) dB", err)
    peak = re.search(r"max_volume: (-?[\d.]+) dB", err)
    if not (mean and peak):
        sys.exit(f"no audible sound in {path}")
    return float(mean[1]), float(peak[1])


def voice_python():
    cfg = HOME / "config.json"
    own = json.loads(cfg.read_text(encoding="utf-8")).get("voice_python") if cfg.exists() else None
    for p in (own, HOME / "voice" / "Scripts" / "python.exe"):
        if p and Path(p).exists():
            return str(p)
    sys.exit("voice environment missing: run  python scripts/setup_check.py  and follow its voice line")


def playable(path):
    if not path.exists():
        return False
    p = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                        str(path)], capture_output=True)
    return p.returncode == 0 and p.stdout.strip() not in (b"", b"N/A")


def narrate(cfg, shots, vo_dir):
    """Speak every line once, cache it by content, and derive each shot's length from the audio."""
    voice, rate = cfg.get("voice", "af_heart"), float(cfg.get("rate", 1.0))
    vo_dir.mkdir(parents=True, exist_ok=True)
    files, jobs = [], {}
    for s in shots:
        text = (s.get("say") or "").strip()
        if not text:
            files.append(None)
            continue
        # named by content, so an edited line is always spoken again and never reuses stale audio
        f = vo_dir / (hashlib.sha1(f"{voice}|{rate}|{text}".encode()).hexdigest()[:16] + ".wav")
        files.append(f)
        if not playable(f):
            jobs[str(f)] = text
    if jobs:
        print(f"  speaking {len(jobs)} line(s) with Kokoro (the first run downloads the model) ...", flush=True)
        spec = vo_dir / "jobs.json"
        spec.write_text(json.dumps({"voice": voice, "speed": rate,
                                    "jobs": [{"text": t, "out": o} for o, t in jobs.items()]}), encoding="utf-8")
        run([voice_python(), str(HERE / "tts_kokoro.py"), str(spec)])
    durs = []
    for i, (s, f) in enumerate(zip(shots, files)):
        vo = dur_of(f) if f else 0.0
        durs.append(max(float(s.get("min", 4.0)), vo + BREATH) if f else float(s.get("min", 4.0)))
        print(f"  {i:02d} {s.get('caption', '')[:34]:<34} vo {vo:5.2f}s  shot {durs[-1]:5.2f}s", flush=True)
    return files, durs


def geometry(cfg, path):
    """The part of the recording that becomes the frame: [x, y, w, h] in source pixels."""
    if cfg.get("crop"):
        return [int(v) for v in cfg["crop"]]
    sw, sh = size_of(path)
    ch = min(sh, int(sw * cfg["height"] / cfg["width"])) // 2 * 2
    cw = min(sw, int(ch * cfg["width"] / cfg["height"])) // 2 * 2
    return [0, 0, cw, ch]   # top-left: keeps the app, drops the taskbar


def render_shot(cfg, out_dir, i, shot, dur):
    W, H, FPS = cfg["width"], cfg["height"], cfg["fps"]
    cx, cy, cw, ch = shot["_geo"]
    Z = float(shot.get("zoom", 1.0))
    speed = float(shot.get("speed", 1.0))
    out = out_dir / f"{i:02d}.mp4"

    # a hard-killed capture carries odd timestamps; without the reset a time-based ramp never starts.
    # tpad holds the last frame, so a shot that outlasts its source freezes instead of desyncing the voice.
    chain = [f"setpts=(PTS-STARTPTS)/{speed}", f"fps={FPS}", f"tpad=stop_mode=clone:stop_duration={dur:.2f}"]
    for x, y, w, h in shot.get("hide", []):
        # a solid box, not a blur: blurred text can sometimes be recovered
        chain.append(f"drawbox=x={int(x)}:y={int(y)}:w={int(w)}:h={int(h)}:color={cfg.get('hide_color', '0x12101a')}:t=fill")
    chain.append(f"crop={cw}:{ch}:{cx}:{cy}")
    if Z > 1.001:
        if Z > cw / W + 0.005:
            print(f"  warning: shot {i:02d} zoom {Z} upscales (max sharp zoom here is {cw / W:.2f})", flush=True)
        tx, ty = shot.get("target", [cx + cw / 2, cy + ch / 2])
        # centre the window on the target, clamped so it never runs off the frame
        fx = min(max((tx - cx - (cw / Z) / 2) / (cw - cw / Z), 0.0), 1.0)
        fy = min(max((ty - cy - (ch / Z) / 2) / (ch - ch / Z), 0.0), 1.0)
        hold, ramp = cfg.get("hold", 1.5), cfg.get("ramp", 1.6)
        # crop evaluates its expressions ONCE at init, so a time-based zoom there is silently inert and
        # every shot comes out flat. zoompan re-evaluates per output frame.
        prog = f"min(max((on/{FPS}-{hold})/{ramp}\\,0)\\,1)"
        zexp = f"1+({Z}-1)*(0.5-0.5*cos(PI*{prog}))"
        chain.append(f"zoompan=z='{zexp}':x='(iw-iw/zoom)*{fx}':y='(ih-ih/zoom)*{fy}':d=1:s={W}x{H}:fps={FPS}")
    else:
        chain.append(f"scale={W}:{H}:flags=lanczos")
    chain.append("setsar=1")
    if shot.get("caption"):
        # read from a file with expansion off: no escaping rules, so any character is safe in a caption
        (out_dir / f"cap_{i:02d}.txt").write_text(shot["caption"], encoding="utf-8")
        chain.append(
            f"drawtext=fontfile='{cfg['font']}':textfile=cap_{i:02d}.txt:expansion=none:"
            f"fontcolor=white:fontsize={cfg.get('caption_size', 44)}:box=1:"
            f"boxcolor={cfg.get('caption_box', '0x12101aCC')}:boxborderw=22:"
            f"x=(w-text_w)/2:y=h-{cfg.get('caption_y', 140)}")
    chain.append(f"fade=t=in:st=0:d=0.25,fade=t=out:st={dur - 0.25:.2f}:d=0.25")
    run(["ffmpeg", "-y", "-nostats", "-loglevel", "error",
         "-ss", str(shot["in"]), "-t", f"{dur * speed:.3f}", "-i", str(shot["_path"]),
         "-vf", ",".join(chain), "-an", "-r", str(FPS), "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", str(out)],
        cwd=out_dir)   # the caption file is named relative to here
    return out


CHORDS = [(220.00, 261.63, 329.63), (174.61, 220.00, 261.63),
          (130.81, 164.81, 196.00), (196.00, 246.94, 293.66)]


def make_music(total, path, sr=44100, bar=6.0):
    """A soft Am-F-C-G pad, generated here so the track carries no licence."""
    frames = bytearray()
    nb = int(bar * sr)
    for i in range(int(total * sr)):
        ci = (i // nb) % len(CHORDS)
        pos = (i % nb) / nb
        env = min(pos / 0.25, 1.0) * min((1 - pos) / 0.3, 1.0)
        t = i / sr
        v = 0.0
        for k, f in enumerate(CHORDS[ci]):
            v += math.sin(2 * math.pi * f * (1 + 0.0016 * math.sin(2 * math.pi * 0.19 * t + k)) * t) / (2.6 + k)
        v += 0.30 * math.sin(2 * math.pi * CHORDS[ci][0] / 2 * t)
        s = int(max(-1.0, min(1.0, v * env * 0.21)) * 32767)
        frames += struct.pack("<hh", s, s)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
        w.writeframes(bytes(frames))


def main():
    cfg_path = Path(sys.argv[1] if len(sys.argv) > 1 else "shots.json").resolve()
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    base = cfg_path.parent
    cfg.setdefault("width", 1920); cfg.setdefault("height", 1080); cfg.setdefault("fps", 30)
    if "font" not in cfg:
        if not Path("C:/Windows/Fonts/segoeuib.ttf").exists():
            sys.exit('caption font not found: set "font" in shots.json (escape the drive colon, e.g. C\\:/path/font.ttf)')
        cfg["font"] = "C\\:/Windows/Fonts/segoeuib.ttf"

    work = (base / cfg.get("work", "cut")).resolve()
    if base not in work.parents:   # this folder is deleted below; it must never be the project or outside it
        sys.exit('"work" must be a folder inside the project folder')
    shots = cfg.get("shots") or sys.exit("shots.json has no shots")
    if not any((s.get("say") or "").strip() for s in shots):
        sys.exit('no narration: a demo needs a voice-over that explains each step; add "say" to the shots')
    for s in shots:
        s["_path"] = (base / cfg["sources"][s["src"]]).resolve()
        if not s["_path"].exists():
            sys.exit(f"source not found: {s['_path']}")
        s["_geo"] = geometry(cfg, s["_path"])
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)

    print("voice-over:")
    files, durs = narrate(cfg, shots, base / cfg.get("vo", "vo"))
    total = sum(durs)
    print(f"total {total:.1f}s")

    parts = []
    for i, (s, d) in enumerate(zip(shots, durs)):
        parts.append(render_shot(cfg, work, i, s, d))
        print(f"  cut {i:02d} {s.get('caption', '')}", flush=True)
    (work / "list.txt").write_text("".join(f"file '{p.name}'\n" for p in parts), encoding="utf-8")
    run(["ffmpeg", "-y", "-nostats", "-loglevel", "error", "-f", "concat", "-safe", "0",
         "-i", str(work / "list.txt"), "-c", "copy", str(work / "video.mp4")])

    # voice bus: every line placed at its shot's start, then measured
    vo_in, vo_f, t, k = [], [], 0.0, 0
    for f, d in zip(files, durs):
        if f:
            vo_in += ["-i", str(f)]
            vo_f.append(f"[{k}:a]aresample=48000,adelay={int((t + LEAD) * 1000)}:all=1[v{k}]")
            k += 1
        t += d
    vo_f.append("".join(f"[v{i}]" for i in range(k)) +
                f"amix=inputs={k}:duration=longest:normalize=0,apad=whole_dur={total:.3f}[vo]")
    vo_wav = work / "vo.wav"
    run(["ffmpeg", "-y", "-nostats", "-loglevel", "error", *vo_in, "-filter_complex", ";".join(vo_f),
         "-map", "[vo]", "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", str(vo_wav)])
    vo_mean, vo_peak = levels(vo_wav)
    vo_gain = -3.0 - vo_peak   # voice peaks at -3 dB whatever engine spoke it

    music = cfg.get("music", "pad")
    inputs = ["-i", str(work / "video.mp4"), "-i", str(vo_wav)]
    chain = f"[1:a]volume={vo_gain:.2f}dB[vo]"
    if music in (None, False, "none"):
        chain += ";[vo]anull[m]"
    else:
        if music == "pad":
            print("music bed ...", flush=True)
            bed, pre = work / "music.wav", "lowpass=f=2200,"
            make_music(total + 1, bed)
        else:
            bed, pre = (base / music).resolve(), ""
            if not bed.exists():
                sys.exit(f"music file not found: {bed}")
            inputs += ["-stream_loop", "-1"]
        bed_gain = (vo_mean + vo_gain - float(cfg.get("music_under", 26))) - levels(bed, 60)[0]
        inputs += ["-i", str(bed)]
        chain += (f";[2:a]{pre}volume={bed_gain:.2f}dB,atrim=0:{total:.3f},"
                  f"afade=t=in:st=0:d=2,afade=t=out:st={max(total - 3, 0):.2f}:d=3[bed];"
                  f"[vo][bed]amix=inputs=2:duration=first:normalize=0[m]")
    chain += ";[m]alimiter=limit=0.89:level=0[a]"

    final = base / cfg.get("out", "demo.mp4")
    final.parent.mkdir(parents=True, exist_ok=True)
    run(["ffmpeg", "-y", "-nostats", "-loglevel", "error", *inputs,
         "-filter_complex", chain, "-map", "0:v", "-map", "[a]",
         "-vf", f"fade=t=in:st=0:d=0.6,fade=t=out:st={max(total - 1.0, 0):.2f}:d=1.0", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-ac", "2", "-ar", "48000",
         "-movflags", "+faststart", str(final)])

    starts = [sum(durs[:i]) for i in range(len(durs))]
    (work / "timeline.json").write_text(json.dumps({
        "out": str(final), "total": total,
        "shots": [{"start": round(a, 3), "dur": round(d, 3), "caption": s.get("caption", ""), "say": s.get("say", "")}
                  for a, d, s in zip(starts, durs, shots)]}, indent=1), encoding="utf-8")

    print(f"\nOK  {final}")
    print(probe(final, "format=duration,size"), probe(final, "stream=width,height", "v:0"))
    print("next: python scripts/review.py final", cfg_path)


if __name__ == "__main__":
    main()
