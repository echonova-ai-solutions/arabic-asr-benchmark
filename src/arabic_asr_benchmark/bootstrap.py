"""Paired bootstrap confidence intervals for WER differences.

For two systems scored on the same utterances, the statistic is

    delta = (errors_B - errors_A) / reference_words * 100

i.e. system A's margin over system B in WER points (positive = A is better).
Each resample draws utterances (``unit="clip"``) or whole recordings
(``unit="recording"``) with replacement; the CI is the 2.5th/97.5th percentile
(linear interpolation) of the resampled deltas.

With ``unit="clip"`` and the default seed and resample count this reproduces the
per-dialect intervals of the EchoNova Sada paper (Table 3), provided the groups
are visited in the same order with one generator per comparison
(see :func:`compare_by_group`). Clip-level intervals ignore that clips from the
same recording are correlated; prefer ``unit="recording"`` when recording ids
are available.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

__all__ = ["BootstrapResult", "paired_bootstrap", "compare_by_group"]

DEFAULT_RESAMPLES = 2000
DEFAULT_SEED = 0
_CHUNK_ELEMENTS = 20_000_000  # bound memory of the (resamples x units) index matrix


@dataclass(frozen=True)
class BootstrapResult:
    delta: float  # A's margin over B, WER points, on the full sample
    ci_low: float
    ci_high: float
    n_units: int
    n_resamples: int
    unit: str

    def to_dict(self) -> dict:
        return self.__dict__.copy()


def _resampled_deltas(
    err_a: np.ndarray, err_b: np.ndarray, ref: np.ndarray, n_resamples: int, rng: np.random.Generator
) -> np.ndarray:
    n = len(ref)
    rows_per_chunk = max(1, _CHUNK_ELEMENTS // max(n, 1))
    out = np.empty(n_resamples, dtype=np.float64)
    done = 0
    while done < n_resamples:
        k = min(rows_per_chunk, n_resamples - done)
        idx = rng.integers(0, n, size=(k, n))
        out[done : done + k] = (err_b[idx].sum(1) - err_a[idx].sum(1)) / ref[idx].sum(1) * 100
        done += k
    return out


def paired_bootstrap(
    errors_a: Sequence[int],
    errors_b: Sequence[int],
    ref_words: Sequence[int],
    *,
    groups: Sequence[str] | None = None,
    n_resamples: int = DEFAULT_RESAMPLES,
    rng: np.random.Generator | None = None,
) -> BootstrapResult:
    """Paired bootstrap of A's WER margin over B.

    ``errors_a``/``errors_b``/``ref_words`` are aligned per utterance. If
    ``groups`` is given, utterances are first summed per group and groups are
    resampled (cluster bootstrap).
    """
    rng = rng if rng is not None else np.random.default_rng(DEFAULT_SEED)
    ea, eb, L = (np.asarray(x, dtype=np.int64) for x in (errors_a, errors_b, ref_words))
    if not (len(ea) == len(eb) == len(L)):
        raise ValueError("errors_a, errors_b and ref_words must have the same length")
    if L.sum() == 0:
        raise ValueError("bootstrap undefined: total reference length is 0")
    unit = "clip"
    if groups is not None:
        if len(groups) != len(L):
            raise ValueError("groups must align with the utterances")
        _, inv = np.unique(np.asarray(groups, dtype=object).astype(str), return_inverse=True)
        ea, eb, L = (np.bincount(inv, weights=x).astype(np.int64) for x in (ea, eb, L))
        unit = "recording"
    delta = float((eb.sum() - ea.sum()) / L.sum() * 100)
    diffs = _resampled_deltas(ea, eb, L, n_resamples, rng)
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return BootstrapResult(delta, float(lo), float(hi), len(L), n_resamples, unit)


def compare_by_group(
    per_group: dict[str, tuple],
    *,
    order: Sequence[str],
    n_resamples: int = DEFAULT_RESAMPLES,
    seed: int = DEFAULT_SEED,
    cluster: bool = False,
) -> dict[str, BootstrapResult]:
    """Bootstrap one comparison per group, then pooled over all groups.

    ``per_group[g]`` is ``(errors_a, errors_b, ref_words, recording_ids)``.
    One generator seeded with ``seed`` is consumed across ``order`` and then the
    pooled comparison (key ``"overall"``), which is the procedure of the paper's
    Table 3 when ``cluster`` is False.
    """
    rng = np.random.default_rng(seed)
    out: dict[str, BootstrapResult] = {}
    pooled = ([], [], [], [])
    for g in order:
        ea, eb, L, rec = per_group[g]
        out[g] = paired_bootstrap(
            ea,
            eb,
            L,
            groups=[f"{g}/{r}" for r in rec] if cluster else None,
            n_resamples=n_resamples,
            rng=rng,
        )
        for acc, vals in zip(pooled, (ea, eb, L, [f"{g}/{r}" for r in rec]), strict=False):
            acc.extend(vals)
    out["overall"] = paired_bootstrap(
        pooled[0],
        pooled[1],
        pooled[2],
        groups=pooled[3] if cluster else None,
        n_resamples=n_resamples,
        rng=rng,
    )
    return out
