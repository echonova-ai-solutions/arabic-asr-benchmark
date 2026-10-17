# The public test set

[`echonova-ai/arabic-dialect-asr-benchmark`](https://huggingface.co/datasets/echonova-ai/arabic-dialect-asr-benchmark)
is a one-sixth sample of the 120-hour private test set evaluated in the Sada-ASR
paper (test set version 2). This page describes how it was drawn and what it
contains. The dataset card on Hugging Face has the field descriptions and usage
examples.

## Contents

One configuration (`default`) with one split (`test`): 8,925 clips, 19.95 hours,
nine varieties.

| Variety | Clips | Hours | Share of audio | Mean clip (s) | Recordings |
| :--- | ---: | ---: | ---: | ---: | ---: |
| MSA | 3,400 | 8.27 | 41.5% | 8.8 | 1,449 |
| Egyptian | 1,508 | 3.37 | 16.9% | 8.0 | 1,352 |
| Saudi | 916 | 1.67 | 8.4% | 6.6 | 236 |
| Emirati | 1,187 | 2.50 | 12.5% | 7.6 | 1,067 |
| Kuwaiti | 423 | 0.84 | 4.2% | 7.1 | 278 |
| Qatari | 396 | 0.83 | 4.2% | 7.6 | 41 |
| Syrian | 361 | 0.83 | 4.2% | 8.3 | 75 |
| Lebanese | 363 | 0.83 | 4.2% | 8.3 | 66 |
| Omani | 371 | 0.81 | 4.0% | 7.8 | 341 |
| **Total** | **8,925** | **19.95** | 100% | 8.0 | 4,902 |

Each variety contributes one sixth of its audio in the private test set, so the
proportions match the paper's test set (its Table 1). Clips last 2.50 to 28.74
seconds. Some recordings contribute clips to two varieties, so the per-variety
recording counts sum to more than the total.

## How it was drawn

The protocol was committed before any metric was computed on a candidate subset:
see [subset_protocol_v2.md](subset_protocol_v2.md). In short:

1. **Audit.** All 53,597 clips of the private test set were decoded exactly as for
   the benchmarked systems and checked: none failed to decode, was truncated or
   silent, or duplicated another clip's audio.
2. **Eligibility.** 55 clips were excluded before the draw: 53 MSA clips whose time
   span overlaps another clip of the same recording, and 2 clips (one MSA, one
   Lebanese) whose reference a listening review judged wrong. No reference
   contains a run of seven or more digits.
3. **Folds.** Within each variety, clips were sorted by duration, cut into blocks
   of six and assigned to six folds by a seeded permutation. Fold 0 is released.
   The released fold is within 0.3% of one sixth of each variety's audio, and every
   fold within 0.5%.
4. **Identifiers.** Public ids and recording ids are assigned in seeded random
   order and carry no information about the source.
5. **Review.** Clips whose references match self-identification or
   contact-detail patterns (29 in the released fold) were reviewed by EchoNova
   for personal information and offensive content before release. None was
   removed.

The full private-set results (`results/echonova_private_120h`) score all 53,597
clips, as the paper does; the 55 exclusions apply to the draw only.

## Is the released fold representative?

WER (%) of the twelve systems on each fold, `echonova-v1` with `sada-paper`
scoring ([`results/echonova_20h/folds.csv`](../results/echonova_20h/folds.csv)):

| System | Fold 0 (released) | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sada-ASR | 11.74 | 11.56 | 11.71 | 11.73 | 11.62 | 11.78 |
| MAI-Transcribe-2 | 13.79 | 13.34 | 13.55 | 13.47 | 13.52 | 13.43 |
| Gemini 3.5 Transcribe | 16.31 | 15.88 | 16.22 | 16.04 | 16.16 | 16.23 |
| ElevenLabs Scribe v2 | 16.35 | 16.00 | 16.09 | 16.10 | 16.08 | 16.14 |
| Jais-ASR | 16.52 | 16.26 | 16.37 | 16.44 | 16.34 | 16.55 |
| gpt-transcribe | 17.11 | 16.90 | 16.94 | 17.16 | 16.94 | 17.16 |
| Speechmatics Enhanced | 18.29 | 17.98 | 17.90 | 18.15 | 18.03 | 18.20 |
| Audar-ASR-V1-Turbo | 21.01 | 20.80 | 20.98 | 20.93 | 20.63 | 20.87 |
| FastConformer | 26.31 | 25.69 | 25.96 | 25.97 | 25.73 | 26.22 |
| Whisper large-v3 | 26.82 | 26.81 | 26.38 | 26.35 | 26.64 | 26.50 |
| Nemotron-3.5 | 28.52 | 28.00 | 28.00 | 28.05 | 27.86 | 28.28 |
| Cohere Transcribe Arabic | 29.53 | 28.90 | 28.93 | 29.17 | 28.63 | 29.61 |

The ranking of the twelve systems is the same in all six folds, except that
Gemini 3.5 Transcribe and ElevenLabs Scribe v2, within 0.15 points of each other,
swap places in three folds; a system's WER varies by 0.2-1.0 points between
folds. The released fold is slightly harder than the others: it has the highest
WER of the six for eight of the twelve systems,
so absolute error rates on it are slightly higher than on the full test set.

## Audio

Every clip is the exact 16 kHz signal the benchmarked systems received: the
source file (24 kHz for 8,823 clips, 16 kHz for 102) was decoded, downmixed to
mono, resampled to 16 kHz and written as 16-bit PCM (clip to [-1, 1], scale by
32767, truncate), then FLAC-encoded losslessly. Each FLAC file was decoded back and
compared sample by sample before release.

## Transcripts

The `text` field is the reference used in the paper, unchanged: the annotator's
transcript, or, for 4 clips of this test set, the automatic transcript that a
listening review judged correct. The MSA, Egyptian, Emirati and Saudi transcripts
were second-reviewed; almost all Kuwaiti, Lebanese, Omani, Qatari and Syrian
transcripts (1,910 clips) are single-pass annotations. The dataset card lists the
transcription conventions and their frequencies.

## What stays private

The other five folds (about 100 hours) remain unreleased. They are kept as a
held-out set that cannot have leaked into any system's training data. The public
and private parts were split at the clip level, so they share source recordings.
