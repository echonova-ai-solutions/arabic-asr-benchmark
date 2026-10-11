"""Regenerate every results table in README.md from the result files.

python scripts/update_readme.py           # rewrite README.md
python scripts/update_readme.py --check   # exit 1 if README.md is out of date (CI)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from arabic_asr_benchmark.report import (
    dialect_markdown,
    load_runs,
    markdown_table,
    summary_markdown,
    update_markers,
)

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["msa", "egyptian", "saudi", "emirati", "kuwaiti", "qatari", "syrian", "lebanese"]
LB_SETS = [
    ("sada", "SADA"),
    ("commonvoice", "CV 18.0"),
    ("masc_clean", "MASC-c"),
    ("masc_noisy", "MASC-n"),
    ("casablanca", "Casab."),
    ("mgb2", "MGB-2"),
    ("average (unweighted, 6 sets)", "Avg"),
]


def leaderboard_markdown() -> str:
    rows = {}
    for r in csv.DictReader(open(ROOT / "results/public_leaderboard/results.csv", encoding="utf-8")):
        rows[(r["normalizer"], r["test_set"])] = 100 * float(r["wer"])
    body = []
    for norm, label in (
        ("oual-2026-07", "leaderboard normalizer (`oual-2026-07`)"),
        ("echonova-v1", "EchoNova normalizer (`echonova-v1`)"),
    ):
        body.append([f"Sada-ASR, {label}"] + [f"{rows[(norm, s)]:.2f}" for s, _ in LB_SETS])
    return markdown_table(["System"] + [h for _, h in LB_SETS], body)


def blocks() -> dict[str, str]:
    meta = json.loads((ROOT / "results/echonova_20h/systems.json").read_text(encoding="utf-8"))
    display = {k: v["display_name"] for k, v in meta.items()}
    r20 = load_runs([ROOT / "results/echonova_20h/runs/echonova-v1"])
    r115 = load_runs([ROOT / "results/echonova_private_115h/runs"])
    return {
        "echonova-20h-summary": summary_markdown(r20, display),
        "echonova-20h-wer-by-dialect": dialect_markdown(r20, ORDER, "wer", display),
        "echonova-115h-summary": summary_markdown(r115, display),
        "public-leaderboard": leaderboard_markdown(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    path = ROOT / "README.md"
    old = path.read_text(encoding="utf-8")
    new = update_markers(old, blocks())
    if a.check:
        if new != old:
            print("README.md tables are out of date; run: python scripts/update_readme.py")
            return 1
        print("README.md tables are up to date")
        return 0
    path.write_text(new, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
