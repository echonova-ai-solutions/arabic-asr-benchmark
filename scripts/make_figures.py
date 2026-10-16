"""Generate the README figures (SVG) from the results, in the EchoNova brand style (light palette).

Every number in a figure is read from the published result files (and, for the
test-set composition, from the dataset's parquet files); nothing is typed by hand.

    python scripts/make_figures.py --dataset <local copy of the HF dataset> [--out build/figures]

Brand rules applied (EchoNova Brand Book v4): papyrus #F7F3EC background, ink #171310
text, exactly one red #D40000 element per figure, no gradients, glow or waveforms;
Lyon Display for the hero headline only, Codec Pro for text, IBM Plex Mono for numbers;
the EchoNova logo alone (no Arabic lockup) on English material.

The PNGs in assets/ are the EchoNova design team's renders of these figures (with
Arabic labels, in EchoNova's licensed fonts, which are not distributed here); their
numbers were checked against the result files. This script draws the same figures
as SVG from the result files, so they can be regenerated when the results change.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
R20 = ROOT / "results" / "echonova_20h"
ASSETS = ROOT / "assets"
LOGO = ASSETS / "echonova-logo.svg"

TEXT = "'Codec Pro', 'Helvetica Neue', Helvetica, Arial, sans-serif"
DISPLAY = "'Lyon Display', Georgia, 'Times New Roman', serif"
MONO = "'IBM Plex Mono', 'SFMono-Regular', Menlo, Consolas, monospace"

ORDER = ["msa", "egyptian", "saudi", "emirati", "kuwaiti", "qatari", "omani", "syrian", "lebanese"]
VARIETY = {
    "msa": "MSA",
    "egyptian": "Egyptian",
    "saudi": "Saudi",
    "emirati": "Emirati",
    "kuwaiti": "Kuwaiti",
    "qatari": "Qatari",
    "omani": "Omani",
    "syrian": "Syrian",
    "lebanese": "Lebanese",
}
SHORT = {
    "sada-asr": "Sada-ASR",
    "mai-transcribe-2": "MAI-2",
    "gemini-3.5-transcribe": "Gemini",
    "gpt-transcribe": "gpt-transcr.",
    "audar-asr-v1-turbo": "Audar",
    "nvidia-fastconformer-ar": "FastConf.",
    "whisper-large-v3": "Whisper",
    "nemotron-3.5-asr-streaming-0.6b": "Nemotron",
    "elevenlabs-scribe-v2": "Scribe v2",
    "speechmatics-enhanced": "Speechm.",
    "jais-asr": "Jais",
    "cohere-transcribe-arabic": "Cohere",
}
LABEL = {
    "sada-asr": "Sada-ASR (EchoNova)",
    "mai-transcribe-2": "Microsoft MAI-Transcribe-2",
    "gemini-3.5-transcribe": "Google Gemini 3.5 Transcribe",
    "gpt-transcribe": "OpenAI gpt-transcribe",
    "audar-asr-v1-turbo": "Audar-ASR-V1-Turbo",
    "nvidia-fastconformer-ar": "NVIDIA FastConformer (ar)",
    "whisper-large-v3": "OpenAI Whisper large-v3",
    "nemotron-3.5-asr-streaming-0.6b": "NVIDIA Nemotron-3.5 0.6B",
    "elevenlabs-scribe-v2": "ElevenLabs Scribe v2",
    "speechmatics-enhanced": "Speechmatics Enhanced",
    "jais-asr": "IFM Jais-ASR",
    "cohere-transcribe-arabic": "Cohere Transcribe Arabic",
}
HIGHLIGHT = "sada-asr"

RED = "#d40000"
THEMES = {
    "light": {
        "surface": "#f7f3ec",
        "ink": "#171310",
        "ink2": "#4a443e",
        "muted": "#7a726a",
        "rule": "#ddd5ca",
        "grid": "#e9e2d9",
        "rest": "#7a726a",
        "series": "#4a443e",
        # papyrus -> ink, darker is worse
        "ramp": ["#e3dbcf", "#c2bbb0", "#a29b92", "#837d75", "#666059", "#4a443f", "#2f2b26", "#171310"],
        "ramp_note": "darker is worse",
    },
}


# --------------------------------------------------------------------------- helpers


def _svg(width: int, height: int, body: list[str], t: dict, title: str) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{escape(title)}">',
            f"<title>{escape(title)}</title>",
            f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" fill="{t["surface"]}" stroke="{t["rule"]}"/>',
            f'<g font-family="{TEXT}">',
            *body,
            "</g>",
            "</svg>",
            "",
        ]
    )


def _text(x, y, s, t, size=14, color="ink", weight=400, anchor="start", family=None, spacing=None):
    fill = t[color] if color in t else color
    fam = f' font-family="{family}"' if family else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}"{fam}{ls}>{escape(s)}</text>'
    )


def _eyebrow(x, y, s, t):
    return _text(x, y, s.upper(), t, 11, "muted", 400, family=MONO, spacing=2)


def _logo(t: dict, x: float, y: float, height: float) -> str:
    src = LOGO.read_text(encoding="utf-8")
    inner = re.search(r"<g[^>]*>(.*)</g>", src, re.S).group(1).replace('fill="black"', f'fill="{t["ink"]}"')
    return f'<g transform="translate({x:.1f},{y:.1f}) scale({height / 19:.4f})">{inner}</g>'


def _footer(t: dict, w: int, h: int, note: str) -> list[str]:
    # The logo's clear space is its own height on every side.
    return [
        f'<line x1="40" y1="{h - 52}" x2="{w - 40}" y2="{h - 52}" stroke="{t["rule"]}" stroke-width="1"/>',
        _text(40, h - 24, note, t, 11, "muted", family=MONO),
        _logo(t, w - 40 - 137.141 * 12 / 19, h - 34, 12),
    ]


def _hbar(x0, y, length, h, color):
    """Horizontal bar, square at the baseline, 2px-rounded data end."""
    r = 2
    if length <= r:
        return f'<rect x="{x0:.1f}" y="{y:.1f}" width="{max(length, 0):.1f}" height="{h}" fill="{color}"/>'
    x1 = x0 + length
    return (
        f'<path d="M{x0:.1f},{y:.1f} H{x1 - r:.1f} Q{x1:.1f},{y:.1f} {x1:.1f},{y + r:.1f} '
        f'V{y + h - r:.1f} Q{x1:.1f},{y + h:.1f} {x1 - r:.1f},{y + h:.1f} H{x0:.1f} Z" fill="{color}"/>'
    )


def _lum(hexcolor):
    c = [int(hexcolor[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _load_runs():
    meta = json.loads((R20 / "systems.json").read_text(encoding="utf-8"))
    summary = {
        r["system"]: r
        for r in csv.DictReader(open(R20 / "summary.csv", encoding="utf-8"))
        if r["normalizer"] == "echonova-v1"
    }
    per = {
        (r["system"], r["dialect"]): 100 * float(r["wer"])
        for r in csv.DictReader(open(R20 / "per_dialect.csv", encoding="utf-8"))
        if r["normalizer"] == "echonova-v1"
    }
    return meta, summary, per


def _dataset_stats(dataset: Path):
    import pyarrow.parquet as pq

    hours, clips = dict.fromkeys(ORDER, 0.0), dict.fromkeys(ORDER, 0)
    for f in sorted((dataset / "data").glob("test-*.parquet")):
        tab = pq.read_table(f, columns=["dialect", "duration"]).to_pydict()
        for d, dur in zip(tab["dialect"], tab["duration"], strict=True):
            hours[d] += dur / 3600
            clips[d] += 1
    return hours, clips


# --------------------------------------------------------------------------- figures


def banner(t: dict, summary, hours_total: float | None) -> str:
    """The hero: Lyon Display headline whose full stop is the one red element."""
    w, h = 1200, 340
    n = int(next(iter(summary.values()))["n_utterances"])
    stats = ([f"{hours_total:.2f} hours"] if hours_total else []) + [
        f"{n:,} clips",
        f"{len(ORDER)} varieties",
        f"{len(summary)} systems",
    ]
    body = [
        _eyebrow(64, 72, "Open benchmark · Arabic speech recognition", t),
        f'<text x="64" y="160" font-family="{DISPLAY}" font-size="60" font-weight="400" fill="{t["ink"]}">'
        f'Arabic Dialect ASR Benchmark<tspan fill="{RED}">.</tspan></text>',
        _text(
            64, 204, "Reproducible evaluation for Modern Standard Arabic and eight dialects.", t, 20, "ink2"
        ),
        f'<line x1="64" y1="244" x2="{w - 64}" y2="244" stroke="{t["rule"]}" stroke-width="1"/>',
        _text(64, 282, "  ·  ".join(s.upper() for s in stats), t, 14, "ink", 400, family=MONO, spacing=1),
        _logo(t, w - 64 - 137.141 * 22 / 19, 268, 22),
    ]
    return _svg(w, h, body, t, "EchoNova Arabic Dialect ASR Benchmark")


def wer_overview(t: dict, meta, summary) -> str:
    """Emphasis bar chart: Sada-ASR's bar is the one red element."""
    rows = sorted(summary.values(), key=lambda r: float(r["wer"]))
    w, left, right, top, row_h, bar_h = 880, 270, 100, 130, 38, 18
    plot_w = w - left - right
    vmax = 30.0
    h = top + row_h * len(rows) + 86
    n = int(rows[0]["n_utterances"])
    body = [
        _eyebrow(40, 48, "Results · public test set", t),
        _text(40, 82, "Word error rate", t, 24, "ink", 700),
        _text(
            40,
            106,
            f"{n:,} clips, MSA and eight dialects. Lower is better. Paper scoring "
            "(echonova-v1 + sada-paper).",
            t,
            14,
            "ink2",
        ),
    ]
    base_y = top + row_h * len(rows) - 12
    for v in range(0, 31, 10):
        x = left + plot_w * v / vmax
        body.append(
            f'<line x1="{x:.1f}" y1="{top - 10}" x2="{x:.1f}" y2="{base_y}" '
            f'stroke="{t["grid"] if v else t["rule"]}" stroke-width="1"/>'
        )
        body.append(_text(x, base_y + 20, f"{v}%", t, 11, "muted", anchor="middle", family=MONO))
    for i, r in enumerate(rows):
        s = r["system"]
        y = top + i * row_h
        wer = 100 * float(r["wer"])
        hi = s == HIGHLIGHT
        body.append(_text(left - 16, y + 9, LABEL[s], t, 14, "ink", 700 if hi else 400, "end"))
        body.append(
            _text(
                left - 16,
                y + 25,
                meta[s]["type"].upper(),
                t,
                9,
                "muted",
                anchor="end",
                family=MONO,
                spacing=1,
            )
        )
        body.append(_hbar(left, y, plot_w * wer / vmax, bar_h, RED if hi else t["rest"]))
        body.append(
            _text(
                left + plot_w * wer / vmax + 10,
                y + 14,
                f"{wer:.2f}%",
                t,
                13,
                "ink",
                500 if hi else 400,
                family=MONO,
            )
        )
    body += _footer(t, w, h, "Source: results/echonova_20h/summary.csv")
    return _svg(
        w, h, body, t, f"Word error rate of {len(rows)} ASR systems on the EchoNova public Arabic test set"
    )


