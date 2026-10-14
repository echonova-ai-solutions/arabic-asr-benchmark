"""Turn result records into CSV files and Markdown tables.

All published tables are generated from result records (``evaluate`` output),
never typed by hand. Markdown tables can be written into a README between
``<!-- BEGIN <name> -->`` and ``<!-- END <name> -->`` markers.
"""

from __future__ import annotations

import csv
import json
import re
from collections.abc import Iterable, Sequence
from pathlib import Path

__all__ = [
    "load_runs",
    "summary_rows",
    "per_dialect_rows",
    "markdown_table",
    "write_csv",
    "update_markers",
    "summary_markdown",
    "dialect_markdown",
]

SUMMARY_HEADER = [
    "system",
    "type",
    "normalizer",
    "scoring",
    "n_utterances",
    "ref_words",
    "wer",
    "macro_wer",
    "cer",
    "macro_cer",
    "sub",
    "del",
    "ins",
    "empty_rate",
]
PER_DIALECT_HEADER = [
    "system",
    "normalizer",
    "scoring",
    "dialect",
    "n_utterances",
    "ref_words",
    "ref_chars",
    "wer",
    "cer",
    "sub",
    "del",
    "ins",
    "empty_hypotheses",
]


def load_runs(paths: Iterable[str | Path]) -> list[dict]:
    runs = []
    for p in paths:
        p = Path(p)
        files = sorted(p.glob("*.json")) if p.is_dir() else [p]
        for f in files:
            with open(f, encoding="utf-8") as fh:
                runs.append(json.load(fh))
    return runs


def _name(run: dict) -> str:
    return run.get("system", {}).get("name", "unnamed")


def summary_rows(runs: Sequence[dict]) -> list[dict]:
    rows = []
    for r in runs:
        o = r["overall"]
        rows.append(
            {
                "system": _name(r),
                "type": r.get("system", {}).get("type", ""),
                "normalizer": r["normalizer"],
                "scoring": r.get("scoring", "none"),
                "n_utterances": o["n_utterances"],
                "ref_words": o["ref_words"],
                "wer": o["wer"],
                "macro_wer": r["macro"]["wer"],
                "cer": o["cer"],
                "macro_cer": r["macro"]["cer"],
                "sub": o["sub"],
                "del": o["del"],
                "ins": o["ins"],
                "empty_rate": o["empty_rate"],
            }
        )
    return sorted(rows, key=lambda x: (x["normalizer"], x["scoring"], x["wer"]))


def per_dialect_rows(runs: Sequence[dict]) -> list[dict]:
    rows = []
    for r in runs:
        for d, s in r["per_dialect"].items():
            rows.append(
                {
                    "system": _name(r),
                    "normalizer": r["normalizer"],
                    "scoring": r.get("scoring", "none"),
                    "dialect": d,
                    **{k: s[k] for k in PER_DIALECT_HEADER[4:]},
                }
            )
    return rows


def _fmt(v) -> str:
    if isinstance(v, float):
        return f"{v:.6f}"
    return str(v)


def write_csv(path: str | Path, header: Sequence[str], rows: Sequence[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for row in rows:
            w.writerow([_fmt(row[h]) for h in header])


def markdown_table(header: Sequence[str], rows: Sequence[Sequence[str]], align: str | None = None) -> str:
    align = align or "l" + "r" * (len(header) - 1)
    sep = ["---:" if a == "r" else ":---" for a in align]
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    lines += ["| " + " | ".join(r) + " |" for r in rows]
    return "\n".join(lines)


def _pct(x: float) -> str:
    return f"{100 * x:.2f}"


def summary_markdown(runs: Sequence[dict], display: dict[str, str] | None = None) -> str:
    """System | Type | WER | Macro WER | CER | Empty %, sorted by WER."""
    display = display or {}
    rows = [
        [
            display.get(r["system"], r["system"]),
            r["type"],
            _pct(r["wer"]),
            _pct(r["macro_wer"]),
            _pct(r["cer"]),
            _pct(r["empty_rate"]),
        ]
        for r in summary_rows(runs)
    ]
    return markdown_table(["System", "Type", "WER", "Macro WER", "CER", "Empty %"], rows, "llrrrr")


def dialect_markdown(
    runs: Sequence[dict],
    order: Sequence[str],
    metric: str = "wer",
    display: dict[str, str] | None = None,
) -> str:
    """Dialects as rows, systems (sorted by overall WER) as columns; best value in bold."""
    display = display or {}
    runs = sorted(runs, key=lambda r: r["overall"]["wer"])
    header = ["Dialect", "Clips"] + [display.get(_name(r), _name(r)) for r in runs]
    rows = []
    for d in order:
        vals = [r["per_dialect"][d][metric] for r in runs]
        best = min(vals)
        cells = [f"**{_pct(v)}**" if v == best else _pct(v) for v in vals]
        rows.append([d, str(runs[0]["per_dialect"][d]["n_utterances"])] + cells)
    return markdown_table(header, rows)


def update_markers(text: str, blocks: dict[str, str]) -> str:
    """Replace the content between ``<!-- BEGIN name -->`` / ``<!-- END name -->``."""
    for name, body in blocks.items():
        pattern = re.compile(
            rf"(<!-- BEGIN {re.escape(name)} -->\n).*?(<!-- END {re.escape(name)} -->)", re.S
        )
        if not pattern.search(text):
            raise KeyError(f"marker block {name!r} not found")
        text = pattern.sub(lambda m, body=body: m.group(1) + body.rstrip("\n") + "\n" + m.group(2), text)
    return text
