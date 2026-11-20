"""Batch voice-over with Kokoro-82M (Apache 2.0), fully local after the first model download.

Run it with the voice environment's Python (cut.py does this for you):

    python tts_kokoro.py jobs.json

jobs.json: {"voice": "af_heart", "speed": 1.0, "jobs": [{"text": "...", "out": "line.wav"}]}
The first letter of the voice is its language: a = American English, b = British English.
One process speaks every line, because loading the model is the slow part.
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

import numpy as np          # noqa: E402
import soundfile as sf      # noqa: E402
from kokoro import KPipeline  # noqa: E402

RATE = 24000


def main():
    spec = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    voice = spec.get("voice", "af_heart")
    pipe = KPipeline(lang_code=voice[0], repo_id="hexgrad/Kokoro-82M")
    for job in spec["jobs"]:
        parts = [np.asarray(r.audio) for r in pipe(job["text"], voice=voice, speed=float(spec.get("speed", 1.0)))]
        if not parts:
            sys.exit(f"no audio produced for: {job['text'][:60]!r}")
        audio = np.concatenate(parts)
        tmp = job["out"] + ".part"   # a half-written file must never look like a finished line
        sf.write(tmp, audio, RATE, format="WAV")
        os.replace(tmp, job["out"])
        print(f"  voice {len(audio) / RATE:5.2f}s  {job['text'][:60]}", flush=True)


if __name__ == "__main__":
    main()
