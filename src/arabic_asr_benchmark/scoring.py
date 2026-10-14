"""Scoring protocols: steps applied after normalization, before WER/CER.

A scoring protocol is a named, versioned pair of text transformations, one for the
hypothesis and one for the reference, applied to already-normalized text. Like
normalizers, a registered name never changes behaviour.

Registered protocols
--------------------
``none``
    Score the normalized strings as they are.
``sada-paper``
    The scoring of the EchoNova Sada paper on private test set v2. Requires the
    ``echonova-v1`` normalizer. Two rules, applied identically to every system and
    never using the reference to change a hypothesis:

    1. **Loop crop (hypothesis only).** Any 1-3-word unit repeated more than 10
       times back-to-back is cut to 10 copies. The longest real back-to-back
       repetition in any reference of the test set is 7 (a stutter), so no correct
       transcript is altered; runaway outputs (one system returned one word 15,008
       times) are.
    2. **Whitespace canonicalization (both sides).** Every whitespace run becomes
       one space, so CER counts characters rather than layout (line breaks, double
       spaces). WER is unaffected.

``asr-bench`` chooses the protocol automatically from the normalizer unless one is
given: ``sada-paper`` with ``echonova-v1``, ``none`` with every other normalizer
(the Open Universal Arabic ASR Leaderboard's own scoring does not crop loops).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

__all__ = [
    "LOOP_MAX_REPEATS",
    "LOOP_MAX_NGRAM",
    "canonical_whitespace",
    "crop_repetition_loops",
    "ScoringProtocol",
    "get_scoring",
    "list_scorings",
    "resolve_scoring",
]

# Longest back-to-back repetition in any reference of private test set v2: 7 for one
# word (a stutter), 6 for a 2-word phrase, 3 for a 3-word phrase. A cap of 10 never
# alters a reference but cuts runaway loops.
LOOP_MAX_REPEATS = 10
LOOP_MAX_NGRAM = 3


def canonical_whitespace(text: str) -> str:
    """Collapse any whitespace run (line breaks, double spaces) to one space.

    Layout is not transcription: without this, CER (computed on characters)
    charges a line break between phrases as a substitution and every extra space
    as an insertion.
    """
    return " ".join(text.split())


def crop_repetition_loops(
    text: str, max_repeats: int = LOOP_MAX_REPEATS, max_ngram: int = LOOP_MAX_NGRAM
) -> str:
    """Keep at most ``max_repeats`` back-to-back copies of any 1..``max_ngram``-word unit.

    Returns ``text`` unchanged (byte for byte) when nothing is cropped.
    """
    words = text.split()
    cropped = False
    for n in range(1, max_ngram + 1):
        out, i = [], 0
        while i < len(words):
            unit = words[i : i + n]
            j, reps = i + n, 1
            while len(unit) == n and words[j : j + n] == unit:
                reps += 1
                j += n
            if reps > max_repeats:
                out += unit * max_repeats
                i, cropped = j, True
            else:
                out.append(words[i])
                i += 1
        words = out
    return " ".join(words) if cropped else text


def _identity(text: str) -> str:
    return text


@dataclass(frozen=True)
class ScoringProtocol:
    """A named pair of post-normalization steps for hypothesis and reference."""

    name: str
    description: str
    hypothesis: Callable[[str], str] = field(repr=False)
    reference: Callable[[str], str] = field(repr=False)
    normalizers: tuple[str, ...] | None = None  # normalizers it may be combined with (None: any)


_REGISTRY: dict[str, ScoringProtocol] = {
    p.name: p
    for p in (
        ScoringProtocol("none", "Score the normalized strings as they are.", _identity, _identity),
        ScoringProtocol(
            "sada-paper",
            "EchoNova Sada paper scoring (private test set v2): echonova-v1, then loops of any "
            "1-3-word unit repeated more than 10 times cropped to 10 copies in the hypothesis, "
            "and whitespace canonicalized on both sides.",
            lambda h: canonical_whitespace(crop_repetition_loops(h)),
            canonical_whitespace,
            normalizers=("echonova-v1",),
        ),
    )
}

_AUTO = {"echonova-v1": "sada-paper"}


def get_scoring(name: str) -> ScoringProtocol:
    try:
        return _REGISTRY[name]
    except KeyError:
        raise KeyError(f"unknown scoring protocol {name!r}; available: {', '.join(_REGISTRY)}") from None


def list_scorings() -> list[str]:
    return list(_REGISTRY)


def resolve_scoring(name: str, normalizer: str) -> ScoringProtocol:
    """Return the protocol to use; ``"auto"`` picks it from the normalizer."""
    protocol = get_scoring(_AUTO.get(normalizer, "none") if name == "auto" else name)
    if protocol.normalizers is not None and normalizer not in protocol.normalizers:
        raise ValueError(
            f"scoring protocol {protocol.name!r} is defined only with the normalizer(s) "
            f"{', '.join(protocol.normalizers)}, not {normalizer!r}"
        )
    return protocol
