"""Loading references and predictions, with strict validation.

References
    ``hf:<org>/<name>[@<revision>]`` (Hugging Face Hub), a local dataset directory
    in Hugging Face layout, a ``.parquet`` file, or a ``.jsonl`` file. Records
    need ``id`` and ``text``; ``dialect`` and ``recording_id`` are optional.
    Audio columns are never decoded.

Predictions
    JSON Lines, one object per utterance: ``{"id": "...", "prediction": "..."}``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

__all__ = [
    "Reference",
    "PredictionError",
    "ValidationReport",
    "load_references",
    "load_predictions",
    "validate_predictions",
    "file_sha256",
]

_REF_COLUMNS = ("id", "text", "dialect", "recording_id")


@dataclass(frozen=True)
class Reference:
    id: str
    text: str
    dialect: str = "all"
    recording_id: str | None = None


class PredictionError(ValueError):
    """Raised when a predictions file does not match its references."""


def _records_to_refs(records: list[dict], source: str) -> list[Reference]:
    refs: list[Reference] = []
    seen = set()
    for i, r in enumerate(records):
        if "id" not in r or "text" not in r:
            raise ValueError(f"{source}: record {i} lacks 'id' or 'text'")
        rid = str(r["id"])
        if rid in seen:
            raise ValueError(f"{source}: duplicate reference id {rid!r}")
        seen.add(rid)
        text = r["text"]
        if not isinstance(text, str):
            raise ValueError(f"{source}: reference {rid!r} has non-string text")
        refs.append(
            Reference(
                id=rid,
                text=text,
                dialect=str(r.get("dialect") or "all"),
                recording_id=None if r.get("recording_id") is None else str(r["recording_id"]),
            )
        )
    if not refs:
        raise ValueError(f"{source}: no references")
    return refs


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError as e:
                    raise ValueError(f"{path}:{n}: invalid JSON ({e.msg})") from None
    return rows


def _read_parquet(path: Path) -> list[dict]:
    import pyarrow.parquet as pq

    schema = pq.read_schema(path)
    cols = [c for c in _REF_COLUMNS if c in schema.names]
    return pq.read_table(path, columns=cols).to_pylist()


def _read_hf(name: str, config: str | None, split: str, revision: str | None) -> list[dict]:
    try:
        from datasets import load_dataset
    except ImportError as e:  # pragma: no cover - exercised only without the extra
        raise ImportError(
            "loading Hugging Face datasets needs: pip install 'arabic-asr-benchmark[hf]'"
        ) from e
    ds = load_dataset(name, config, split=split, revision=revision)
    ds = ds.select_columns([c for c in _REF_COLUMNS if c in ds.column_names])
    return ds.to_list()


def _read_local_dir(path: Path, config: str | None, split: str) -> list[dict]:
    """Read a local copy of a dataset in Hugging Face layout without caching.

    Parquet shards are looked up as ``data/<split>-*.parquet`` for the default
    config and ``<config>/<split>-*.parquet`` otherwise; other layouts fall back to
    ``datasets.load_dataset``.
    """
    sub = "data" if config in (None, "default") else config
    files = sorted((path / sub).glob(f"{split}-*.parquet"))
    if not files:
        return _read_hf(str(path), config, split, None)
    rows: list[dict] = []
    for f in files:
        rows += _read_parquet(f)
    return rows


def load_references(
    source: str,
    *,
    config: str | None = None,
    split: str = "test",
) -> list[Reference]:
    """Load references from the Hub, a local HF dataset directory, parquet or JSONL."""
    if source.startswith("hf:"):
        name, _, revision = source[3:].partition("@")
        return _records_to_refs(_read_hf(name, config, split, revision or None), source)
    path = Path(source)
    if path.is_dir():
        return _records_to_refs(_read_local_dir(path, config, split), source)
    if path.suffix == ".parquet":
        return _records_to_refs(_read_parquet(path), source)
    if path.suffix == ".jsonl":
        return _records_to_refs(_read_jsonl(path), source)
    raise ValueError(
        f"unsupported reference source {source!r} (use hf:<repo>, a directory, .parquet or .jsonl)"
    )


@dataclass
class ValidationReport:
    n_references: int
    n_predictions: int
    missing: list[str] = field(default_factory=list)
    unknown: list[str] = field(default_factory=list)
    duplicates: list[str] = field(default_factory=list)
    empty: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (self.missing or self.unknown or self.duplicates)

    def summary(self) -> str:
        def few(ids: list[str]) -> str:
            return ", ".join(ids[:5]) + (" ..." if len(ids) > 5 else "")

        lines = [f"references: {self.n_references}  predictions: {self.n_predictions}"]
        for label, ids in (
            ("missing", self.missing),
            ("unknown", self.unknown),
            ("duplicate", self.duplicates),
            ("empty", self.empty),
        ):
            if ids:
                lines.append(f"{label}: {len(ids)} ({few(ids)})")
        return "\n".join(lines)


def load_predictions(path: str | Path) -> tuple[dict[str, str], list[str]]:
    """Read a predictions JSONL file. Returns (id -> prediction, duplicate ids)."""
    preds: dict[str, str] = {}
    duplicates: list[str] = []
    for n, row in enumerate(_read_jsonl(Path(path)), 1):
        if not isinstance(row, dict) or "id" not in row or "prediction" not in row:
            raise PredictionError(f"{path}: line {n} must be an object with 'id' and 'prediction'")
        pid, text = str(row["id"]), row["prediction"]
        if text is None:
            text = ""
        if not isinstance(text, str):
            raise PredictionError(f"{path}: prediction for {pid!r} is not a string")
        if pid in preds:
            duplicates.append(pid)
        preds[pid] = text
    return preds, duplicates


def validate_predictions(
    references: list[Reference], predictions: dict[str, str], duplicates: list[str] = ()
) -> ValidationReport:
    ref_ids = {r.id for r in references}
    return ValidationReport(
        n_references=len(references),
        n_predictions=len(predictions),
        missing=[r.id for r in references if r.id not in predictions],
        unknown=sorted(p for p in predictions if p not in ref_ids),
        duplicates=sorted(set(duplicates)),
        empty=[r.id for r in references if r.id in predictions and not predictions[r.id].strip()],
    )


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
