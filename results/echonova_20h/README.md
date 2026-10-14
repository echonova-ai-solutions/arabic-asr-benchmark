# Results: public test set (`echonova_20h`)

The eight systems compared in the EchoNova Sada paper, on
[`echonova-ai/arabic-dialect-asr-benchmark`](https://huggingface.co/datasets/echonova-ai/arabic-dialect-asr-benchmark)
(8,925 clips, 19.95 h, 9 varieties). Every file here is generated from the
published predictions with the `asr-bench` CLI; see
[docs/reproducibility.md](../../docs/reproducibility.md).

| File | Content |
| :--- | :--- |
| `predictions/<system>.jsonl` | Raw per-clip output of each system (`{"id", "prediction"}`), exactly as returned, before any normalization or loop cropping |
| `systems.json` | Type, provider, model identifier, evaluation date, settings, and counts of failed requests and re-requested runaway outputs (`null` = not recorded) |
| `runs/<normalizer>/<system>.json` | Full result records: `echonova-v1` with the `sada-paper` scoring (headline), `echonova-v1.1` and `oual-2026-07` (both with plain scoring) |
| `summary.csv` | One row per system and normalizer: WER, macro WER, CER, S/D/I, empty rate |
| `per_dialect.csv` | One row per system, normalizer and variety |
| `bootstrap.csv` | Sada-ASR's WER margin over each system with 95% CIs, per variety and overall, recording- and clip-level (`echonova-v1`, `sada-paper`). These are the package's own intervals; the paper's come from a separate recording grouping and can differ in the second decimal |
| `folds.csv` | WER of every system on all six folds of the private test set (fold 0 is this test set), `sada-paper` scoring |
| `normalizer_ablation.csv` | `echonova-v1` with and without the `sada-paper` scoring, and the effect of each `echonova-v1.1` correction (leave-one-out) |

Rates in CSV and JSON files are fractions; multiply by 100 for %. In
`bootstrap.csv`, `delta_wer_points` is positive when Sada-ASR has the lower WER.

The outputs were produced on 13 October 2026 in the evaluation reported in the
paper; they were not re-run for this release. A runaway output (more than five
times the reference's word count and more than 50 words) from an API was
re-requested up to three times and the first normal output kept; `systems.json`
counts these. Systems benchmarked by EchoNova but not compared in the paper are
not included.