def wer_heatmap(t: dict, meta, summary, per) -> str:
    """Ink-ramp heatmap; a red dot marks Sada-ASR's column (the one red element)."""
    ramp = t["ramp"]
    systems = [r["system"] for r in sorted(summary.values(), key=lambda r: float(r["wer"]))]
    vals = [per[(s, d)] for s in systems for d in ORDER]
    lo, hi = min(vals), max(vals)
    left, top, cw, ch, gap = 120, 168, 88, 34, 2
    w = left + cw * len(systems) + 40
    h = top + ch * len(ORDER) + 118
    body = [
        _eyebrow(40, 48, "Results · by variety", t),
        _text(40, 82, "Word error rate by variety", t, 24, "ink", 700),
        _text(
            40,
            106,
            f"Public test set, % WER. {t['ramp_note'].capitalize()}; bold marks the best system in each row.",
            t,
            14,
            "ink2",
        ),
    ]
    for j, s in enumerate(systems):
        x = left + j * cw + cw / 2
        is_hi = s == HIGHLIGHT
        body.append(_text(x, top - 14, SHORT[s], t, 12, "ink", 700 if is_hi else 400, "middle"))
        if is_hi:
            body.append(f'<circle cx="{x:.1f}" cy="{top - 38:.1f}" r="4" fill="{RED}"/>')
    for i, d in enumerate(ORDER):
        y = top + i * ch
        row = {s: per[(s, d)] for s in systems}
        best = min(row.values())
        body.append(_text(left - 14, y + ch / 2 + 5, VARIETY[d], t, 13, "ink", anchor="end"))
        for j, s in enumerate(systems):
            x = left + j * cw
            k = 0 if hi == lo else round((row[s] - lo) / (hi - lo) * (len(ramp) - 1))
            fill = ramp[max(0, min(len(ramp) - 1, k))]
            ink = "#171310" if _lum(fill) > 0.3 else "#f7f3ec"
            body.append(
                f'<rect x="{x + gap / 2:.1f}" y="{y + gap / 2:.1f}" width="{cw - gap}" height="{ch - gap}" '
                f'fill="{fill}"><title>{escape(VARIETY[d])}, {escape(SHORT[s])}: {row[s]:.2f}% WER</title></rect>'
            )
            body.append(
                _text(
                    x + cw / 2,
                    y + ch / 2 + 4,
                    f"{row[s]:.1f}",
                    t,
                    12,
                    ink,
                    600 if row[s] == best else 400,
                    "middle",
                    family=MONO,
                )
            )
    ly = top + ch * len(ORDER) + 28
    lw = 240
    for k, c in enumerate(ramp):
        body.append(
            f'<rect x="{left + k * lw / len(ramp):.1f}" y="{ly}" width="{lw / len(ramp) + 0.5:.1f}" '
            f'height="10" fill="{c}"/>'
        )
    body.append(_text(left - 8, ly + 9, f"{lo:.1f}%", t, 11, "muted", anchor="end", family=MONO))
    body.append(_text(left + lw + 8, ly + 9, f"{hi:.1f}%", t, 11, "muted", family=MONO))
    body += _footer(t, w, h, "Source: results/echonova_20h/per_dialect.csv")
    return _svg(w, h, body, t, "Word error rate by Arabic variety and system on the EchoNova public test set")


