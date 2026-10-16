# Paper consistency review

Every number in the paper *Sada-ASR: A Production Multidialectal Arabic Speech
Recognition System* <!-- TODO: link to the published paper --> that can be
computed from the release was recomputed with this package and compared with the
paper at the paper's precision.

- **Private test set (Tables 1-3, 5 and 7, §6.1-6.3, §7):** recomputed from the
  twelve systems' stored raw outputs on all 53,597 clips with the normalizer
  `echonova-v1` and the scoring protocol `sada-paper`. These figures can be
  recomputed only by EchoNova, since five sixths of the test set are unreleased;
  the released sixth and its results are in
  [`results/echonova_20h/`](../results/echonova_20h/).
- **Public test sets (Tables 4 and 8, §6.4):** Sada-ASR's figures recomputed from
  its outputs with `oual-2026-07`, the leaderboard's current evaluation code; the
  other rows of Table 4 compared with
  [`published_baselines.csv`](../results/public_leaderboard/published_baselines.csv)
  and its sources.

## Summary

| Paper item | Values checked | Match | Mismatch |
| :--- | ---: | ---: | ---: |
| Table 1: hours, clips and mean clip length per variety and in total; hours and clips of the released subset | 50 | 50 | 0 |
| §6.1: MSA share of the audio (41.6%), number of source recordings (14,686) | 2 | 2 | 0 |
| Table 2: WER, macro WER, CER and empty rate, 12 systems | 48 | 48 | 0 |
| Table 3: WER by variety, 12 systems × 9 varieties, and the Δ MAI-2 point estimates | 117 | 117 | 0 |
| Table 7: CER by variety, 12 systems × 9 varieties | 108 | 108 | 0 |
| §6.2: WER before and after the loop crop for the four systems it changes, and that it changes exactly four | 9 | 9 | 0 |
| §6.3: overall margin (1.83), relative reduction (13.5%), Omani relative margin (21.1%), dialect-to-MSA ratios (2.99, 2.61), Syrian CER difference (+0.03), varieties where Sada-ASR is lowest (7 by WER, 9 by CER), MAI-Transcribe-2 clips with digits the reference lacks (9.23%, none for Sada-ASR), empty and runaway counts | 14 | 14 | 0 |
| Table 5: substitution, deletion and insertion shares, WER and CER on Lebanese and Syrian | 20 | 20 | 0 |
| §7: Lebanese source recordings (71) and those where Sada-ASR makes more errors (55) | 2 | 2 | 0 |
| Table 4 and Table 8: Sada-ASR per public test set and average, WER and CER | 21 | 21 | 0 |
| Table 4: published figures for the other systems, against `published_baselines.csv` | 162 | 162 | 0 |
| §6.4: number of public-test-set clips (46,757) | 1 | 1 | 0 |
| **Total** | **554** | **554** | **0** |

## Not recomputed by this package

These figures come from EchoNova's evaluation analyses and depend on procedures
outside the package. They are neither confirmed nor contradicted here.

| Paper item | Figures |
| :--- | :--- |
| Table 3 and §6.3 | The 95% confidence intervals, including the Syrian CER interval. The paper resamples source recordings with its own grouping and draw order; `asr-bench compare --unit recording` uses the dataset's `recording_id`, so its intervals can differ in the second decimal and are reported as the package's own. |
| Table 3, §6.3 | The Δ ctrl. column and the margins on clips without number and Latin-script conventions (0.74, and 0.49 with hesitation fillers removed). |
| §7, Table 6 | The decomposition of the Lebanese and Syrian gaps (1.18, 0.88, 1.35, 1.46, 2.50 and 0.51 points) and the substitution counts. |
| §6.2 | The 48-clip locale check for MAI-Transcribe-2. |

## Notes

- The paper describes ta-marbuta folding as word-final; `echonova-v1` folds every
  ة, as did the scoring behind the paper. No reported figure depends on the
  difference.
- The paper's WER and CER include the two scoring rules of `sada-paper` (loop
  crop and whitespace canonicalization, §6.2). Scoring the same outputs with
  `--scoring none` gives higher WER for the systems whose outputs contain runaway
  repetition loops and slightly higher CER for every system.
- Per-clip outputs are published for nine of the twelve systems. The figures of
  ElevenLabs Scribe v2, Speechmatics Enhanced and Cohere Transcribe Arabic were
  recomputed by EchoNova from their stored outputs in the same way, but cannot be
  recomputed by others.
