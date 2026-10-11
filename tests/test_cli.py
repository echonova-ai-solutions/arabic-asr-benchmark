import csv
import json
from pathlib import Path

from arabic_asr_benchmark.cli import main
from arabic_asr_benchmark.report import update_markers

EX = Path(__file__).resolve().parents[1] / "examples" / "synthetic"
REFS = str(EX / "references.jsonl")
A, B = str(EX / "predictions_system_a.jsonl"), str(EX / "predictions_system_b.jsonl")


def test_normalize(capsys):
    assert main(["normalize", "أحمدُ، مدرسة"]) == 0
    assert capsys.readouterr().out.strip() == "احمد مدرسه"


def test_validate(capsys):
    assert main(["validate", "--references", REFS, "--predictions", A]) == 0
    assert "OK" in capsys.readouterr().out


def test_evaluate_compare_report(tmp_path):
    meta = tmp_path / "systems.json"
    meta.write_text(
        json.dumps(
            {
                "a": {"display_name": "System A", "type": "open-weight"},
                "b": {"display_name": "System B", "type": "API"},
            }
        )
    )
    runs = tmp_path / "runs"
    for name, path in (("a", A), ("b", B)):
        assert (
            main(
                [
                    "evaluate",
                    "--references",
                    REFS,
                    "--predictions",
                    path,
                    "--system",
                    name,
                    "--system-meta",
                    str(meta),
                    "--output",
                    str(runs / f"{name}.json"),
                ]
            )
            == 0
        )
    rec = json.loads((runs / "a.json").read_text())
    assert rec["system"] == {"name": "a", "display_name": "System A", "type": "open-weight"}
    assert rec["predictions_sha256"] and rec["normalizer"] == "echonova-v1"

    out_csv = tmp_path / "boot.csv"
    assert (
        main(
            [
                "compare",
                "--references",
                REFS,
                "--predictions",
                f"a={A}",
                f"b={B}",
                "--baseline",
                "a",
                "--order",
                "msa,egyptian,lebanese",
                "--resamples",
                "200",
                "--output",
                str(out_csv),
            ]
        )
        == 0
    )
    rows = list(csv.DictReader(out_csv.open()))
    assert [r["group"] for r in rows] == ["msa", "egyptian", "lebanese", "overall"]
    assert all(r["unit"] == "recording" for r in rows)
    assert float(rows[-1]["delta_wer_points"]) > 0  # a is better than b

    readme = tmp_path / "README.md"
    readme.write_text(
        "x\n<!-- BEGIN t-summary -->\nold\n<!-- END t-summary -->\n"
        "<!-- BEGIN t-wer-by-dialect -->\n<!-- END t-wer-by-dialect -->\n"
        "<!-- BEGIN t-cer-by-dialect -->\n<!-- END t-cer-by-dialect -->\n"
    )
    assert (
        main(
            [
                "report",
                str(runs),
                "--out",
                str(tmp_path / "tables"),
                "--system-meta",
                str(meta),
                "--readme",
                str(readme),
                "--block",
                "t",
                "--order",
                "msa,egyptian,lebanese",
            ]
        )
        == 0
    )
    text = readme.read_text()
    assert "old" not in text and "System A" in text and "| msa |" in text
    assert (tmp_path / "tables" / "summary.csv").exists()
    # Regenerating is a no-op (tables are deterministic).
    main(
        [
            "report",
            str(runs),
            "--system-meta",
            str(meta),
            "--readme",
            str(readme),
            "--block",
            "t",
            "--order",
            "msa,egyptian,lebanese",
        ]
    )
    assert readme.read_text() == text


def test_update_markers_missing_block():
    import pytest

    with pytest.raises(KeyError):
        update_markers("no markers", {"x": "y"})
