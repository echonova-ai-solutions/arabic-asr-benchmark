import json
from pathlib import Path

import pytest

from arabic_asr_benchmark.data import (
    PredictionError,
    load_predictions,
    load_references,
    validate_predictions,
)
from arabic_asr_benchmark.evaluate import evaluate, score_utterances
from arabic_asr_benchmark.normalization import get_normalizer

EX = Path(__file__).resolve().parents[1] / "examples" / "synthetic"
REFS = EX / "references.jsonl"


def _write(tmp_path, name, rows):
    p = tmp_path / name
    p.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    return p


def test_load_references_jsonl():
    refs = load_references(str(REFS))
    assert len(refs) == 12
    assert {r.dialect for r in refs} == {"msa", "egyptian", "lebanese"}
    assert refs[0].recording_id == "rec_01"


def test_load_references_parquet(tmp_path):
    pa = pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq

    rows = [json.loads(line) for line in REFS.read_text(encoding="utf-8").splitlines()]
    table = pa.Table.from_pylist([{**r, "audio": b"x"} for r in rows])
    pq.write_table(table, tmp_path / "refs.parquet")
    refs = load_references(str(tmp_path / "refs.parquet"))
    assert [r.id for r in refs] == [r["id"] for r in rows]


def test_reference_errors(tmp_path):
    with pytest.raises(ValueError, match="duplicate"):
        load_references(
            str(_write(tmp_path, "d.jsonl", [{"id": "a", "text": "x"}, {"id": "a", "text": "y"}]))
        )
    with pytest.raises(ValueError, match="lacks"):
        load_references(str(_write(tmp_path, "m.jsonl", [{"id": "a"}])))
    with pytest.raises(ValueError, match="unsupported"):
        load_references("refs.csv")
    bad = tmp_path / "bad.jsonl"
    bad.write_text("{not json}\n")
    with pytest.raises(ValueError, match="invalid JSON"):
        load_references(str(bad))


def test_prediction_validation(tmp_path):
    refs = load_references(str(REFS))
    rows = [
        {"id": "msa_00001", "prediction": "x"},
        {"id": "msa_00001", "prediction": "y"},
        {"id": "zzz", "prediction": "z"},
        {"id": "msa_00002", "prediction": ""},
    ]
    preds, dups = load_predictions(_write(tmp_path, "p.jsonl", rows))
    rep = validate_predictions(refs, preds, dups)
    assert not rep.ok
    assert rep.duplicates == ["msa_00001"] and rep.unknown == ["zzz"]
    assert len(rep.missing) == 10 and rep.empty == ["msa_00002"]
    assert "missing: 10" in rep.summary()
    with pytest.raises(PredictionError):
        load_predictions(_write(tmp_path, "q.jsonl", [{"id": "a", "text": "x"}]))
    with pytest.raises(PredictionError):
        load_predictions(_write(tmp_path, "r.jsonl", [{"id": "a", "prediction": 3}]))


def test_missing_predictions_fail_unless_allowed():
    refs = load_references(str(REFS))
    preds, _ = load_predictions(EX / "predictions_system_a.jsonl")
    del preds["msa_00001"]
    with pytest.raises(PredictionError, match="missing"):
        score_utterances(refs, preds, "echonova-v1")
    scores = score_utterances(refs, preds, "echonova-v1", allow_missing=True)
    assert scores[0].empty_hyp and scores[0].dele == scores[0].ref_words
    preds["extra"] = "x"
    with pytest.raises(PredictionError, match="unknown"):
        score_utterances(refs, preds, "echonova-v1", allow_missing=True)


def test_evaluate_record():
    refs = load_references(str(REFS))
    preds, _ = load_predictions(EX / "predictions_system_b.jsonl")
    res = evaluate(refs, preds, "echonova-v1", system={"name": "b"})
    norm = get_normalizer("echonova-v1")
    total_ref = sum(len(norm(r.text).split()) for r in refs)
    assert res["overall"]["ref_words"] == total_ref
    assert res["overall"]["empty_hypotheses"] == 1
    assert set(res["per_dialect"]) == {"egyptian", "lebanese", "msa"}
    per = [res["per_dialect"][d]["wer"] for d in res["macro"]["groups"]]
    assert res["macro"]["wer"] == pytest.approx(sum(per) / 3)
    assert (
        sum(res["per_dialect"][d]["word_errors"] for d in per and res["per_dialect"])
        == res["overall"]["word_errors"]
    )
    json.dumps(res)  # serializable


def test_perfect_system_scores_zero():
    refs = load_references(str(REFS))
    res = evaluate(refs, {r.id: r.text for r in refs}, "echonova-v1")
    assert res["overall"]["wer"] == 0 and res["overall"]["cer"] == 0


def test_load_references_local_hf_layout(tmp_path):
    pa = pytest.importorskip("pyarrow")
    import pyarrow.parquet as pq

    rows = [json.loads(line) for line in REFS.read_text(encoding="utf-8").splitlines()]
    (tmp_path / "data").mkdir()
    (tmp_path / "extra").mkdir()
    pq.write_table(pa.Table.from_pylist(rows[:6]), tmp_path / "data" / "test-00000-of-00002.parquet")
    pq.write_table(pa.Table.from_pylist(rows[6:]), tmp_path / "data" / "test-00001-of-00002.parquet")
    pq.write_table(pa.Table.from_pylist(rows[:2]), tmp_path / "extra" / "test-00000-of-00001.parquet")
    assert [r.id for r in load_references(str(tmp_path))] == [r["id"] for r in rows]
    assert len(load_references(str(tmp_path), config="extra")) == 2