def composition(t: dict, hours: dict, clips: dict) -> str:
    """Neutral bars; the title's red full stop is the one red element."""
    rows = sorted(ORDER, key=lambda d: -hours[d])
    w, left, right, top, row_h, bar_h = 880, 120, 210, 130, 32, 16
    plot_w = w - left - right
    vmax = max(hours.values())
    h = top + row_h * len(rows) + 90
    total_h, total_c = sum(hours.values()), sum(clips.values())
    body = [
        _eyebrow(40, 48, "Dataset · public test set", t),
        f'<text x="40" y="82" font-size="24" font-weight="700" fill="{t["ink"]}">What is in the test set'
        f'<tspan fill="{RED}">.</tspan></text>',
        _text(
            40,
            106,
            f"{total_h:.2f} hours and {total_c:,} clips: one sixth of every variety of the 120-hour "
            "private test set.",
            t,
            14,
            "ink2",
        ),
    ]
    for i, d in enumerate(rows):
        y = top + i * row_h
        body.append(_text(left - 14, y + 13, VARIETY[d], t, 13, "ink", anchor="end"))
        body.append(_hbar(left, y, plot_w * hours[d] / vmax, bar_h, t["series"]))
        body.append(
            _text(
                left + plot_w * hours[d] / vmax + 10,
                y + 13,
                f"{hours[d]:.2f} h · {clips[d]:,} clips",
                t,
                12,
                "ink2",
                family=MONO,
            )
        )
    body += _footer(t, w, h, "Source: the dataset's parquet files (released 16 kHz audio)")
    return _svg(w, h, body, t, "Hours and clips per Arabic variety in the EchoNova public test set")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--dataset", type=Path, help="local copy of the HF dataset (composition figure, banner hours)"
    )
    ap.add_argument("--out", type=Path, default=ROOT / "build" / "figures")
    a = ap.parse_args()
    meta, summary, per = _load_runs()
    hours = clips = None
    if a.dataset:
        hours, clips = _dataset_stats(a.dataset)
    a.out.mkdir(parents=True, exist_ok=True)
    t = THEMES["light"]
    figs = {
        "banner": banner(t, summary, sum(hours.values()) if hours else None),
        "wer-overview": wer_overview(t, meta, summary),
        "wer-by-variety": wer_heatmap(t, meta, summary, per),
    }
    if hours:
        figs["test-set-composition"] = composition(t, hours, clips)
    for name, svg in figs.items():
        (a.out / f"{name}.svg").write_text(svg, encoding="utf-8")
    print("wrote", sorted(p.name for p in a.out.glob("*.svg")))


if __name__ == "__main__":
    main()
