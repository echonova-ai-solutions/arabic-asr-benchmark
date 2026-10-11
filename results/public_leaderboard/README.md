# Results: Open Universal Arabic ASR Leaderboard test sets

Sada-ASR on the six test sets of the
[Open Universal Arabic ASR Leaderboard](https://huggingface.co/spaces/elmresearchcenter/open_universal_arabic_asr_leaderboard)
(Wang, Alhmoud and Alqurishi, 2024): SADA, Common Voice 18.0, MASC (clean and
noisy test), Casablanca and MGB-2, 46,757 clips.

**Status: EchoNova-reproduced.** EchoNova ran Sada-ASR on the test sets and
scored it with the leaderboard's protocol (corpus-level WER/CER per set,
unweighted average over the six sets). This is not an official leaderboard
entry, and Sada-ASR's per-clip outputs are not published.

| File | Content |
| :--- | :--- |
| `results.csv` | Sada-ASR per test set and averaged, under `oual-2026-07` (the leaderboard's current normalizer, headline), `oual-2024-12` (its original normalizer) and `echonova-v1` |
| `published_baselines.csv` | Figures for other systems as published by their authors or by the leaderboard (not re-run by EchoNova), with sources |
| `evaluation_config.yaml` | Upstream commits, test-set sources and other protocol details |

## Caveats

- **Normalizer version.** The leaderboard's evaluation code changed on
  27 July 2026 (see [docs/normalization.md](../../docs/normalization.md)). The
  average is 17.14% under the current code and 33.07% under the original, which
  removes no punctuation. The leaderboard does not record which version produced
  each published entry, so comparisons with `published_baselines.csv` carry this
  uncertainty.
- **Common Voice audio.** The leaderboard's Common Voice 18.0 test manifest was
  used, with audio files read from the Common Voice 23.0 release.
- **Training-data overlap.** Sada-ASR's training data is not public. EchoNova is
  checking it for overlap with these public test sets, in particular MASC;
  <!-- TODO: state the outcome of the MASC overlap check before release. -->
- **Published figures** come from their authors' own runs at different dates
  and are reproduced here as published.

We thank the leaderboard's maintainers and the creators of the test sets.
