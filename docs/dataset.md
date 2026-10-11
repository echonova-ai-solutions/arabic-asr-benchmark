# The public test set

[`echonova-ai/arabic-dialect-asr-benchmark`](https://huggingface.co/datasets/echonova-ai/arabic-dialect-asr-benchmark)
is a one-sixth sample of the 120-hour private test set evaluated in the EchoNova
Sada paper. This page describes how it was drawn and what it contains. The
dataset card on Hugging Face has the field descriptions and usage examples.

## Contents

| Config | Clips | Hours | Varieties |
| :--- | ---: | ---: | :--- |
| `default` (split `test`) | 7,396 | 19.16 | MSA, Egyptian, Saudi, Emirati, Kuwaiti, Qatari, Syrian, Lebanese |
| `omani_unverified` (split `test`) | 381 | 0.83 | Omani (references failed label verification) |

| Dialect | Clips | Hours | Share of audio | Mean clip (s) | Recordings |
| :--- | ---: | ---: | ---: | ---: | ---: |
| MSA | 2,332 | 8.33 | 43.5% | 12.9 | 2,331 |
| Egyptian | 1,272 | 3.32 | 17.3% | 9.4 | 1,229 |
| Saudi | 1,001 | 1.67 | 8.7% | 6.0 | 550 |
| Emirati | 1,161 | 2.50 | 13.1% | 7.8 | 1,068 |
| Kuwaiti | 473 | 0.83 | 4.4% | 6.4 | 288 |
| Qatari | 381 | 0.83 | 4.3% | 7.9 | 23 |
| Syrian | 388 | 0.84 | 4.4% | 7.8 | 49 |
| Lebanese | 388 | 0.84 | 4.4% | 7.7 | 30 |

Each dialect contributes one sixth of its audio in the private test set, so the
proportions match the paper's test set (Table 1 there). Clips last 0.91 to 30.01
seconds.

## How it was drawn

The protocol was committed before any metric was computed on a candidate
subset: see [subset_protocol.md](subset_protocol.md), including the addendum
recording one implementation correction. In short:

1. **Audit.** All 46,697 clips of the private set were decoded exactly as for
   the benchmarked systems and checked.
2. **Eligibility.** 47 clips were excluded before the draw: 3 truncated files,
   28 clips overlapping another clip of the same recording, 12 clips whose
   audio was identical to another clip's, and 4 whose reference contains a run
   of seven or more digits (some clips match more than one rule). Six more
   overlapping clips were found afterwards (see the addendum); none was in the
   released fold.
3. **Folds.** Within each variety, clips were sorted by duration, cut into
   blocks of six and assigned to six folds by a seeded permutation. Fold 0 is
   released. The released fold is within 0.35% of one sixth of each variety's
   audio, and every fold within 0.53%.
4. **Identifiers.** Public ids and recording ids are assigned in seeded random
   order. They carry no information about the source.
5. **Review.** Clips of fold 0 whose references match self-identification or
   contact-detail patterns, plus a random 5% of each variety, are reviewed by
   EchoNova's data team before release. <!-- TODO: report the number of clips
   removed in review (if any) once the review is complete. -->

## Is the released fold representative?

WER (%) of the seven systems on each fold, `echonova-v1`, eight varieties
([`results/echonova_20h/folds.csv`](../results/echonova_20h/folds.csv)):

| System | Fold 0 (released) | Fold 1 | Fold 2 | Fold 3 | Fold 4 | Fold 5 |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| Sada-ASR | 14.70 | 14.87 | 14.64 | 14.85 | 14.96 | 14.67 |
| MAI-Transcribe-2 | 16.51 | 16.53 | 16.44 | 16.54 | 16.75 | 16.46 |
| gpt-transcribe | 20.18 | 20.58 | 20.31 | 20.35 | 20.65 | 20.31 |
| Audar-ASR-V1-Turbo | 26.41 | 26.59 | 26.68 | 26.56 | 26.51 | 26.56 |
| FastConformer | 28.91 | 29.29 | 29.17 | 28.97 | 29.52 | 29.04 |
| Whisper large-v3 | 32.04 | 32.28 | 31.96 | 33.27 | 35.65 | 32.41 |
| Nemotron-3.5 | 33.20 | 33.81 | 33.77 | 33.74 | 33.55 | 33.50 |

The ranking of the seven systems is the same in five of the six folds (Whisper
and Nemotron swap in fold 4). The released fold has the lowest WER of the six
for gpt-transcribe, Audar, FastConformer and Nemotron, and sits mid-range for
Sada-ASR and MAI-Transcribe-2, so it slightly flatters some external systems
relative to the full private set. Fold-to-fold spread is 0.3-0.6 points for six
systems; Whisper large-v3 varies more (3.7 points), consistent with occasional
runaway outputs on a few clips.

## Audio

Every clip is the exact 16 kHz signal the benchmarked systems received: the
source file was decoded, downmixed to mono, resampled to 16 kHz and written as
16-bit PCM (clip to [-1, 1], scale by 32767, truncate), then FLAC-encoded
losslessly. Each FLAC file was decoded back and compared sample by sample
before release. 2,829 of the 7,396 clips of the `default` config were originally 22.05 kHz
and the rest 16 kHz (`original_sampling_rate`).

## Transcripts

The `text` field is the verbatim reference used in the paper, unchanged. See the
dataset card for transcription conventions (diacritics, Latin script, digits,
speaker-change markers and non-speech tags) and their frequencies.

## What stays private

The other five folds (about 100 hours) remain unreleased. They are kept as a
held-out set that cannot have leaked into any system's training data. Note that
the public and private parts were split at the clip level, so they share source
recordings.
