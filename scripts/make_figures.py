"""Generate the README and dataset-card figures (SVG, light and dark) from the results.

Every number in a figure is read from the published result files (and, for the
test-set composition, from the dataset's parquet files); nothing is typed by hand.

    python scripts/make_figures.py --dataset <local copy of the HF dataset>

Writes assets/<name>-light.svg and assets/<name>-dark.svg.
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
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
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
}
# Row labels for the overview chart (full names, trimmed to fit the label column).
LABEL = {
    "sada-asr": "Sada-ASR (EchoNova)",
    "mai-transcribe-2": "Microsoft MAI-Transcribe-2",
    "gemini-3.5-transcribe": "Google Gemini 3.5 Transcribe",
    "gpt-transcribe": "OpenAI gpt-transcribe",
    "audar-asr-v1-turbo": "Audar-ASR-V1-Turbo",
    "nvidia-fastconformer-ar": "NVIDIA FastConformer (ar)",
    "whisper-large-v3": "OpenAI Whisper large-v3",
    "nemotron-3.5-asr-streaming-0.6b": "NVIDIA Nemotron-3.5 0.6B",
}
HIGHLIGHT = "sada-asr"

# Tokens: EchoNova website palette (echonova.ai) - paper #f7f3ec, ink #171310, brand red #d40000,
# warm neutrals - mapped onto the dataviz roles and validated against both surfaces.
THEMES = {
    "light": {
        "surface": "#f7f3ec",
        "ink": "#171310",
        "ink2": "#4a443e",
        "muted": "#7a726a",
        "grid": "#e9e2d9",
        "axis": "#ddd5ca",
        "border": "#e9e2d9",
        "accent": "#d40000",
        "rest": "#7a726a",
        "series": "#7a726a",
    },
    "dark": {
        "surface": "#171310",
        "ink": "#f7f3ec",
        "ink2": "#ddd5ca",
        "muted": "#898781",
        "grid": "#2b2621",
        "axis": "#3a342e",
        "border": "rgba(247,243,236,0.12)",
        "accent": "#d40000",
        "rest": "#898781",
        "series": "#898781",
    },
}
# Sequential single-hue red ramp (OKLCH hue 29, the brand red's hue), light -> dark, for the heatmap.
RAMP = ["#fdc9c1", "#ffa294", "#ff7a69", "#f75141", "#e4251b", "#c11911", "#981f16", "#722018", "#4d1c16"]
SERIF = "'Lyon Display', 'Iowan Old Style', Georgia, 'Times New Roman', serif"
ARABIC = "'Lyon Arabic Text', Amiri, 'Noto Naskh Arabic', 'Geeza Pro', serif"
LOGO = ASSETS / "echonova-logo.svg"


def _svg(width: int, height: int, body: list[str], t: dict, title: str) -> str:
    return "\n".join(
        [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
            f'role="img" aria-label="{escape(title)}">',
            f"<title>{escape(title)}</title>",
            f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="12" fill="{t["surface"]}" '
            f'stroke="{t["border"]}"/>',
            f'<g font-family="{FONT}">',
            *body,
            "</g>",
            "</svg>",
            "",
        ]
    )


def _text(x, y, s, t, size=13, color="ink", weight=400, anchor="start", extra=""):
    fill = t[color] if color in t else color
    return (
        f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
        f'text-anchor="{anchor}"{extra}>{escape(s)}</text>'
    )


def _hbar(x0, y, length, h, r, color):
    """Horizontal bar, square at the baseline, 4px-rounded data end."""
    if length <= r:
        return f'<rect x="{x0:.1f}" y="{y:.1f}" width="{max(length, 0):.1f}" height="{h}" fill="{color}"/>'
    x1 = x0 + length
    return (
        f'<path d="M{x0:.1f},{y:.1f} H{x1 - r:.1f} Q{x1:.1f},{y:.1f} {x1:.1f},{y + r:.1f} '
        f'V{y + h - r:.1f} Q{x1:.1f},{y + h:.1f} {x1 - r:.1f},{y + h:.1f} H{x0:.1f} Z" fill="{color}"/>'
    )


def _load_runs():
    meta = json.loads((R20 / "systems.json").read_text(encoding="utf-8"))
    summary = {
        r["system"]: r
        for r in csv.DictReader(open(R20 / "summary.csv", encoding="utf-8"))
        if r["normalizer"] == "echonova-v1"
    }
    per = {}
    for r in csv.DictReader(open(R20 / "per_dialect.csv", encoding="utf-8")):
        if r["normalizer"] == "echonova-v1":
            per[(r["system"], r["dialect"])] = 100 * float(r["wer"])
    return meta, summary, per


def wer_overview(t: dict, meta, summary) -> str:
    rows = sorted(summary.values(), key=lambda r: float(r["wer"]))
    w, left, right, top, row_h, bar_h = 820, 250, 92, 92, 36, 20
    plot_w = w - left - right
    vmax = 30.0
    h = top + row_h * len(rows) + 64
    n = int(rows[0]["n_utterances"])
    body = [
        _text(24, 38, "Word error rate on the public test set", t, 18, "ink", 600),
        _text(
            24,
            60,
            f"{n:,} clips, MSA and eight dialects · lower is better · paper scoring (echonova-v1 + sada-paper)",
            t,
            13,
            "ink2",
        ),
    ]
    for v in range(0, 31, 10):
        x = left + plot_w * v / vmax
        body.append(
            f'<line x1="{x:.1f}" y1="{top - 8}" x2="{x:.1f}" y2="{top + row_h * len(rows) - 8}" '
            f'stroke="{t["grid"] if v else t["axis"]}" stroke-width="1"/>'
        )
        body.append(_text(x, top + row_h * len(rows) + 10, f"{v}%", t, 12, "muted", anchor="middle"))
    for i, r in enumerate(rows):
        s = r["system"]
        y = top + i * row_h
        wer = 100 * float(r["wer"])
        hi = s == HIGHLIGHT
        body.append(_text(left - 14, y + 11, LABEL[s], t, 13, "ink", 600 if hi else 400, "end"))
        body.append(_text(left - 14, y + 26, meta[s]["type"], t, 11, "muted", anchor="end"))
        body.append(_hbar(left, y, plot_w * wer / vmax, bar_h, 4, t["accent"] if hi else t["rest"]))
        body.append(
            _text(left + plot_w * wer / vmax + 8, y + 15, f"{wer:.2f}%", t, 13, "ink", 600 if hi else 400)
        )
    body.append(
        _text(
            24,
            h - 18,
            "Source: results/echonova_20h/summary.csv. Per-clip outputs of every system are "
            "published, so these figures can be recomputed.",
            t,
            11,
            "muted",
        )
    )
    return _svg(w, h, body, t, "Word error rate of eight ASR systems on the EchoNova public Arabic test set")


def _ramp_color(v, lo, hi):
    k = 0 if hi == lo else round((v - lo) / (hi - lo) * (len(RAMP) - 1))
    return RAMP[max(0, min(len(RAMP) - 1, k))]


def _lum(hexcolor):
    c = [int(hexcolor[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def wer_heatmap(t: dict, meta, summary, per) -> str:
    systems = [r["system"] for r in sorted(summary.values(), key=lambda r: float(r["wer"]))]
    vals = [per[(s, d)] for s in systems for d in ORDER]
    lo, hi = min(vals), max(vals)
    left, top, cw, ch, gap = 112, 112, 86, 34, 2
    w = left + cw * len(systems) + 28
    h = top + ch * len(ORDER) + 88
    body = [
        _text(24, 38, "Word error rate by variety", t, 18, "ink", 600),
        _text(
            24,
            60,
            "Public test set · darker is worse · bold marks the best system in each row",
            t,
            13,
            "ink2",
        ),
    ]
    for j, s in enumerate(systems):
        x = left + j * cw + cw / 2
        body.append(_text(x, top - 14, SHORT[s], t, 12, "ink", 600 if s == HIGHLIGHT else 400, "middle"))
    for i, d in enumerate(ORDER):
        y = top + i * ch
        row = {s: per[(s, d)] for s in systems}
        best = min(row.values())
        body.append(_text(left - 12, y + ch / 2 + 4, VARIETY[d], t, 13, "ink", anchor="end"))
        for j, s in enumerate(systems):
            x = left + j * cw
            fill = _ramp_color(row[s], lo, hi)
            ink = "#0b0b0b" if _lum(fill) > 0.32 else "#ffffff"
            body.append(
                f'<rect x="{x + gap / 2:.1f}" y="{y + gap / 2:.1f}" width="{cw - gap}" height="{ch - gap}" '
                f'rx="3" fill="{fill}"><title>{escape(VARIETY[d])}, {escape(SHORT[s])}: '
                f"{row[s]:.2f}% WER</title></rect>"
            )
            body.append(
                _text(
                    x + cw / 2,
                    y + ch / 2 + 4,
                    f"{row[s]:.1f}",
                    t,
                    12,
                    ink,
                    700 if row[s] == best else 400,
                    "middle",
                )
            )
    ly = top + ch * len(ORDER) + 26
    lw = 220
    for k, c in enumerate(RAMP):
        body.append(
            f'<rect x="{left + k * lw / len(RAMP):.1f}" y="{ly}" width="{lw / len(RAMP) + 0.5:.1f}" '
            f'height="10" fill="{c}"/>'
        )
    body.append(_text(left - 8, ly + 9, f"{lo:.1f}%", t, 11, "muted", anchor="end"))
    body.append(_text(left + lw + 8, ly + 9, f"{hi:.1f}% WER", t, 11, "muted"))
    body.append(
        _text(
            24,
            h - 18,
            "Source: results/echonova_20h/per_dialect.csv (echonova-v1 + sada-paper scoring).",
            t,
            11,
            "muted",
        )
    )
    return _svg(w, h, body, t, "Word error rate by Arabic variety and system on the EchoNova public test set")


def composition(t: dict, dataset: Path) -> str:
    import pyarrow.parquet as pq

    hours, clips = dict.fromkeys(ORDER, 0.0), dict.fromkeys(ORDER, 0)
    for f in sorted((dataset / "data").glob("test-*.parquet")):
        tab = pq.read_table(f, columns=["dialect", "duration"]).to_pydict()
        for d, dur in zip(tab["dialect"], tab["duration"], strict=True):
            hours[d] += dur / 3600
            clips[d] += 1
    rows = sorted(ORDER, key=lambda d: -hours[d])
    w, left, right, top, row_h, bar_h = 820, 112, 170, 92, 30, 18
    plot_w = w - left - right
    vmax = max(hours.values())
    h = top + row_h * len(rows) + 52
    total_h, total_c = sum(hours.values()), sum(clips.values())
    body = [
        _text(24, 38, "What is in the public test set", t, 18, "ink", 600),
        _text(
            24,
            60,
            f"{total_h:.2f} hours · {total_c:,} clips · one sixth of every variety of the 120-hour "
            "private test set",
            t,
            13,
            "ink2",
        ),
    ]
    for i, d in enumerate(rows):
        y = top + i * row_h
        body.append(_text(left - 12, y + 13, VARIETY[d], t, 13, "ink", anchor="end"))
        body.append(_hbar(left, y, plot_w * hours[d] / vmax, bar_h, 4, t["series"]))
        body.append(
            _text(
                left + plot_w * hours[d] / vmax + 8,
                y + 13,
                f"{hours[d]:.2f} h · {clips[d]:,} clips",
                t,
                12,
                "ink2",
            )
        )
    body.append(
        _text(
            24,
            h - 18,
            "Source: the dataset's parquet files (duration of the released 16 kHz audio).",
            t,
            11,
            "muted",
        )
    )
    return _svg(w, h, body, t, "Hours and clips per Arabic variety in the EchoNova public test set")


def banner(t: dict, mode: str, summary, dataset: Path | None) -> str:
    w, h = 1200, 300
    logo = ""
    if LOGO.exists():
        src = LOGO.read_text(encoding="utf-8")
        inner = re.search(r"<g[^>]*>(.*)</g>", src, re.S).group(1)
        inner = inner.replace('fill="black"', f'fill="{t["ink"]}"')
        logo = f'<g transform="translate(64,60) scale(1.6)">{inner}</g>'
    n = int(next(iter(summary.values()))["n_utterances"])
    hours = ""
    if dataset is not None:
        import pyarrow.parquet as pq

        tot = sum(
            sum(pq.read_table(f, columns=["duration"]).column(0).to_pylist())
            for f in (dataset / "data").glob("test-*.parquet")
        )
        hours = f"{tot / 3600:.2f} hours · "
    # A stylised echo (Sada, صدى): arcs radiating from a source point, fading out.
    import math

    cx, cy = 1004, 150
    arcs = []
    for k, r in enumerate(range(34, 171, 34)):
        a = math.radians(48)
        x0, y0 = cx + r * math.cos(-a), cy + r * math.sin(-a)
        x1, y1 = cx + r * math.cos(a), cy + r * math.sin(a)
        arcs.append(
            f'<path d="M{x0:.1f},{y0:.1f} A{r},{r} 0 0 1 {x1:.1f},{y1:.1f}" fill="none" '
            f'stroke="{t["accent"]}" stroke-width="4" stroke-linecap="round" '
            f'opacity="{1 - k * 0.17:.2f}"/>'
        )
    body = [
        logo,
        _text(64, 150, "Arabic Dialect ASR Benchmark", t, 46, "ink", 500, extra=f' font-family="{SERIF}"'),
        _text(
            64,
            192,
            "Reproducible speech-recognition evaluation for MSA and eight Arabic dialects",
            t,
            19,
            "ink2",
        ),
        _text(
            64,
            238,
            f"{hours}{n:,} clips · 9 varieties · 8 systems · normalizers, scoring and per-clip outputs",
            t,
            15,
            "muted",
        ),
        f'<circle cx="{cx}" cy="{cy}" r="9" fill="{t["accent"]}"/>',
        *arcs,
        f'<text x="{cx - 26}" y="{cy + 14}" font-size="42" font-family="{ARABIC}" fill="{t["ink"]}" '
        f'text-anchor="end">صدى</text>',
    ]
    return _svg(w, h, body, t, "EchoNova Arabic Dialect ASR Benchmark")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", type=Path, help="local copy of the HF dataset (for the composition figure)")
    a = ap.parse_args()
    meta, summary, per = _load_runs()
    ASSETS.mkdir(exist_ok=True)
    for mode, t in THEMES.items():
        figs = {
            "wer-overview": wer_overview(t, meta, summary),
            "wer-by-variety": wer_heatmap(t, meta, summary, per),
            "banner": banner(t, mode, summary, a.dataset),
        }
        if a.dataset:
            figs["test-set-composition"] = composition(t, a.dataset)
        for name, svg in figs.items():
            (ASSETS / f"{name}-{mode}.svg").write_text(svg, encoding="utf-8")
    print("wrote", sorted(p.name for p in ASSETS.glob("*.svg")))


if __name__ == "__main__":
    main()
