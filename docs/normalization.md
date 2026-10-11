# Arabic text normalization

Arabic ASR scores depend heavily on normalization: whether hamza forms, ta
marbuta or punctuation count as errors can move WER by several points and
change rankings. This page documents exactly what each normalizer in
`arabic_asr_benchmark.normalization` does, quirks included. Every normalizer is
applied identically to references and hypotheses, and the unnormalized text
remains available in the dataset (`text`) and in the published predictions.

| Name | Status | Use it for |
| :--- | :--- | :--- |
| `echonova-v1` | Frozen. Default. | All EchoNova results; comparing with the paper. |
| `echonova-v1.1` | Frozen. Opt-in. | Analyses where the `echonova-v1` quirks below matter (especially CER). |
| `oual-2026-07` | Frozen. | Comparing with the Open Universal Arabic ASR Leaderboard as of July 2026. |
| `oual-2024-12` | Frozen. | Comparing with leaderboard figures computed before 27 July 2026. |
| `none` | | Inspecting raw error rates. |

A name never changes behaviour. Corrections get a new name.

## `echonova-v1`

The normalizer behind every private-test-set figure in the EchoNova Sada paper
(internally called `v2-ta`). It is a reproduction, not a redesign: it was
checked character by character against the original implementation on every
Unicode code point and on all 326,879 stored reference and hypothesis strings
of the paper's evaluation, with zero differences.

Rules, in order:

1. Delete these characters: ``! " # $ % & ' ( ) * + , - . / : ; < = > ? @ [ ] ^ _ ` { | } ~``
   and the Arabic comma ، semicolon ؛ and question mark ؟.
2. Delete the harakat U+064B-U+0652 (tanween, fatha, damma, kasra, shadda, sukun).
3. Fold پ→ب, ڤ→ف, آ→ا, أ→ا, إ→ا, ؤ→و, ئ→ي.
4. Delete standalone hamza ء.
5. Map Eastern Arabic digits ٠-٩ to 0-9.
6. Map every ta marbuta ة to ه.
7. Strip leading and trailing whitespace.

Every rule maps or deletes a single character and no rule's output feeds
another rule, so the order does not change the result.

**What it does not do** (these are properties of the paper's numbers, not
oversights in this reproduction):

- Punctuation is *deleted*, not replaced by a space: `3.5` becomes `35`,
  `10:30` becomes `1030`, and `كلمة-كلمة` becomes one word.
- Other punctuation is kept: « » … ٪ ۔ “ ” and the backslash.
- Inner whitespace is not collapsed. This does not affect WER (words are split
  on any whitespace) but double spaces count as characters in CER.
- Tatweel ـ, superscript alef (U+0670), other combining marks (U+0653-U+065F),
  alef wasla ٱ, Persian ک and ی, and Persian digits ۰-۹ are kept.
- Alef maqsura ى is not folded into ي.
- Latin text is not lowercased.
- Numbers are not converted between digits and words, so a system that writes
  `10` where the reference says `عشرة` is charged an error.
- Bracketed non-speech tags in references (for example `[موسيقى]`) lose their
  brackets and the word inside is scored. Three clips in the public test set
  contain such tags.

**Differences from the paper's description.** The paper describes the
normalizer in one sentence (Section 5.2). The code differs from that sentence in
three places: punctuation removal covers the fixed set above rather than all
punctuation; the "two Persian letters" are پ and ڤ (ڤ is used for /v/ in Arabic
and is not a Persian letter); and ta marbuta is folded everywhere, not only
word-finally. The last point changes no reported figure, because ة occurs
almost only word-finally (60 non-final occurrences in the private test set).

**Lossy transformations.** All rules are lossy. The hamza folds, the ة→ه fold and
punctuation deletion can merge distinct words. These merges are intended: they
remove spelling conventions on which annotators and systems legitimately
differ.

## `echonova-v1.1`

`echonova-v1` with corrections, for analyses where its quirks matter:

