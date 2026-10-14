# Paper consistency review

Every number in the paper *EchoNova Sada: A Benchmark Study of Dialectal Arabic
Speech Recognition* <!-- TODO: link to the published paper --> that can be
computed from the release was recomputed with this package and compared with the
paper at the paper's precision.

- **Private test set (Tables 1-3 and 5, §5.1-5.3):** recomputed from the systems'
  stored raw outputs on all 53,597 clips with the normalizer `echonova-v1` and the
  scoring protocol `sada-paper`. These figures can be recomputed only by EchoNova,
  since five sixths of the test set are unreleased; the released sixth and its
  results are in [`results/echonova_20h/`](../results/echonova_20h/).
- **Public test sets (Tables 4 and 6, §5.5):** recomputed from Sada-ASR's outputs
  with `oual-2026-07`, the leaderboard's current evaluation code.

## Summary

| Paper item | Values checked | Match | Mismatch |
| :--- | ---: | ---: | ---: |
| Table 1: hours, clips and mean clip length per variety, and totals | 30 | 30 | 0 |
| §5.1: MSA share of the audio (41.6%), number of source recordings (14,686) | 2 | 2 | 0 |
| Table 2: WER, macro WER, CER and empty rate, 8 systems | 32 | 32 | 0 |
| Table 3: WER by variety, 8 systems × 9 varieties, and the Δ MAI-2 point estimates | 81 | 81 | 0 |
| Table 5: CER by variety, 4 systems × 9 varieties | 36 | 36 | 0 |
| §5.3: overall margin (1.83), relative reduction (13.5%), Omani relative margin (21.1%), dialect-to-MSA ratios (2.99, 2.61), empty and runaway counts | 9 | 9 | 0 |
| Table 4 and Table 6: Sada-ASR per public test set and average | 14 | 14 | 0 |
| §5.5: number of public-test-set clips (46,757) | 1 | 1 | 0 |
| **Total** | **205** | **205** | **0** |

## Not recomputed by this package

These figures come from EchoNova's evaluation analyses and depend on procedures
outside the package. They are neither confirmed nor contradicted here.

| Paper item | Figures |
| :--- | :--- |
| Table 3 and §5.3 | The 95% confidence intervals. The paper resamples source recordings with its own grouping and draw order; `asr-bench compare --unit recording` uses the dataset's `recording_id`, so its intervals can differ in the second decimal and are reported as the package's own. |
| Table 3, §5.3 | The Δ ctrl. column and the margins on clips without number and Latin-script conventions (0.74, and 0.49 with hesitation fillers removed). |
| §5.3 | The share of MAI-Transcribe-2 clips with digits the reference lacks (9.23%). |
| §5.4 | The Lebanese and Syrian error analysis (substitution shares, filler counts). |
| §5.2 | The 48-clip locale check for MAI-Transcribe-2. |

## Notes

- The paper describes ta-marbuta folding as word-final; `echonova-v1` folds every
  ة, as did the scoring behind the paper. No reported figure depends on the
  difference.
- The paper's WER and CER include the two scoring rules of `sada-paper` (loop
  crop and whitespace canonicalization, §5.2). Scoring the same outputs with
  `--scoring none` gives higher WER for Gemini 3.5 Transcribe and Whisper
  large-v3, whose outputs contain runaway repetition loops, and slightly higher
  CER for every system.
