# EchoNova Arabic ASR Benchmark

**Reproducible evaluation of Arabic speech recognition across MSA and seven dialects.**

This repository holds the evaluation code, normalizers, results and per-clip
system outputs behind EchoNova's Arabic speech recognition benchmark. It
accompanies the paper *EchoNova Sada: A Benchmark Study of Dialectal Arabic
Speech Recognition* and the public test set
[`echonova-ai/arabic-dialect-asr-benchmark`](https://huggingface.co/datasets/echonova-ai/arabic-dialect-asr-benchmark).

The evaluation works with any system's transcripts: you need a predictions
file, not access to any model, API key or EchoNova service.

## Overview

- **Public test set.** 19.16 hours (7,396 clips) of Modern Standard Arabic and
  Egyptian, Saudi, Emirati, Kuwaiti, Qatari, Syrian and Lebanese speech with
  verbatim transcripts: a one-sixth, duration-stratified sample of the 120-hour
  private test set used in the paper. An extra 0.83 hours of Omani speech with
  unverified transcripts is provided separately.
- **Seven systems** measured on it: EchoNova's Sada-ASR, two commercial APIs and
  four open-weight models. Their raw per-clip outputs are published, so every
  figure can be recomputed.
- **Versioned Arabic normalizers**, including a bit-exact reproduction of the
  paper's normalizer and of the Open Universal Arabic ASR Leaderboard's.
- **Paper results** on the full private set and on six public test sets,
  recomputed from stored outputs and labelled by how far they can be verified.

## Resources

| Resource | Link |
| :--- | :--- |
| Test set (Hugging Face) | [echonova-ai/arabic-dialect-asr-benchmark](https://huggingface.co/datasets/echonova-ai/arabic-dialect-asr-benchmark) |
| Paper | *EchoNova Sada: A Benchmark Study of Dialectal Arabic Speech Recognition* (Khaled, Abd-Elnaser and Mohsen, 2026), preprint forthcoming <!-- TODO: arXiv link --> |
| Open Universal Arabic ASR Leaderboard | [Hugging Face Space](https://huggingface.co/spaces/elmresearchcenter/open_universal_arabic_asr_leaderboard) · [code](https://github.com/Natural-Language-Processing-Elm/open_universal_arabic_asr_leaderboard) |
| Methodology | [docs/methodology.md](docs/methodology.md) |
| Normalization | [docs/normalization.md](docs/normalization.md) |
| Test set construction and statistics | [docs/dataset.md](docs/dataset.md) |
| Reproducing the results | [docs/reproducibility.md](docs/reproducibility.md) |
| Paper consistency review | [docs/paper_consistency.md](docs/paper_consistency.md) |

## Results

### Public test set (19.16 h, 8 varieties)

WER, macro WER and CER in %, normalizer `echonova-v1`. WER and CER are corpus
micro-averages; macro WER is the unweighted mean of the eight per-dialect WERs;
Empty is the share of clips with an empty transcript. Recomputed from each
system's stored outputs, which are published in
[`results/echonova_20h/predictions/`](results/echonova_20h/predictions/).
**Fully verifiable at the metric level.**

<!-- BEGIN echonova-20h-summary -->
| System | Type | WER | Macro WER | CER | Empty % |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Sada-ASR (EchoNova) | proprietary | 14.70 | 16.85 | 6.51 | 0.01 |
| Microsoft MAI-Transcribe-2 | commercial API | 16.51 | 18.14 | 8.40 | 0.05 |
| OpenAI gpt-transcribe | commercial API | 20.18 | 22.82 | 10.51 | 0.19 |
| Audar-ASR-V1-Turbo | open-weight | 26.41 | 29.88 | 13.86 | 0.00 |
| NVIDIA FastConformer (Arabic) | open-weight | 28.91 | 34.26 | 13.63 | 0.19 |
| OpenAI Whisper large-v3 | open-weight | 32.04 | 36.12 | 18.43 | 0.00 |
| NVIDIA Nemotron-3.5 ASR streaming 0.6B | open-weight | 33.20 | 37.17 | 14.78 | 1.55 |
<!-- END echonova-20h-summary -->

WER (%) by dialect (best per row in bold):

<!-- BEGIN echonova-20h-wer-by-dialect -->
| Dialect | Clips | Sada-ASR (EchoNova) | Microsoft MAI-Transcribe-2 | OpenAI gpt-transcribe | Audar-ASR-V1-Turbo | NVIDIA FastConformer (Arabic) | OpenAI Whisper large-v3 | NVIDIA Nemotron-3.5 ASR streaming 0.6B |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| msa | 2332 | **11.89** | 13.43 | 14.98 | 19.90 | 19.42 | 22.76 | 26.38 |
| egyptian | 1272 | **12.07** | 14.75 | 19.33 | 27.72 | 29.53 | 32.10 | 34.13 |
| saudi | 1001 | **17.82** | 21.12 | 24.48 | 28.43 | 34.45 | 40.06 | 37.25 |
| emirati | 1161 | **18.19** | 20.72 | 26.42 | 31.92 | 36.60 | 43.10 | 36.93 |
| kuwaiti | 473 | **15.03** | 15.45 | 20.29 | 31.26 | 37.12 | 31.10 | 35.46 |
| qatari | 381 | **15.34** | 16.84 | 20.99 | 26.79 | 34.49 | 33.53 | 33.09 |
| syrian | 388 | 19.63 | **19.42** | 26.08 | 33.97 | 39.84 | 43.14 | 44.30 |
| lebanese | 388 | 24.78 | **23.38** | 30.03 | 39.07 | 42.64 | 43.13 | 49.80 |
<!-- END echonova-20h-wer-by-dialect -->

The Kuwaiti, Qatari, Syrian and Lebanese slices hold under an hour each, so
their figures carry wide confidence intervals; see
[`results/echonova_20h/bootstrap.csv`](results/echonova_20h/bootstrap.csv)
(paired, recording-level bootstrap). Results under other normalizers, CER by
dialect, the Omani slice and all six folds are in
[`results/echonova_20h/`](results/echonova_20h/).

### Private test set (paper, 115 h, 8 varieties)

The figures reported in the paper, recomputed with this package from the stored
outputs on the full private set. **Reported, not externally reproducible:** the
audio and references beyond the public sixth are not released.

<!-- BEGIN echonova-115h-summary -->
| System | Type | WER | Macro WER | CER | Empty % |
| :--- | :--- | ---: | ---: | ---: | ---: |
| Sada-ASR (EchoNova) | proprietary | 14.79 | 16.88 | 6.51 | 0.01 |
| Microsoft MAI-Transcribe-2 | commercial API | 16.54 | 18.08 | 8.46 | 0.03 |
| OpenAI gpt-transcribe | commercial API | 20.41 | 23.10 | 10.71 | 0.18 |
| Audar-ASR-V1-Turbo | open-weight | 26.56 | 30.13 | 13.95 | 0.00 |
| NVIDIA FastConformer (Arabic) | open-weight | 29.15 | 34.26 | 13.76 | 0.19 |
| OpenAI Whisper large-v3 | open-weight | 32.94 | 37.55 | 19.27 | 0.00 |
| NVIDIA Nemotron-3.5 ASR streaming 0.6B | open-weight | 33.60 | 37.53 | 14.99 | 1.48 |
<!-- END echonova-115h-summary -->

### Open Universal Arabic ASR Leaderboard test sets

Sada-ASR's WER (%) on the six test sets of the
[Open Universal Arabic ASR Leaderboard](https://huggingface.co/spaces/elmresearchcenter/open_universal_arabic_asr_leaderboard)
(Wang et al., 2024). **EchoNova-reproduced:** run by EchoNova following the
leaderboard's protocol; not an official leaderboard entry. Avg is the unweighted
mean of the six sets, as on the leaderboard.

<!-- BEGIN public-leaderboard -->
| System | SADA | CV 18.0 | MASC-c | MASC-n | Casab. | MGB-2 | Avg |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sada-ASR, leaderboard normalizer (`oual-2026-07`) | 25.37 | 3.62 | 5.30 | 17.00 | 41.62 | 9.90 | 17.14 |
| Sada-ASR, EchoNova normalizer (`echonova-v1`) | 25.63 | 3.91 | 7.86 | 17.02 | 44.73 | 9.93 | 18.18 |
<!-- END public-leaderboard -->

Published figures for other systems, the protocol details and caveats are in
[`results/public_leaderboard/`](results/public_leaderboard/).

## Installation

```bash
pip install "arabic-asr-benchmark[hf] @ git+https://github.com/echonova-ai-solutions/arabic-asr-benchmark"
```

Python 3.10 or newer. The core package depends only on `numpy` and
`editdistance`; the `hf` extra adds `datasets` for loading the test set.

## Quick start

1. Transcribe every clip of the test set with your system:

   ```python
   from datasets import load_dataset

   ds = load_dataset("echonova-ai/arabic-dialect-asr-benchmark", split="test")
   # ds[i]["audio"]["array"] is 16 kHz mono; decoding with datasets 4.x needs
   # pip install "datasets[audio]"
   ```

2. Write one JSON object per clip to `predictions.jsonl`:

   ```json
   {"id": "egyptian_00001", "prediction": "..."}
   ```

3. Score:

   ```bash
   asr-bench evaluate --predictions predictions.jsonl --system my-system --output my-system.json
   ```

   This prints overall WER, macro WER and CER and writes per-dialect results.
   Missing, duplicate or unknown ids are errors.

4. Compare with a published system, with a paired bootstrap CI:

   ```bash
   asr-bench compare --predictions mine=predictions.jsonl \
       sada-asr=results/echonova_20h/predictions/sada-asr.jsonl \
       --baseline mine --order msa,egyptian,saudi,emirati,kuwaiti,qatari,syrian,lebanese
   ```

Try it without downloading anything, on the bundled synthetic example:

```bash
asr-bench evaluate --references examples/synthetic/references.jsonl \
    --predictions examples/synthetic/predictions_system_a.jsonl
```

## Evaluation methodology

- **Normalization.** References and hypotheses are normalized identically
  before scoring. `echonova-v1` (default) is the paper's normalizer: it removes
  ASCII and Arabic punctuation and the harakat, folds hamza and madda forms of
  alif, hamza on waw and ya, پ and ڤ, Eastern Arabic digits and ة→ه, and deletes
  standalone hamza. It does not convert numbers between digits and words. See
  [docs/normalization.md](docs/normalization.md) for every rule, its known quirks
  and the alternative normalizers.
- **Metrics.** WER and CER are corpus-level: total edit distance over total
  reference length (never a mean of per-clip rates). Macro WER averages the
  per-dialect WERs without weighting. Empty transcripts count as full deletions.
- **Confidence intervals.** Paired bootstrap over recordings (default) or clips,
  2,000 resamples, seed 0.
- **Omani.** Excluded from every headline figure because its references did not
  pass label verification.

Details: [docs/methodology.md](docs/methodology.md).

## Reproducibility

| What | Who can verify it |
| :--- | :--- |
| Metric computation for all seven systems on the public test set | Anyone: references and per-clip outputs are public |
| Inference of the open-weight models | Anyone with the models (dated snapshots, settings in [`systems.json`](results/echonova_20h/systems.json)) |
| Inference of the commercial APIs | Only approximately: hosted models change without notice; measurements are dated |
| Inference of Sada-ASR | Not externally: the model is proprietary |
| Results on the 100 unreleased hours | Not externally: recomputed by EchoNova from stored outputs |

Step-by-step commands: [docs/reproducibility.md](docs/reproducibility.md).

## Citation

If you use the test set or this code, please cite:

```bibtex
@misc{khaled2026sada,
  title  = {EchoNova Sada: A Benchmark Study of Dialectal Arabic Speech Recognition},
  author = {Khaled, Mahmoud and Abd-Elnaser, Mohammed and Mohsen, Mahmoud},
  year   = {2026},
  note   = {EchoNova Technologies. Preprint forthcoming}
}
```

See also [CITATION.cff](CITATION.cff).

## License

Code: Apache License 2.0 (see [LICENSE](LICENSE)). The test set has its own
license, stated on its Hugging Face page. Published system outputs are provided
for verifying the reported metrics.

## Acknowledgments

We thank the maintainers of the Open Universal Arabic ASR Leaderboard
(Wang, Alhmoud and Alqurishi, 2024) and the creators of the SADA, Common Voice,
MASC, MGB-2 and Casablanca test sets. The leaderboard normalizers here are
independent re-implementations of its published evaluation code.
