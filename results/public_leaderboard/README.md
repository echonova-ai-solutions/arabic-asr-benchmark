# Results: Open Universal Arabic ASR Leaderboard test sets

Sada-ASR on the six test sets of the
[Open Universal Arabic ASR Leaderboard](https://huggingface.co/spaces/elmresearchcenter/open_universal_arabic_asr_leaderboard)
(Wang, Alhmoud and Alqurishi, Interspeech 2025): SADA, Common Voice 18.0, MASC
(clean and noisy test), Casablanca and MGB-2, 46,757 clips. Measured on
13-14 October 2026.

**Status: EchoNova-reproduced.** EchoNova ran Sada-ASR on the test sets and
scored it with the leaderboard's evaluation code (corpus-level WER/CER per set,
unweighted average over the six sets). This is not an official leaderboard
entry, and Sada-ASR's per-clip outputs on these sets are not published.

| File | Content |
| :--- | :--- |
| `results.csv` | Sada-ASR per test set and averaged, under `oual-2026-07` (the leaderboard's current code; headline), `oual-2024-12` (its original code) and `echonova-v1` with `sada-paper` scoring |
| `published_baselines.csv` | Figures for other systems as published by their authors or by the leaderboard (not re-run by EchoNova), with sources |
| `evaluation_config.yaml` | Upstream commits, test-set sources and other protocol details |

Under the leaderboard's current code, Sada-ASR's average WER is **17.17%**
(CER 7.05%).

## Caveats

- **Scorer version.** The leaderboard's evaluation code changed on 27 July 2026
  (upstream commits `64b4732` and `8fce859`; see
  [docs/normalization.md](../../docs/normalization.md)): before the change its
  punctuation pattern never matched, so punctuation stayed attached to words and
  counted as errors. The rows already on the leaderboard were not re-scored after
  the change. Sada-ASR's average is 17.17% under the current code and 33.10% under
  the original code; Sada-ASR punctuates almost every output, so the original code
  penalizes it heavily. It is not recorded which version produced each figure in
  `published_baselines.csv`, so comparisons with them are indicative, not
  established.
- **Common Voice audio.** The leaderboard's Common Voice 18.0 test manifest was
  used, with audio files read from the Common Voice 23.0 release.
- **MASC-noisy manifest.** It lists one clip id twice; like the leaderboard, all
  9,394 lines are scored.
- **Training-data overlap.** EchoNova's training team has stated that the model
  evaluated here saw none of these six test sets, in training or in checkpoint
  selection. An automated check of the training manifest against the test sets is
  pending. <!-- TODO: update when the manifest check has been run. -->
- **Published figures** come from their authors' own runs at different dates
  and are reproduced here as published.

We thank the leaderboard's maintainers and the creators of the test sets.
