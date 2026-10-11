import pytest

from arabic_asr_benchmark.normalization import get_normalizer, list_normalizers, normalize

V1 = get_normalizer("echonova-v1")
V11 = get_normalizer("echonova-v1.1")
OUAL24 = get_normalizer("oual-2024-12")
OUAL26 = get_normalizer("oual-2026-07")


def test_registry():
    assert list_normalizers() == ["echonova-v1", "echonova-v1.1", "oual-2024-12", "oual-2026-07", "none"]
    with pytest.raises(KeyError):
        get_normalizer("nope")
    with pytest.raises(TypeError):
        V1(None)


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("", ""),
        ("مَرْحَبًا", "مرحبا"),  # harakat U+064B-0652 removed
        ("أحمد إلى آخر", "احمد الى اخر"),  # hamza/madda alef -> bare alef; ى kept
        ("مسؤول قائم", "مسوول قايم"),  # ؤ -> و, ئ -> ي
        ("شيء سماء", "شي سما"),  # standalone hamza deleted
        ("پيتزا ڤيديو", "بيتزا فيديو"),
        ("رقم ١٢٣٤٥٦٧٨٩٠", "رقم 1234567890"),
        ("مدرسة جميلة", "مدرسه جميله"),  # every ة -> ه
        ("نعم، شكرا. هل؟ نعم؛", "نعم شكرا هل نعم"),
        ("كلمة-كلمة 3.5 10:30", "كلمهكلمه 35 1030"),  # punctuation deleted without a space
        ("  نص  مع   مسافات  ", "نص  مع   مسافات"),  # inner whitespace NOT collapsed
        ("كتـــاب", "كتـــاب"),  # tatweel kept
        ("ٱلله", "ٱلله"),  # alef wasla kept
        ("ک ی ۱۲", "ک ی ۱۲"),  # Persian kaf/yeh and Persian digits kept
        ("a\\b", "a\\b"),  # backslash is not in the punctuation set
        ("Hello WORLD", "Hello WORLD"),  # Latin case kept
        ("«نص»", "«نص»"),  # guillemets not in the punctuation set
        (">> [موسيقى]", "موسيقى"),
    ],
)
def test_echonova_v1(raw, expected):
    assert V1(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("كتـــاب", "كتاب"),
        ("ٱلله", "الله"),
        ("ک ی ۱۲", "ك ي 12"),
        ("كلمة-كلمة 3.5", "كلمه كلمه 3 5"),
        ("  نص  مع   مسافات  ", "نص مع مسافات"),
        ("Hello WORLD", "hello world"),
        ("«نص» … ٪", "نص"),
        ("[موسيقى] اهلا >> نعم", "اهلا نعم"),
        ("أ", "ا"),  # decomposed alef + hamza above
        ("مرحبا‌بكم‏", "مرحبابكم"),  # format controls removed
        ("ﻻ", "لا"),  # presentation form via NFKC
        ("على", "على"),  # alef maqsura deliberately not folded
    ],
)
def test_echonova_v1_1(raw, expected):
    assert V11(raw) == expected


def test_oual_2024_keeps_punctuation():
    # The first upstream version's punctuation pattern never matches ordinary text.
    assert OUAL24("نعم، شكرا.") == "نعم، شكرا."
    assert OUAL24("أحمد ١") == "احمد 1"
    assert OUAL24("x}~،؛؟]y") == "xy"
    assert OUAL24("مدرسة") == "مدرسة"  # no ta-marbuta folding


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("نعم، شكرا.", "نعم شكرا"),
        ("a\\b", "ab"),
        ("قال و ذهب", "قال وذهب"),
        ("و ذهب", "وذهب"),
        ("و و ذهب", "وو ذهب"),
        ("  كثير   من\tالناس ", "كثير من الناس"),
        ("مدرسة", "مدرسة"),
    ],
)
def test_oual_2026_07(raw, expected):
    assert OUAL26(raw) == expected


def test_normalize_helper_and_identity():
    assert normalize("أ") == "ا"
    assert normalize(" x ", "none") == " x "


@pytest.mark.parametrize("name", ["echonova-v1", "echonova-v1.1", "oual-2024-12", "oual-2026-07"])
def test_idempotent(name):
    n = get_normalizer(name)
    for s in ["أحمدُ، و  مدرسةٌ ١٢ «x»", "كتـاب ٱلله ک", "[ضحك] Hello"]:
        assert n(n(s)) == n(s)


def test_v11_with_every_fix_disabled_equals_v1_on_simple_text():
    from arabic_asr_benchmark.normalization import V11_FIXES, make_echonova_v1_1

    off = make_echonova_v1_1(frozenset(V11_FIXES))
    for s in ["أحمدُ، مدرسةٌ ١٢", "كتـاب ٱلله", "نعم؛ شكرا!", "  a  b "]:
        assert off(s) == V1(s)
    import pytest as _pytest

    with _pytest.raises(ValueError):
        make_echonova_v1_1(frozenset({"bogus"}))
