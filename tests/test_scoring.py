import json
from pathlib import Path

import pytest

from arabic_asr_benchmark.cli import main
from arabic_asr_benchmark.data import Reference
from arabic_asr_benchmark.evaluate import evaluate, score_utterances
from arabic_asr_benchmark.scoring import (
    LOOP_MAX_REPEATS,
    canonical_whitespace,
    crop_repetition_loops,
    get_scoring,
    list_scorings,
    resolve_scoring,
)

EX = Path(__file__).resolve().parents[1] / "examples" / "synthetic"


# ---- ported verbatim from the benchmark's tests (v2 final scoring rules) ----


def test_crop_repetition_loops_cuts_runaway_unigram():
    assert crop_repetition_loops("يالا " * 15008 + "شباب") == " ".join(["يالا"] * 10 + ["شباب"])


def test_crop_repetition_loops_cuts_runaway_phrase():
    assert crop_repetition_loops("حقا نعم " * 40) == " ".join(["حقا", "نعم"] * 10)


def test_crop_repetition_loops_keeps_real_stutter_and_text_unchanged():
    stutter = "اعتماد ال ال ال ال ال ال ال الشهادات"  # 7 repeats, the longest in any reference
    assert crop_repetition_loops(stutter) == stutter
    odd = "نص  فيه\nمسافات"  # untouched byte for byte when nothing is cropped
    assert crop_repetition_loops(odd) == odd


def test_canonical_whitespace():
    assert canonical_whitespace(" سطر اول\nسطر  ثاني ") == "سطر اول سطر ثاني"


# ---- package-specific ----


def test_crop_boundaries():
    word = "نعم"
    exactly = " ".join([word] * LOOP_MAX_REPEATS)
    assert crop_repetition_loops(exactly) == exactly  # 10 copies: not a loop
    assert crop_repetition_loops(" ".join([word] * (LOOP_MAX_REPEATS + 1))) == exactly
    tri = "ا ب ج "
    assert crop_repetition_loops(tri * 12) == " ".join(["ا", "ب", "ج"] * 10)
    quad = "ا ب ج د "  # 4-word units are out of scope
    assert crop_repetition_loops(quad * 12) == quad * 12
    assert crop_repetition_loops("") == ""


def test_registry_and_resolution():
    assert list_scorings() == ["none", "sada-paper"]
    assert resolve_scoring("auto", "echonova-v1").name == "sada-paper"
    for n in ("echonova-v1.1", "oual-2024-12", "oual-2026-07", "none"):
        assert resolve_scoring("auto", n).name == "none"
    assert resolve_scoring("none", "echonova-v1").name == "none"
    with pytest.raises(ValueError, match="only with"):
        resolve_scoring("sada-paper", "oual-2026-07")
    with pytest.raises(KeyError):
        get_scoring("paper")


def test_protocol_applies_crop_to_hypothesis_only_and_whitespace_to_both():
    loop = " ".join(["كلمة"] * 30)
    refs = [Reference("a", loop, "msa"), Reference("b", "نص  بمسافتين", "msa")]
    preds = {"a": loop, "b": "نص\nبمسافتين"}
    paper = score_utterances(refs, preds, "echonova-v1", scoring="sada-paper")
    plain = score_utterances(refs, preds, "echonova-v1", scoring="none")
    # the reference is never cropped: a looping reference is matched by a looping hypothesis
    # only up to the crop, so the cropped hypothesis is charged deletions
    assert plain[0].word_errors == 0 and paper[0].dele == 30 - LOOP_MAX_REPEATS
    # whitespace: WER unchanged, CER counts characters not layout
    assert plain[1].word_errors == paper[1].word_errors == 0
    assert plain[1].char_errors > 0 and paper[1].char_errors == 0


def test_evaluate_records_scoring():
    refs = [Reference("a", "نعم", "msa")]
    assert evaluate(refs, {"a": "نعم"}, "echonova-v1")["scoring"] == "sada-paper"
    assert evaluate(refs, {"a": "نعم"}, "oual-2026-07")["scoring"] == "none"
    assert evaluate(refs, {"a": "نعم"}, "echonova-v1", scoring="none")["scoring"] == "none"


def test_cli_scoring_flag(tmp_path, capsys):
    refs = str(EX / "references.jsonl")
    preds = str(EX / "predictions_system_a.jsonl")
    for scoring in ("auto", "none"):
        out = tmp_path / f"{scoring}.json"
        assert (
            main(
                [
                    "evaluate",
                    "--references",
                    refs,
                    "--predictions",
                    preds,
                    "--scoring",
                    scoring,
                    "--output",
                    str(out),
                ]
            )
            == 0
        )
        rec = json.loads(out.read_text())
        assert rec["scoring"] == ("sada-paper" if scoring == "auto" else "none")
    assert "scoring sada-paper" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main(
            [
                "evaluate",
                "--references",
                refs,
                "--predictions",
                preds,
                "--normalizer",
                "oual-2026-07",
                "--scoring",
                "sada-paper",
            ]
        )
