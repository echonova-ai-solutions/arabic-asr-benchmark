# Paper consistency review

Every number reported for Sada-ASR and the six external systems in *EchoNova
Sada: A Benchmark Study of Dialectal Arabic Speech Recognition* (draft of
10 October 2026) was recomputed with this package from the systems' stored raw
outputs, and compared with the paper at the paper's precision (two decimals).
The private-set rows can only be recomputed by EchoNova; the public-test-set
results in this repository can be recomputed by anyone.

## Summary

| Paper item | Cells | Match | Mismatch | Not recomputed |
| :--- | ---: | ---: | ---: | ---: |
| Table 1: clips and hours per variety | 20 | 20 | 0 | 0 |
| Table 2: WER, macro WER, CER, empty rate (8 varieties) | 28 | 28 | 0 | 0 |
| Table 3: WER by variety, 7 systems | 56 | 56 | 0 | 0 |
| Table 3: Sada-ASR vs MAI-Transcribe-2 margin and 95% CI | 24 | 24 | 0 | 0 |
| Table 5: WER and CER with Omani (9 varieties) | 14 | 14 | 0 | 0 |
| Table 6: CER by variety, 3 systems | 24 | 24 | 0 | 0 |
| Table 4 / Table 7: Sada-ASR on the six public test sets (WER, CER, averages) | 15 | 15 | 0 | 0 |
| Section 5.5: number of public-test-set clips (46,757) | 1 | 1 | 0 | 0 |
| Section 5.3: overall margin over MAI-Transcribe-2 and its CI | 3 | 1 | 2 | 0 |
| Section 5.3: dialect-to-MSA WER ratios (1.47, 1.38) and Sada-ASR's 3 empty clips | 3 | 3 | 0 | 0 |
| Section 5.3: digit rate of MAI-Transcribe-2 and the two subset margins with CIs | 7 | | | 7 |
| Section 5.4: Lebanese error-analysis figures | 7 | | | 7 |
| **Total** | **202** | **186** | **2** | **14** |

The Table 3 confidence intervals reproduce exactly with
`arabic_asr_benchmark.bootstrap.compare_by_group` (clip level, one generator
seeded 0 consumed across the varieties in the paper's order, 2,000 resamples).

## Findings

1. **Overall CI in Section 5.3.** The paper gives a 95% CI of 1.65-1.86 for
   Sada-ASR's 1.76-point overall margin over MAI-Transcribe-2. That interval
   came from a different bootstrap script than Table 3; under this package's
   procedure it is 1.66-1.87. The margin itself matches. Recommended amendment:
   report 1.66-1.87 and state the procedure, or keep the original and name the
   procedure that produced it.
2. **Normalization description (Section 5.2).** The paper's one-sentence
   description differs from the implementation in three ways (see
   [normalization.md](normalization.md)): punctuation removal covers a fixed set
   (ASCII punctuation and ، ؛ ؟); the "two Persian letters" are پ and ڤ; and ta
   marbuta is folded everywhere, not only word-finally. No reported figure
   changes. Recommended amendment: describe the rules as in
   [normalization.md](normalization.md).
3. **Leaderboard normalizer version (Section 5.5).** The 17.14% average uses the
   leaderboard's evaluation code as of 27 July 2026 (`oual-2026-07`). Leaderboard
   entries computed before that date used the earlier version (`oual-2024-12`),
   which keeps punctuation and gives Sada-ASR an average of 33.07%. The
   leaderboard does not record which version produced each published entry, so
   comparisons with published rows carry this uncertainty. Recommended amendment:
   name the upstream commit.
4. **Common Voice audio.** The Common Voice 18.0 test manifest was used with
   audio files taken from the Common Voice 23.0 release. Clip files are shared
   across releases, but this was not checked byte for byte. Recommended
   amendment: state it.
5. **Released subset.** The paper says a subset of the test set will be
   released. That subset is the public test set (19.16 h plus 0.83 h of Omani).
   Results on it are close to the paper's but not identical (for example,
   Sada-ASR 14.70% vs 14.79% WER) and should be reported as a separate table.
   On the public test set, Sada-ASR's Kuwaiti margin over MAI-Transcribe-2
   (+0.42 points) has a confidence interval that includes zero; on the full
   private set it does not.

Items not recomputed (the Section 5.3 subset margins and the Section 5.4
percentages) depend on analysis scripts outside this package; they are neither
confirmed nor contradicted here.
