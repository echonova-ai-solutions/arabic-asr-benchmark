"""Score a set of predictions against references and build a result record."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Sequence

from . import __version__
from .data import PredictionError, Reference, validate_predictions
from .metrics import CorpusScore, UtteranceScore, macro_average, score_corpus, score_utterance
from .normalization import get_normalizer
from .scoring import resolve_scoring

__all__ = ["SCHEMA_VERSION", "score_utterances", "evaluate"]

SCHEMA_VERSION = 1


def score_utterances(
    references: Sequence[Reference],
    predictions: dict[str, str],
    normalizer: str,
    *,
    allow_missing: bool = False,
    duplicates: Sequence[str] = (),
    scoring: str = "auto",
) -> list[UtteranceScore]:
    """Validate and score every reference, in reference order.

    Missing, unknown or duplicate prediction ids are errors. With
    ``allow_missing``, a missing prediction is scored as an empty hypothesis
    (every reference word deleted); unknown and duplicate ids remain errors.
    ``scoring`` names a protocol from :mod:`arabic_asr_benchmark.scoring`
    (``"auto"`` picks it from the normalizer).
    """
    report = validate_predictions(list(references), predictions, list(duplicates))
    problems = report.unknown or report.duplicates or (report.missing and not allow_missing)
    if problems:
        raise PredictionError("predictions do not match the references\n" + report.summary())
    norm = get_normalizer(normalizer)
    protocol = resolve_scoring(scoring, normalizer)
    return [
        score_utterance(
            protocol.reference(norm(r.text)), protocol.hypothesis(norm(predictions.get(r.id, "")))
        )
        for r in references
    ]


def _group_scores(
    references: Sequence[Reference], scores: Sequence[UtteranceScore]
) -> dict[str, CorpusScore]:
    groups: dict[str, list[UtteranceScore]] = defaultdict(list)
    for r, s in zip(references, scores, strict=False):
        groups[r.dialect].append(s)
    return {g: score_corpus(v) for g, v in sorted(groups.items())}


def evaluate(
    references: Sequence[Reference],
    predictions: dict[str, str],
    normalizer: str,
    *,
    allow_missing: bool = False,
    duplicates: Sequence[str] = (),
    system: dict | None = None,
    dataset: dict | None = None,
    predictions_sha256: str | None = None,
    scoring: str = "auto",
) -> dict:
    """Return a JSON-serializable result record (schema version 1)."""
    protocol = resolve_scoring(scoring, normalizer)
    scores = score_utterances(
        references,
        predictions,
        normalizer,
        allow_missing=allow_missing,
        duplicates=duplicates,
        scoring=protocol.name,
    )
    overall = score_corpus(scores)
    per_dialect = _group_scores(references, scores)
    n_missing = sum(r.id not in predictions for r in references)
    return {
        "schema_version": SCHEMA_VERSION,
        "system": system or {},
        "dataset": dataset or {},
        "normalizer": normalizer,
        "scoring": protocol.name,
        "package": {"name": "arabic-asr-benchmark", "version": __version__},
        "predictions_sha256": predictions_sha256,
        "n_missing_predictions": n_missing,
        "overall": overall.to_dict(),
        "macro": {
            "wer": macro_average(c.wer for c in per_dialect.values()),
            "cer": macro_average(c.cer for c in per_dialect.values()),
            "groups": list(per_dialect),
        },
        "per_dialect": {g: c.to_dict() for g, c in per_dialect.items()},
    }
