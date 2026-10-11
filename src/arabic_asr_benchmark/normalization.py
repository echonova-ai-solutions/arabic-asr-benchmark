"""Arabic text normalizers for ASR scoring.

Every normalizer is applied identically to references and hypotheses before
computing WER/CER. Normalizers are identified by a stable name; a name never
changes behaviour once released. See ``docs/normalization.md`` for the full rule
listing, examples and the differences between protocols.

Registered normalizers
----------------------
``echonova-v1``
    The normalizer used for every private-test-set figure in the EchoNova Sada
    paper (internally called ``v2-ta``). Reproduced bit-exactly, quirks included.
``echonova-v1.1``
    Opt-in corrections to ``echonova-v1`` (whitespace, tatweel, full punctuation
    and diacritic coverage, ...). Not used for any headline figure.
``oual-2024-12``
    Open Universal Arabic ASR Leaderboard normalizer as of its first commit
    (7185c3b, 2024-12-10). Its punctuation regex never matches, so punctuation is
    kept.
``oual-2026-07``
    The same normalizer after upstream commits 64b4732 and 8fce859 (2026-07-27):
    punctuation removed, the conjunction و attached to the next word, whitespace
    collapsed.
``none``
    Identity.

The leaderboard normalizers are independent re-implementations of the upstream
behaviour (the upstream repository carries no license); equivalence with the
upstream code is verified by EchoNova on every code point and on the
leaderboard evaluation data.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass, field

__all__ = ["Normalizer", "get_normalizer", "list_normalizers", "normalize"]


@dataclass(frozen=True)
class Normalizer:
    """A named, versioned text normalizer."""

    name: str
    description: str
    fn: Callable[[str], str] = field(repr=False)

    def __call__(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError(f"normalizer {self.name!r} expects str, got {type(text).__name__}")
        return self.fn(text)


# --------------------------------------------------------------------------- #
# Shared character sets
# --------------------------------------------------------------------------- #

# ASCII punctuation as listed by the original rules. Note: no backslash.
_ASCII_PUNCT = "!\"#$%&'()*+,-./:;<=>?@[]^_`{|}~"
_ARABIC_PUNCT = "\u060c\u061b\u061f"  # ، ؛ ؟
_HARAKAT = [chr(c) for c in range(0x064B, 0x0653)]  # fathatan .. sukun
_HAMZA_FOLDS = {
    "\u067e": "\u0628",  # پ -> ب
    "\u06a4": "\u0641",  # ڤ -> ف
    "\u0622": "\u0627",  # آ -> ا
    "\u0623": "\u0627",  # أ -> ا
    "\u0625": "\u0627",  # إ -> ا
    "\u0624": "\u0648",  # ؤ -> و
    "\u0626": "\u064a",  # ئ -> ي
}
_HAMZA = "\u0621"  # ء (deleted)
_EASTERN_DIGITS = {chr(0x0660 + i): str(i) for i in range(10)}  # ٠-٩
_PERSIAN_DIGITS = {chr(0x06F0 + i): str(i) for i in range(10)}  # ۰-۹
_TA_MARBUTA, _HA = "\u0629", "\u0647"


def _table(delete: str | list[str], mapping: dict[str, str]) -> dict[int, object]:
    table: dict[int, object] = {ord(c): None for c in delete}
    table.update({ord(k): v for k, v in mapping.items()})
    return table


# --------------------------------------------------------------------------- #
# echonova-v1 (paper normalizer)
# --------------------------------------------------------------------------- #

# Every rule maps or deletes a single character and no rule's output is another
# rule's input, so the ordered rule list is exactly one translation table.
_ECHONOVA_V1_TABLE = _table(
    list(_ASCII_PUNCT + _ARABIC_PUNCT) + _HARAKAT + [_HAMZA],
    {**_HAMZA_FOLDS, **_EASTERN_DIGITS, _TA_MARBUTA: _HA},
)


def _echonova_v1(text: str) -> str:
    return text.translate(_ECHONOVA_V1_TABLE).strip()


# --------------------------------------------------------------------------- #
# Open Universal Arabic ASR Leaderboard
# --------------------------------------------------------------------------- #

_OUAL_COMMON_TABLE = _table(_HARAKAT + [_HAMZA], {**_HAMZA_FOLDS, **_EASTERN_DIGITS})
# The 2024-12 punctuation pattern closes its character class early and contains
# a bare ``|``; the only text it can ever match is this literal sequence.
_OUAL_2024_PUNCT_LITERAL = "}~\u060c\u061b\u061f]"
_OUAL_2026_PUNCT_TABLE = _table(list(_ASCII_PUNCT + "\\" + _ARABIC_PUNCT), {})
_WAW_ATTACH_RE = re.compile(r"(^|\s)\u0648\s+")
_WS_RE = re.compile(r"\s+")


def _oual_2024_12(text: str) -> str:
    text = text.replace(_OUAL_2024_PUNCT_LITERAL, "")
    return text.translate(_OUAL_COMMON_TABLE).strip()


def _oual_2026_07(text: str) -> str:
    text = text.translate(_OUAL_2026_PUNCT_TABLE).translate(_OUAL_COMMON_TABLE)
    text = _WAW_ATTACH_RE.sub("\\1\u0648", text)
    return _WS_RE.sub(" ", text).strip()


# --------------------------------------------------------------------------- #
# echonova-v1.1 (opt-in corrections)
# --------------------------------------------------------------------------- #

_EVENT_TAG_RE = re.compile(r"\[[^\[\]]*\]")
_TATWEEL = "\u0640"
_EXTRA_FOLDS = {
    "\u0671": "\u0627",  # ٱ -> ا
    "\u06a9": "\u0643",  # ک -> ك
    "\u06cc": "\u064a",  # ی -> ي
}
_V1_PUNCT = set(_ASCII_PUNCT + _ARABIC_PUNCT)
_V1_HARAKAT = set(_HARAKAT)

#: The individual corrections that ``echonova-v1.1`` makes on top of ``echonova-v1``.
V11_FIXES = (
    "nfkc",  # Unicode NFKC (presentation forms, decomposed letters)
    "event_tags",  # drop bracketed non-speech tags such as [موسيقى]
    "punctuation",  # every punctuation/symbol character becomes a space (v1 deletes a fixed set)
    "marks",  # remove all combining marks, tatweel and format controls (v1: harakat only)
    "extra_folds",  # ٱ -> ا, ک -> ك, ی -> ي
    "persian_digits",  # ۰-۹ -> 0-9
    "lowercase",  # Latin lowercase
    "whitespace",  # collapse whitespace runs (v1 keeps inner runs, which CER counts)
)


def make_echonova_v1_1(disabled: frozenset[str] = frozenset()) -> Callable[[str], str]:
    """Build ``echonova-v1.1``, optionally with some fixes switched back to v1 behaviour.

    Used to measure each fix's effect; only the full normalizer is registered.
    """
    unknown = set(disabled) - set(V11_FIXES)
    if unknown:
        raise ValueError(f"unknown v1.1 fixes: {sorted(unknown)}")
    on = {f: f not in disabled for f in V11_FIXES}
    folds = {**_HAMZA_FOLDS, _TA_MARBUTA: _HA, **_EASTERN_DIGITS}
    if on["extra_folds"]:
        folds.update(_EXTRA_FOLDS)
    if on["persian_digits"]:
        folds.update(_PERSIAN_DIGITS)
    cache: dict[str, str] = {}

    def char(c: str) -> str:
        if c in folds:
            return folds[c]
        if c == _HAMZA:
            return ""
        cat = unicodedata.category(c)
        if on["marks"]:
            if c == _TATWEEL or cat in ("Mn", "Cf"):
                return ""
        elif c in _V1_HARAKAT:
            return ""
        if on["punctuation"]:
            if cat[0] in "PS":
                return " "
        elif c in _V1_PUNCT:
            return ""
        return c

    def normalize_v11(text: str) -> str:
        if on["nfkc"]:
            text = unicodedata.normalize("NFKC", text)
        if on["event_tags"]:
            text = _EVENT_TAG_RE.sub(" ", text)
        out = []
        for c in text:
            m = cache.get(c)
            if m is None:
                m = cache[c] = char(c)
            out.append(m)
        text = "".join(out)
        if on["lowercase"]:
            text = text.lower()
        if on["whitespace"]:
            text = _WS_RE.sub(" ", text)
        return text.strip()

    return normalize_v11


_echonova_v1_1 = make_echonova_v1_1()


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #

_REGISTRY: dict[str, Normalizer] = {
    n.name: n
    for n in (
        Normalizer(
            "echonova-v1",
            "EchoNova paper normalizer (internal 'v2-ta'): delete ASCII punctuation and ، ؛ ؟, "
            "delete harakat U+064B-0652, fold آأإ->ا ؤ->و ئ->ي پ->ب ڤ->ف, delete ء, "
            "Eastern Arabic digits -> 0-9, ة->ه, strip.",
            _echonova_v1,
        ),
        Normalizer(
            "echonova-v1.1",
            "echonova-v1 with corrections: NFKC, drop [event] tags, all punctuation/symbols -> space, "
            "remove all combining marks, tatweel and format controls, also fold ٱ ک ی and Persian "
            "digits, lowercase, collapse whitespace.",
            _echonova_v1_1,
        ),
        Normalizer(
            "oual-2024-12",
            "Open Universal Arabic ASR Leaderboard normalizer at upstream 7185c3b (2024-12-10).",
            _oual_2024_12,
        ),
        Normalizer(
            "oual-2026-07",
            "Open Universal Arabic ASR Leaderboard normalizer at upstream 8fce859 (2026-07-27).",
            _oual_2026_07,
        ),
        Normalizer("none", "Identity (no normalization).", lambda s: s),
    )
}


def get_normalizer(name: str) -> Normalizer:
    """Return the normalizer registered under ``name``."""
    try:
        return _REGISTRY[name]
    except KeyError:
        raise KeyError(f"unknown normalizer {name!r}; available: {', '.join(_REGISTRY)}") from None


def list_normalizers() -> list[str]:
    return list(_REGISTRY)


def normalize(text: str, name: str = "echonova-v1") -> str:
    return get_normalizer(name)(text)
