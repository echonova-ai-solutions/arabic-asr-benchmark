# Arabic text normalization and scoring

Arabic ASR scores depend heavily on normalization: whether hamza forms, ta
marbuta or punctuation count as errors can move WER by several points and
change rankings. This page documents exactly what each normalizer in
`arabic_asr_benchmark.normalization` and each scoring protocol in
`arabic_asr_benchmark.scoring` does, quirks included. Every normalizer is applied
identically to references and hypotheses, and the unnormalized text remains
available in the dataset (`text`) and in the published predictions.

| Name | Status | Use it for |
| :--- | :--- | :--- |
| `echonova-v1` | Frozen. Default. | All EchoNova results; comparing with the paper. |
| `echonova-v1.1` | Frozen. Opt-in. | Analyses where the `echonova-v1` quirks below matter. |
| `oual-2026-07` | Frozen. | Comparing with the Open Universal Arabic ASR Leaderboard as of July 2026. |
| `oual-2024-12` | Frozen. | Comparing with leaderboard figures computed before 27 July 2026. |
| `none` | | Inspecting raw error rates. |

A name never changes behaviour. Corrections get a new name.

## `echonova-v1`

The normalizer behind every private-test-set figure in the EchoNova Sada paper.
It was checked character by character against the implementation used for the
paper on every Unicode code point and on all 1,393,522 stored reference and
hypothesis strings of the paper's evaluation (13 systems × 53,597 clips), with
zero differences.

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
- Inner whitespace is not collapsed by the normalizer itself; the `sada-paper`
  scoring protocol does that (below).
- Tatweel ـ, superscript alef (U+0670), other combining marks (U+0653-U+065F),
  alef wasla ٱ, Persian ک and ی, and Persian digits ۰-۹ are kept.
- Alef maqsura ى is not folded into ي.
- Latin text is not lowercased.
- Numbers are not converted between digits and words, so a system that writes
  `10` where the reference says `عشرة` is charged an error.

**Ta marbuta everywhere.** The paper describes the fold as word-final; the
normalizer folds every ة, and the paper's figures were computed this way. In the
references of the private test set, 1,505 of 89,441 ة (1.7%) are not word-final.

**Lossy transformations.** All rules are lossy. The hamza folds, the ة→ه fold and
punctuation deletion can merge distinct words. These merges are intended: they
remove spelling conventions on which annotators and systems legitimately
differ.

## Scoring protocol `sada-paper`

Two steps applied after `echonova-v1`, identically to every system, as in the
paper (its §5.2). Stored predictions are never edited, and the reference is never
used to change a prediction.

1. **Loop crop, hypothesis only.** For n = 1, 2, 3 in turn, any n-word unit
   repeated more than 10 times back-to-back is cut to 10 copies; text without such
   a loop is returned unchanged. The longest real back-to-back repetition in any
   reference of the private test set is 7 (a stutter), so no correct transcript
   is altered. Runaway outputs are: on the full private test set the crop changes
   the WER of Gemini 3.5 Transcribe (19.95 → 16.13; 2 clips, one of them a 15,008-word
   output for a 13-word reference, a single word repeated 15,006 times) and Whisper large-v3 (28.94 → 26.57).
2. **Whitespace canonicalization, both sides.** Every whitespace run becomes one
   space, so CER counts characters, not layout (some systems separate phrases with
   line breaks; some references contain double spaces). WER is unaffected.

`asr-bench` uses `sada-paper` automatically with `echonova-v1` and plain scoring
(`none`) with every other normalizer; `--scoring` overrides this, and every
result records the protocol used. `sada-paper` cannot be combined with another
normalizer.

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
are not verbalized. It does not crop loops, so it is scored with the plain
protocol. Not used for any headline figure.

