"""Transcribe the public test set with Sada-ASR through the EchoNova speech-to-text API.

Writes a predictions file that `asr-bench evaluate` scores directly:

    pip install "arabic-asr-benchmark[hf,api] @ git+https://github.com/echonova-ai-solutions/arabic-asr-benchmark"
    export ECHONOVA_API_KEY=...        # your EchoNova API key
    python scripts/transcribe_with_sada_api.py --output sada-api.jsonl
    asr-bench evaluate --predictions sada-api.jsonl --system sada-asr-api --output sada-asr-api.json

Each clip is sent as 16 kHz 16-bit WAV, the exact samples of the released FLAC. Only the
transcript text of each response is kept. The script is resumable: clips already in the
output file are skipped, so it can be stopped and restarted.

The figures published in this repository were measured by EchoNova on its own hardware
with the evaluated version (Sada EchoNova v1), not through the API, so API results can
differ from them.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import threading
import time
import wave
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

API_URL = "https://api.echonova.ai/v1/speech-to-text"
RETRY_STATUS = {429, 500, 502, 503, 504}


def to_wav(flac_bytes: bytes) -> bytes:
    """Decode a released FLAC clip and re-encode it losslessly as 16-bit PCM WAV."""
    import soundfile as sf

    samples, rate = sf.read(io.BytesIO(flac_bytes), dtype="int16")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(samples.tobytes())
    return buf.getvalue()


def transcript_of(payload) -> str:
    """The transcript string of a response; everything else in the response is discarded."""
    if isinstance(payload, dict):
        for scope in (payload, payload.get("data")):
            if isinstance(scope, dict):
                for key in ("text", "transcription", "transcript"):
                    if isinstance(scope.get(key), str):
                        return scope[key]
    raise ValueError("the response has no transcript field")


def transcribe(
    session, wav: bytes, clip_id: str, api_key: str, language: str, retries: int, timeout: float
) -> str:
    for attempt in range(retries + 1):
        try:
            r = session.post(
                API_URL,
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (f"{clip_id}.wav", wav, "audio/wav")},
                data={"language": language},
                timeout=timeout,
            )
        except Exception as exc:  # network errors: retry
            error = type(exc).__name__
        else:
            if r.status_code == 200:
                return transcript_of(r.json())
            error = f"HTTP {r.status_code}"
            if r.status_code not in RETRY_STATUS:
                break
        if attempt < retries:
            time.sleep(min(2**attempt, 30))
    raise RuntimeError(f"{clip_id}: {error}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument(
        "--dataset",
        default="echonova-ai/arabic-dialect-asr-benchmark",
        help="Hugging Face dataset id or a local copy of it",
    )
    ap.add_argument(
        "--output", type=Path, required=True, help="predictions file (JSON Lines) to write or resume"
    )
    ap.add_argument(
        "--language",
        default="ar",
        choices=["auto", "ar", "en"],
        help="ar: Arabic and mixed Arabic/English speech (default for this test set)",
    )
    ap.add_argument("--workers", type=int, default=4, help="parallel requests")
    ap.add_argument("--retries", type=int, default=5)
    ap.add_argument("--timeout", type=float, default=120)
    ap.add_argument("--limit", type=int, help="only the first N clips (for a trial run)")
    a = ap.parse_args()

    api_key = os.environ.get("ECHONOVA_API_KEY")
    if not api_key:
        sys.exit("set ECHONOVA_API_KEY to your EchoNova API key")
    import requests
    from datasets import Audio, load_dataset

    ds = load_dataset(a.dataset, split="test").cast_column("audio", Audio(decode=False))
    if a.limit:
        ds = ds.select(range(min(a.limit, len(ds))))
    done = set()
    if a.output.exists():
        done = {json.loads(line)["id"] for line in a.output.open(encoding="utf-8") if line.strip()}
    todo = [i for i, clip_id in enumerate(ds["id"]) if clip_id not in done]
    print(f"{len(ds)} clips, {len(done)} already transcribed, {len(todo)} to go", file=sys.stderr)

    session, lock, failed = requests.Session(), threading.Lock(), []
    with a.output.open("a", encoding="utf-8") as out, ThreadPoolExecutor(a.workers) as pool:

        def job(i):
            row = ds[i]
            text = transcribe(
                session, to_wav(row["audio"]["bytes"]), row["id"], api_key, a.language, a.retries, a.timeout
            )
            with lock:
                out.write(json.dumps({"id": row["id"], "prediction": text}, ensure_ascii=False) + "\n")
                out.flush()

        for n, fut in enumerate(as_completed([pool.submit(job, i) for i in todo]), 1):
            try:
                fut.result()
            except Exception as exc:
                failed.append(str(exc))
            if n % 250 == 0:
                print(f"  {n}/{len(todo)}", file=sys.stderr)
    if failed:
        print(f"{len(failed)} clips failed (rerun to retry them), e.g. {failed[0]}", file=sys.stderr)
        return 1
    print(f"done: {a.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
