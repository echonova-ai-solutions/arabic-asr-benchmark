# Subset construction protocol, test set v2 (pre-registered)

This file fixes how the public benchmark is drawn from version 2 of EchoNova's
120-hour private Arabic test set. It replaces the protocol for version 1
([subset_protocol.md](https://github.com/echonova-ai-solutions/arabic-asr-benchmark/blob/09ea774/docs/subset_protocol.md)), whose test set has been retired. It was
committed **before** any metric was computed on any candidate subset of version 2
and is not edited afterwards. (Some systems had already been run on the full
version 2 set when this was written; no metric on any subset had been computed and
model outputs play no part in the selection.)

## Source

Private test set version 2 (`testset_120h_final`, frozen 2026-10-12): 53,597 clips,
119.86 hours, nine varieties: MSA, Egyptian, Saudi, Emirati, Kuwaiti, Qatari,
Syrian, Lebanese and Omani. The reference of a clip is its human transcript,
except where a listening review judged the stored automatic transcript to be the
correct one (24 clips), exactly as the benchmark scores it.

## Target

One sixth of every variety, by duration (about 20 hours in total). All nine
varieties form the single `test` split.

## Audio

Every clip is decoded exactly as it is for the benchmarked systems: decoded and
resampled to 16 kHz mono, then written as 16-bit PCM (clip to [-1, 1], scale by
32767, truncate). The released audio is these samples, losslessly FLAC-encoded.
Durations below are measured on this audio.

## Eligibility (applied before sampling)

A clip is excluded if any of the following holds:

1. the audio fails to decode or is silent (all samples zero);
2. its decoded duration differs from its labelled duration by more than 0.5 s;
3. its time span overlaps another clip cut from the same source recording
   (recordings are identified by source file name, with known name variants
   merged);
4. its decoded audio is sample-identical to another clip's;
5. its reference contains a run of seven or more digits (possible phone or
   account number);
6. a listening review judged both the human and the automatic transcript wrong.

Eligibility never uses model outputs, decoding statistics of any model, or the
dialect classifier's output.

## Fold assignment

For each variety separately:

1. Sort eligible clips by decoded duration (ties broken by a seeded hash of the
   internal clip id).
2. Cut the sorted list into consecutive blocks of six clips (the last block may
   be shorter).
3. Within each block, assign the clips to folds 0-5 by a seeded random
   permutation (a short last block fills a random subset of folds).

- Seed: the first 8 bytes (big-endian) of `sha256("echonova-arabic-dialect-asr-benchmark/testset-v2")`.
- Released fold: **0**.

## Post-selection review

Clips of the released fold whose references match self-identification or
contact-detail patterns are reviewed for personal information and offensive
content. A clip removed in review is dropped, not replaced; the number is
reported. Transcripts are otherwise released unchanged: in this version the
Kuwaiti, Lebanese, Omani, Qatari and Syrian transcripts are single-pass
annotations, which the dataset card states.

## Identifiers

Public ids are `<dialect>_<5 digits>`, numbered in a seeded random order.
`recording_id` is an opaque per-recording label (`rec_<5 digits>`), assigned in
a seeded random order.

## Representativeness check (reported, never used for selection)

The WER of every published system is reported on all six folds, so readers can
see where the released fold falls. The fold is not re-drawn whatever the outcome.

---

## Addendum (appended 2026-10-14; rules above unchanged)

The version 1 protocol was removed from the repository when its test set was
retired. The link above now points to it as it stood when this protocol was
registered (commit `09ea774`); nothing else in this file was changed.