WER / CER (%) on the public test set
([`results/echonova_20h/normalizer_ablation.csv`](../results/echonova_20h/normalizer_ablation.csv),
which also lists each fix's individual effect):

| System | `echonova-v1`, plain | `echonova-v1` + `sada-paper` (headline) | `echonova-v1.1`, plain |
| :--- | :--- | :--- | :--- |
| Sada-ASR | 11.74 / 4.78 | 11.74 / 4.72 | 11.70 / 4.70 |
| MAI-Transcribe-2 | 13.79 / 6.97 | 13.79 / 6.52 | 13.75 / 6.49 |
| Gemini 3.5 Transcribe | 16.31 / 8.46 | 16.31 / 8.39 | 16.29 / 8.37 |
| gpt-transcribe | 17.11 / 8.67 | 17.11 / 8.61 | 17.08 / 8.59 |
| Audar-ASR-V1-Turbo | 21.01 / 10.28 | 21.01 / 10.09 | 20.99 / 10.07 |
| FastConformer | 26.32 / 12.48 | 26.31 / 12.42 | 26.30 / 12.41 |
| Whisper large-v3 | 28.93 / 16.80 | 26.82 / 15.17 | 28.91 / 16.73 |
| Nemotron-3.5 | 28.52 / 11.70 | 28.52 / 11.65 | 28.48 / 11.63 |

The corrections in `echonova-v1.1` move WER by at most 0.04 points; the loop crop
is what moves Whisper large-v3, whose outputs on 20 clips of this test set contain
runaway loops. The leave-one-out rows in the ablation file are not additive: the
`punctuation` fix creates extra spaces that only the `whitespace` fix removes.

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

The leaderboard's rows from before 27 July 2026 were not re-scored after the change,
and it does not record which version produced each entry.

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
convention, not something a recognizer can hear. The references of the private
test set follow no single convention: the share of word-final ة/ه written as ة,
before folding, is

| MSA | Egyptian | Saudi | Emirati | Kuwaiti | Qatari | Syrian | Lebanese | Omani |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 69.0% | 59.2% | 53.5% | 64.0% | 51.1% | 69.5% | 7.5% | 48.7% | 2.4% |

The two Levantine varieties disagree with each other (7.5% against 48.7%), which
points to the annotation teams rather than the dialects. Without the fold, WER
partly measures whether a system guessed each team's convention. Effect of the
fold on the full private test set (WER %, `sada-paper` scoring):

| System | Without the fold | `echonova-v1` | Change |
| :--- | ---: | ---: | ---: |
| Gemini 3.5 Transcribe | 18.90 | 16.13 | −2.77 |
| Sada-ASR | 14.06 | 11.69 | −2.37 |
| FastConformer | 26.85 | 25.97 | −0.88 |
| MAI-Transcribe-2 | 14.39 | 13.51 | −0.87 |
| Audar-ASR-V1-Turbo | 21.63 | 20.86 | −0.76 |
| gpt-transcribe | 17.78 | 17.03 | −0.75 |
| Whisper large-v3 | 27.25 | 26.57 | −0.69 |
| Nemotron-3.5 | 28.73 | 28.11 | −0.62 |

The leaderboard normalizers do not fold ta marbuta. On the public test set the
effect is large for some varieties (WER %; `echonova-v1` with `sada-paper`,
`oual-2026-07` with plain scoring as on the leaderboard):

| Variety | Sada-ASR `echonova-v1` | Sada-ASR `oual-2026-07` | MAI-Transcribe-2 `echonova-v1` | MAI-Transcribe-2 `oual-2026-07` |
| :--- | ---: | ---: | ---: | ---: |
| MSA | 5.54 | 6.65 | 7.18 | 7.28 |
| Egyptian | 9.60 | 10.18 | 13.81 | 14.09 |
| Saudi | 14.76 | 19.06 | 17.17 | 17.36 |
| Emirati | 18.83 | 21.46 | 20.89 | 20.71 |
| Kuwaiti | 14.94 | 21.40 | 15.70 | 16.14 |
| Qatari | 15.71 | 23.40 | 16.15 | 16.42 |
| Omani | 16.06 | 17.59 | 20.05 | 28.11 |
| Syrian | 19.48 | 19.98 | 19.92 | 25.65 |
| Lebanese | 25.07 | 30.12 | 22.74 | 23.18 |
| Overall (micro) | 11.74 | 13.91 | 13.79 | 14.49 |
| Macro | 15.56 | 18.87 | 17.07 | 18.77 |

Under the leaderboard normalizer Sada-ASR's overall WER is still the lowest of
the eight systems, but its macro WER is slightly higher than MAI-Transcribe-2's,
driven by Kuwaiti, Qatari, Saudi and Lebanese, whose references mostly write ة
where Sada-ASR writes ه. Never mix normalizers within one comparison table.

## Reproducing the paper's figures

- Private test set (paper Tables 1-3 and 5): `echonova-v1` with the `sada-paper`
  scoring (the default).
- Sada-ASR on the six leaderboard test sets (paper Tables 4 and 6): `oual-2026-07`,
  average 17.17%.
- See [paper_consistency.md](paper_consistency.md) for the cell-by-cell check.
