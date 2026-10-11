# Results: public test set (`echonova_20h`)

Seven systems on [`echonova-ai/arabic-dialect-asr-benchmark`](https://huggingface.co/datasets/echonova-ai/arabic-dialect-asr-benchmark)
(`default` config: 7,396 clips, 19.16 h, 8 varieties). Every file here is
generated from the published predictions with the `asr-bench` CLI; see
[docs/reproducibility.md](../../docs/reproducibility.md).

| File | Content |
| :--- | :--- |
| `predictions/<system>.jsonl` | Raw per-clip output of each system (`{"id", "prediction"}`), before normalization |
| `predictions/omani_unverified/<system>.jsonl` | The same for the `omani_unverified` config |
| `systems.json` | Type, provider, model identifier, evaluation date and recorded settings of each system (`null` = not recorded) |
| `runs/<normalizer>/<system>.json` | Full result records under `echonova-v1` (headline), `echonova-v1.1` and `oual-2026-07` |
| `summary.csv` | One row per system and normalizer: WER, macro WER, CER, S/D/I, empty rate |
| `per_dialect.csv` | One row per system, normalizer and dialect |
| `bootstrap.csv` | Sada-ASR's WER margin over each system with 95% CIs, per dialect and overall, recording- and clip-level (`echonova-v1`) |
| `folds.csv` | WER of every system on all six folds of the private test set (fold 0 is this test set) |
| `normalizer_ablation.csv` | Effect of each `echonova-v1.1` correction (leave-one-out) |
| `runs_omani_unverified/`, `omani_unverified.csv` | Results on the Omani slice (unverified references; not a headline figure) |

Rates in CSV and JSON files are fractions; multiply by 100 for %. In
`bootstrap.csv`, `delta_wer_points` is positive when Sada-ASR has the lower WER.

The systems' outputs were produced in September 2026 during the evaluation
reported in the EchoNova Sada paper (MAI-Transcribe-2 on 2026-09-06, the other
external systems on 2026-09-03); they were not re-run for this release.
