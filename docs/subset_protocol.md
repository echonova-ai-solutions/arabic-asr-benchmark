# Subset construction protocol (pre-registered)

This file fixes how the public 20-hour benchmark is drawn from EchoNova's
120-hour private Arabic test set. It was committed **before** any metric was
computed on any candidate subset and is not edited afterwards; results and
statistics are reported in [`dataset.md`](dataset.md).

## Source

The private test set used in the EchoNova Sada paper: 46,697 clips, 120.008
hours, nine varieties (MSA, Egyptian, Saudi, Emirati, Kuwaiti, Qatari, Syrian,
Lebanese, Omani). Omani references did not pass label verification and are
excluded from the paper's headline figures.

## Target

One sixth of every variety, by duration (about 20 hours in total). The eight
verified varieties form the `test` split; the Omani sixth is released separately
as the `omani_unverified` configuration and is never part of headline metrics.

## Audio

Every clip is decoded exactly as it was for the benchmarked systems: decoded and
resampled to 16 kHz mono, then written as 16-bit PCM (clip to [-1, 1], scale by
32767, truncate). The released audio is these samples, losslessly FLAC-encoded.
Durations below are measured on this audio.

## Eligibility (applied before sampling)

A clip is excluded if any of the following holds:

1. the audio fails to decode or is silent (all samples zero);
2. its decoded duration differs from its labelled segment length by more than
   0.5 s (truncated file);
3. its time span overlaps another clip cut from the same source recording
   (including the same segment labelled with two varieties);
4. its decoded audio is sample-identical to another clip's;
5. its reference contains a run of seven or more digits (possible phone or
   account number).

Eligibility never uses model outputs.

## Fold assignment

For each variety separately, including Omani:

1. Sort eligible clips by decoded duration (ties broken by a seeded hash of the
   internal clip id).
2. Cut the sorted list into consecutive blocks of six clips (the last block may
   be shorter).
3. Within each block, assign the clips to folds 0-5 by a seeded random
   permutation (a short last block fills a random subset of folds).

The six folds partition the eligible clips, each fold matches the variety's
duration distribution, and clips from each recording are spread at random across
folds.

- Seed: the first 8 bytes (big-endian) of `sha256("echonova-arabic-dialect-asr-benchmark/v1.0.0")`.
- Released fold: **0**.

## Post-selection human review

Clips of the released fold whose references match self-identification or
contact-detail patterns, plus a random 5% of each variety, are reviewed by the
data team for personal information and offensive content. A clip removed in
review is dropped, not replaced. The number of removed clips is reported.

## Identifiers

Public ids are `<dialect>_<5 digits>`, numbered in a seeded random order.
`recording_id` is an opaque per-recording label (`rec_<4 digits>`), assigned in
a seeded random order. Recording grouping comes from source file names and is
approximate.

## Representativeness check (reported, never used for selection)

After release, the WER of every benchmarked system is reported on all six folds,
so readers can see where the released fold falls. The fold is not re-drawn
whatever the outcome.

---

## Addendum: implementation erratum (appended 2026-10-11; rules above unchanged)

The first implementation of eligibility rule 3 grouped clips by the raw source
file name. Some source recordings appear under two names (a title and a
`<title>_<title>_concat_...` variant with the same absolute segment times), so
overlaps across the two names were missed. Twelve of these clips were already
excluded by rule 4 (identical audio); six were not.

This was found after fold 0 had been drawn and scored. To keep the draw fixed,
the folds were **not** re-drawn: the six clips are treated as ineligible and
dropped wherever they occur. None of them is in fold 0, so the released clips
are unchanged. The same correction merges the two name variants into one
`recording_id` (Egyptian: 1,229 recordings instead of 1,271 in the released
fold).