| Fix | Effect |
| :--- | :--- |
| `nfkc` | Unicode NFKC first (presentation forms, decomposed letters) |
| `event_tags` | Drop bracketed non-speech tags such as `[موسيقى]` |
| `punctuation` | Every Unicode punctuation or symbol character becomes a space |
| `marks` | Remove all combining marks, tatweel and format controls (RLM, ZWNJ, ...) |
| `extra_folds` | ٱ→ا, ک→ك, ی→ي |
| `persian_digits` | ۰-۹ → 0-9 |
| `lowercase` | Lowercase Latin |
| `whitespace` | Collapse whitespace runs |

It deliberately adds no new spelling policy: ى is still not folded and numbers
are not verbalized.

Effect on the public test set
([`results/echonova_20h/normalizer_ablation.csv`](../results/echonova_20h/normalizer_ablation.csv),
which also lists each fix's individual effect):

| System | WER v1 → v1.1 | CER v1 → v1.1 |
| :--- | :--- | :--- |
| Sada-ASR | 14.70 → 14.64 | 6.51 → 6.41 |
| MAI-Transcribe-2 | 16.51 → 16.45 | 8.40 → 7.88 |
| gpt-transcribe | 20.18 → 20.11 | 10.51 → 10.41 |
| Audar-ASR-V1-Turbo | 26.41 → 26.34 | 13.86 → 13.70 |
| FastConformer | 28.91 → 28.88 | 13.63 → 13.54 |
| Whisper large-v3 | 32.04 → 32.02 | 18.43 → 18.29 |
| Nemotron-3.5 | 33.20 → 33.16 | 14.78 → 14.70 |

WER moves by at most 0.07 points and no ranking changes. Almost all of the CER
change comes from whitespace: under `echonova-v1`, runs of spaces (including
those left where punctuation is deleted next to a space) count as characters.
MAI-Transcribe-2's CER changes most (8.40 → 7.88). The leave-one-out rows in the
ablation file are not additive: the `punctuation` fix creates extra spaces that
only the `whitespace` fix removes.

## Open Universal Arabic ASR Leaderboard: `oual-2024-12` and `oual-2026-07`

The [leaderboard's evaluation code](https://github.com/Natural-Language-Processing-Elm/open_universal_arabic_asr_leaderboard)
has changed once:

- **`oual-2024-12`** reproduces upstream commit `7185c3b` (10 December 2024).
  Its punctuation regular expression closes its character class early, so it
  never matches ordinary text and **no punctuation is removed**. Otherwise it
  removes harakat, applies the same hamza, پ/ڤ and digit folds as
  `echonova-v1`, and strips.
- **`oual-2026-07`** reproduces upstream commits `64b4732` and `8fce859`
  (27 July 2026). It removes the same punctuation as `echonova-v1` plus the
  backslash, attaches a standalone conjunction و to the following word
  (`قال و ذهب` → `قال وذهب`), and collapses whitespace.

Neither folds ة→ه. The upstream repository has no license, so these are
independent re-implementations of the documented behaviour. Their output was
checked against the upstream function at each commit on every Unicode code
point (in four contexts) and on 200,000 random strings, with zero differences.

Leaderboard entries computed before 27 July 2026 used the first version; the
leaderboard does not record which version produced each entry.

## Comparing protocols

| Input | `echonova-v1` | `echonova-v1.1` | `oual-2024-12` | `oual-2026-07` |
| :--- | :--- | :--- | :--- | :--- |
| `أَهلاً␣بِكُم␣في␣المَدرسةِ!` | `اهلا␣بكم␣في␣المدرسه` | `اهلا␣بكم␣في␣المدرسه` | `اهلا␣بكم␣في␣المدرسة!` | `اهلا␣بكم␣في␣المدرسة` |
| `قال:␣سأتصل␣بك␣غداً.` | `قال␣ساتصل␣بك␣غدا` | `قال␣ساتصل␣بك␣غدا` | `قال:␣ساتصل␣بك␣غدا.` | `قال␣ساتصل␣بك␣غدا` |
| `مسؤول␣قائم␣شيء` | `مسوول␣قايم␣شي` | `مسوول␣قايم␣شي` | `مسوول␣قايم␣شي` | `مسوول␣قايم␣شي` |
| `پيتزا␣ڤيديو` | `بيتزا␣فيديو` | `بيتزا␣فيديو` | `بيتزا␣فيديو` | `بيتزا␣فيديو` |
| `الساعة␣١٠:٣٠` | `الساعه␣1030` | `الساعه␣10␣30` | `الساعة␣10:30` | `الساعة␣1030` |
| `3.5␣كيلو` | `35␣كيلو` | `3␣5␣كيلو` | `3.5␣كيلو` | `35␣كيلو` |
| `كلمة-كلمة` | `كلمهكلمه` | `كلمه␣كلمه` | `كلمة-كلمة` | `كلمةكلمة` |
| `كتـــاب␣ٱلله` | `كتـــاب␣ٱلله` | `كتاب␣الله` | `كتـــاب␣ٱلله` | `كتـــاب␣ٱلله` |
| `ک␣ی␣۱۲` | `ک␣ی␣۱۲` | `ك␣ي␣12` | `ک␣ی␣۱۲` | `ک␣ی␣۱۲` |
| `على␣مستشفى` | `على␣مستشفى` | `على␣مستشفى` | `على␣مستشفى` | `على␣مستشفى` |
| `قال␣و␣ذهب` | `قال␣و␣ذهب` | `قال␣و␣ذهب` | `قال␣و␣ذهب` | `قال␣وذهب` |
| `>>␣[موسيقى]␣نعم` | `موسيقى␣نعم` | `نعم` | `>>␣[موسيقى]␣نعم` | `موسيقى␣نعم` |
| `نص␣␣بمسافتين` | `نص␣␣بمسافتين` | `نص␣بمسافتين` | `نص␣␣بمسافتين` | `نص␣بمسافتين` |
| `«مرحبا»␣…␣OK` | `«مرحبا»␣…␣OK` | `مرحبا␣ok` | `«مرحبا»␣…␣OK` | `«مرحبا»␣…␣OK` |

(␣ marks a space.) Reproduce any row with
`asr-bench normalize --normalizer <name> "<text>"`.

### Why ta marbuta matters

Whether a word-final feminine ending is written ة or ه is an annotation
convention, not something a recognizer can hear, and conventions differ between
dialect annotation teams and between systems. Normalizers that do not fold it
measure agreement with the annotators' convention. On the public test set the
effect is large for some dialects (WER, %):

| Dialect | Sada-ASR `echonova-v1` | Sada-ASR `oual-2026-07` | MAI-Transcribe-2 `echonova-v1` | MAI-Transcribe-2 `oual-2026-07` |
| :--- | ---: | ---: | ---: | ---: |
| MSA | 11.89 | 12.34 | 13.43 | 13.72 |
| Egyptian | 12.07 | 13.07 | 14.75 | 15.30 |
| Saudi | 17.82 | 21.31 | 21.12 | 21.70 |
| Emirati | 18.19 | 19.98 | 20.72 | 20.69 |
| Kuwaiti | 15.03 | 22.16 | 15.45 | 16.54 |
| Qatari | 15.34 | 24.22 | 16.84 | 16.96 |
| Syrian | 19.63 | 19.48 | 19.42 | 26.78 |
| Lebanese | 24.78 | 31.64 | 23.38 | 23.39 |
| Overall (micro) | 14.70 | 16.70 | 16.51 | 17.18 |
| Macro | 16.85 | 20.53 | 18.14 | 19.39 |

Under the leaderboard normalizer Sada-ASR's overall WER is still the lowest of
the seven systems, but its macro WER is higher than MAI-Transcribe-2's, driven
by Kuwaiti, Qatari and Lebanese, where its ta-marbuta convention differs from
the references. Never mix normalizers within one comparison table.

## Reproducing historical results

- Private-test-set figures in the paper (Tables 1-3, 5, 6): `echonova-v1`.
- Sada-ASR on the six leaderboard test sets: per set under `echonova-v1`
  (paper Table 4 rows, Table 7) and as an average under `oual-2026-07` (17.14).
- See [paper_consistency.md](paper_consistency.md) for the cell-by-cell check.
