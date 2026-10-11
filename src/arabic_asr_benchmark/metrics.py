"""Word and character error rates.

WER and CER are corpus-level micro averages: total edit distance divided by total
reference length, in whitespace-separated words or in characters (spaces
included). They are never the mean of per-utterance rates. Macro WER/CER is the
unweighted mean of per-group (per-dialect) corpus rates.

An empty reference contributes zero to the denominator; any hypothesis words for
it count as insertions. A corpus whose total reference length is zero has no
defined error rate and raises ``ValueError``.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, fields

import editdistance

__all__ = ["UtteranceScore", "CorpusScore", "score_utterance", "score_corpus", "macro_average"]


def _as_ids(a: Sequence[str], b: Sequence[str]) -> tuple[list[int], list[int]]:
    """Map tokens to integer ids so distances never depend on ``hash()`` values."""
    vocab: dict[str, int] = {}
    ia = [vocab.setdefault(t, len(vocab)) for t in a]
    ib = [vocab.setdefault(t, len(vocab)) for t in b]
    return ia, ib


def _distance(hyp: Sequence[str], ref: Sequence[str]) -> int:
    h, r = _as_ids(hyp, ref)
    return int(editdistance.eval(h, r))


def _align_counts(hyp: Sequence[str], ref: Sequence[str]) -> tuple[int, int, int]:
    """(substitutions, deletions, insertions) of a minimum-cost alignment.

    Ties are broken substitution > deletion > insertion, so the three counts always
    sum to the edit distance.
    """
    n, m = len(ref), len(hyp)
    if n == 0:
        return 0, 0, m
    if m == 0:
        return 0, n, 0
    prev = list(range(m + 1))
    ops = [["i"] * (m + 1)]
    for i in range(1, n + 1):
        cur = [i] + [0] * m
        row_ops = ["d"] + [""] * m
        ref_tok = ref[i - 1]
        for j in range(1, m + 1):
            if ref_tok == hyp[j - 1]:
                cur[j], row_ops[j] = prev[j - 1], "="
                continue
            sub_c, del_c, ins_c = prev[j - 1], prev[j], cur[j - 1]
            best = min(sub_c, del_c, ins_c)
            cur[j] = best + 1
            row_ops[j] = "s" if best == sub_c else ("d" if best == del_c else "i")
        ops.append(row_ops)
        prev = cur
    sub = dele = ins = 0
    i, j = n, m
    while i > 0 or j > 0:
        op = ops[i][j] if i > 0 else "i"
        if op in ("=", "s"):
            sub += op == "s"
            i, j = i - 1, j - 1
        elif op == "d":
            dele += 1
            i -= 1
        else:
            ins += 1
            j -= 1
    return sub, dele, ins


@dataclass(frozen=True)
class UtteranceScore:
    """Edit statistics for one (normalized) reference/hypothesis pair."""

    ref_words: int
    hyp_words: int
    word_errors: int
    sub: int
    dele: int
    ins: int
    ref_chars: int
    char_errors: int
    empty_hyp: bool


def score_utterance(reference: str, hypothesis: str) -> UtteranceScore:
    """Score one already-normalized pair."""
    ref_w, hyp_w = reference.split(), hypothesis.split()
    sub, dele, ins = _align_counts(hyp_w, ref_w)
    word_errors = _distance(hyp_w, ref_w)
    assert sub + dele + ins == word_errors
    return UtteranceScore(
        ref_words=len(ref_w),
        hyp_words=len(hyp_w),
        word_errors=word_errors,
        sub=sub,
        dele=dele,
        ins=ins,
        ref_chars=len(reference),
        char_errors=_distance(list(hypothesis), list(reference)),
        empty_hyp=hypothesis.strip() == "",
    )


@dataclass(frozen=True)
class CorpusScore:
    """Summed edit statistics over a set of utterances."""

    n_utterances: int = 0
    ref_words: int = 0
    hyp_words: int = 0
    word_errors: int = 0
    sub: int = 0
    dele: int = 0
    ins: int = 0
    ref_chars: int = 0
    char_errors: int = 0
    empty_hypotheses: int = 0

    @property
    def wer(self) -> float:
        if self.ref_words == 0:
            raise ValueError("WER undefined: total reference length is 0 words")
        return self.word_errors / self.ref_words

    @property
    def cer(self) -> float:
        if self.ref_chars == 0:
            raise ValueError("CER undefined: total reference length is 0 characters")
        return self.char_errors / self.ref_chars

    @property
    def empty_rate(self) -> float:
        return self.empty_hypotheses / self.n_utterances if self.n_utterances else 0.0

    def to_dict(self) -> dict:
        d = {f.name: getattr(self, f.name) for f in fields(self)}
        d["del"] = d.pop("dele")
        d.update(wer=self.wer, cer=self.cer, empty_rate=self.empty_rate)
        return d


def score_corpus(utterances: Iterable[UtteranceScore]) -> CorpusScore:
    totals = {f.name: 0 for f in fields(CorpusScore)}
    for u in utterances:
        totals["n_utterances"] += 1
        totals["ref_words"] += u.ref_words
        totals["hyp_words"] += u.hyp_words
        totals["word_errors"] += u.word_errors
        totals["sub"] += u.sub
        totals["dele"] += u.dele
        totals["ins"] += u.ins
        totals["ref_chars"] += u.ref_chars
        totals["char_errors"] += u.char_errors
        totals["empty_hypotheses"] += u.empty_hyp
    return CorpusScore(**totals)


def macro_average(values: Iterable[float]) -> float:
    """Unweighted mean (of unrounded per-group rates).

    Uses ``math.fsum`` (exactly rounded) so the result is identical on every
    Python version; the built-in ``sum`` of floats changed in Python 3.12.
    """
    vals = list(values)
    if not vals:
        raise ValueError("macro average of no groups")
    return math.fsum(vals) / len(vals)
