"""Command-line interface: ``asr-bench <command>``.

Commands
    normalize   print normalized text
    validate    check a predictions file against references
    evaluate    score one predictions file -> result record (JSON)
    compare     paired bootstrap of one system against others -> CSV
    report      result records -> CSV files and Markdown tables (optionally into a README)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .bootstrap import DEFAULT_RESAMPLES, DEFAULT_SEED, compare_by_group
from .data import file_sha256, load_predictions, load_references, validate_predictions
from .evaluate import evaluate, score_utterances
from .normalization import get_normalizer, list_normalizers
from .report import (
    PER_DIALECT_HEADER,
    SUMMARY_HEADER,
    dialect_markdown,
    load_runs,
    per_dialect_rows,
    summary_markdown,
    summary_rows,
    update_markers,
    write_csv,
)

DEFAULT_DATASET = "hf:echonova-ai/arabic-dialect-asr-benchmark"


def _add_reference_args(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--references",
        default=DEFAULT_DATASET,
        help="hf:<repo>[@rev], a local HF dataset directory, .parquet or .jsonl "
        f"(default: {DEFAULT_DATASET})",
    )
    p.add_argument("--config", default=None, help="dataset config, e.g. omani_unverified")
    p.add_argument("--split", default="test")


def _load_meta(path: str | None) -> dict[str, dict]:
    if not path:
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _dump(obj, path: str | None) -> None:
    text = json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def cmd_normalize(a: argparse.Namespace) -> int:
    norm = get_normalizer(a.normalizer)
    lines = [a.text] if a.text is not None else sys.stdin.read().splitlines()
    for line in lines:
        print(norm(line))
    return 0


def cmd_validate(a: argparse.Namespace) -> int:
    refs = load_references(a.references, config=a.config, split=a.split)
    preds, dups = load_predictions(a.predictions)
    report = validate_predictions(refs, preds, dups)
    print(report.summary())
    print("OK" if report.ok else "INVALID")
    return 0 if report.ok else 1


def cmd_evaluate(a: argparse.Namespace) -> int:
    refs = load_references(a.references, config=a.config, split=a.split)
    preds, dups = load_predictions(a.predictions)
    system = {
        "name": a.system or Path(a.predictions).stem,
        **_load_meta(a.system_meta).get(a.system or "", {}),
    }
    dataset = {
        "source": a.dataset_label or a.references,
        "config": a.config or "default",
        "split": a.split,
        "revision": a.dataset_revision,
        "n_references": len(refs),
    }
    result = evaluate(
        refs,
        preds,
        a.normalizer,
        allow_missing=a.allow_missing,
        duplicates=dups,
        system=system,
        dataset=dataset,
        predictions_sha256=file_sha256(a.predictions),
    )
    _dump(result, a.output)
    o = result["overall"]
    print(
        f"{system['name']}  [{a.normalizer}]  WER {100 * o['wer']:.2f}  "
        f"macro WER {100 * result['macro']['wer']:.2f}  CER {100 * o['cer']:.2f}  "
        f"n={o['n_utterances']}  missing={result['n_missing_predictions']}",
        file=sys.stderr,
    )
    return 0


def _parse_named(items: list[str]) -> dict[str, str]:
    out = {}
    for it in items:
        name, sep, path = it.partition("=")
        if not sep:
            name, path = Path(it).stem, it
        out[name] = path
    return out


def cmd_compare(a: argparse.Namespace) -> int:
    refs = load_references(a.references, config=a.config, split=a.split)
    named = _parse_named(a.predictions)
    if a.baseline not in named:
        raise SystemExit(f"--baseline {a.baseline!r} is not among the predictions: {', '.join(named)}")
    scores = {}
    for name, path in named.items():
        preds, dups = load_predictions(path)
        scores[name] = score_utterances(refs, preds, a.normalizer, duplicates=dups)
    if a.unit == "recording" and any(r.recording_id is None for r in refs):
        raise SystemExit("--unit recording needs a recording_id for every reference")
    order = a.order.split(",") if a.order else sorted({r.dialect for r in refs})
    rows = []
    for other in [n for n in named if n != a.baseline]:
        per_group = {}
        for g in order:
            idx = [i for i, r in enumerate(refs) if r.dialect == g]
            per_group[g] = (
                [scores[a.baseline][i].word_errors for i in idx],
                [scores[other][i].word_errors for i in idx],
                [scores[a.baseline][i].ref_words for i in idx],
                [refs[i].recording_id for i in idx],
            )
        res = compare_by_group(
            per_group, order=order, n_resamples=a.resamples, seed=a.seed, cluster=a.unit == "recording"
        )
        for g, b in res.items():
            rows.append(
                {
                    "baseline": a.baseline,
                    "other": other,
                    "normalizer": a.normalizer,
                    "group": g,
                    "unit": b.unit,
                    "n_units": b.n_units,
                    "resamples": b.n_resamples,
                    "seed": a.seed,
                    "delta_wer_points": b.delta,
                    "ci_low": b.ci_low,
                    "ci_high": b.ci_high,
                }
            )
    header = [
        "baseline",
        "other",
        "normalizer",
        "group",
        "unit",
        "n_units",
        "resamples",
        "seed",
        "delta_wer_points",
        "ci_low",
        "ci_high",
    ]
    if a.output:
        write_csv(a.output, header, rows)
    for r in rows:
        print(
            f"{r['baseline']} vs {r['other']:32s} {r['group']:10s} {r['delta_wer_points']:+6.2f} "
            f"[{r['ci_low']:+.2f}, {r['ci_high']:+.2f}]",
            file=sys.stderr,
        )
    return 0


def cmd_report(a: argparse.Namespace) -> int:
    runs = load_runs(a.runs)
    if not runs:
        raise SystemExit("no result records found")
    display = {k: v.get("display_name", k) for k, v in _load_meta(a.system_meta).items()}
    if a.out:
        out = Path(a.out)
        write_csv(out / "summary.csv", SUMMARY_HEADER, summary_rows(runs))
        write_csv(out / "per_dialect.csv", PER_DIALECT_HEADER, per_dialect_rows(runs))
    normalizers = sorted({r["normalizer"] for r in runs})
    if a.readme:
        if len(normalizers) != 1:
            raise SystemExit("README tables need runs from exactly one normalizer; filter with --normalizer")
        order = a.order.split(",") if a.order else sorted(runs[0]["per_dialect"])
        blocks = {
            f"{a.block}-summary": summary_markdown(runs, display),
            f"{a.block}-wer-by-dialect": dialect_markdown(runs, order, "wer", display),
            f"{a.block}-cer-by-dialect": dialect_markdown(runs, order, "cer", display),
        }
        path = Path(a.readme)
        path.write_text(update_markers(path.read_text(encoding="utf-8"), blocks), encoding="utf-8")
    else:
        for n in normalizers:
            print(f"## {n}\n\n" + summary_markdown([r for r in runs if r["normalizer"] == n], display) + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="asr-bench", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("normalize", help="print normalized text")
    s.add_argument("text", nargs="?", help="text to normalize (default: read lines from stdin)")
    s.add_argument("--normalizer", default="echonova-v1", choices=list_normalizers())
    s.set_defaults(func=cmd_normalize)

    s = sub.add_parser("validate", help="check a predictions file against references")
    _add_reference_args(s)
    s.add_argument("--predictions", required=True)
    s.set_defaults(func=cmd_validate)

    s = sub.add_parser("evaluate", help="score one predictions file")
    _add_reference_args(s)
    s.add_argument("--predictions", required=True, help='JSONL: {"id": ..., "prediction": ...}')
    s.add_argument("--normalizer", default="echonova-v1", choices=list_normalizers())
    s.add_argument("--system", help="system name (default: predictions file stem)")
    s.add_argument("--system-meta", help="JSON file mapping system name -> metadata to record")
    s.add_argument("--dataset-revision", help="dataset revision to record in the result")
    s.add_argument("--dataset-label", help="dataset name to record instead of the --references value")
    s.add_argument(
        "--allow-missing", action="store_true", help="score missing predictions as empty instead of failing"
    )
    s.add_argument("--output", help="write the result record here (default: stdout)")
    s.set_defaults(func=cmd_evaluate)

    s = sub.add_parser("compare", help="paired bootstrap CIs of one system against others")
    _add_reference_args(s)
    s.add_argument("--predictions", nargs="+", required=True, help="name=path.jsonl (or path; name = stem)")
    s.add_argument("--baseline", required=True)
    s.add_argument("--normalizer", default="echonova-v1", choices=list_normalizers())
    s.add_argument("--unit", choices=["clip", "recording"], default="recording")
    s.add_argument("--resamples", type=int, default=DEFAULT_RESAMPLES)
    s.add_argument("--seed", type=int, default=DEFAULT_SEED)
    s.add_argument("--order", help="comma-separated dialect order (fixes RNG consumption order)")
    s.add_argument("--output", help="CSV output path")
    s.set_defaults(func=cmd_compare)

    s = sub.add_parser("report", help="result records -> CSV and Markdown")
    s.add_argument("runs", nargs="+", help="result JSON files or directories")
    s.add_argument("--out", help="directory for summary.csv and per_dialect.csv")
    s.add_argument("--system-meta", help="JSON file with display_name per system")
    s.add_argument("--readme", help="update marker blocks in this Markdown file")
    s.add_argument("--block", default="results", help="marker block name prefix")
    s.add_argument("--order", help="comma-separated dialect order for tables")
    s.set_defaults(func=cmd_report)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
