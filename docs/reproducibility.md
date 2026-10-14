# Reproducing and extending the results

Everything below runs on a clean machine with Python 3.10+, without access to
any EchoNova model, service or credential.

## What can be verified, and by whom

| Claim | Verifiable by | How |
| :--- | :--- | :--- |
| Metrics of the eight systems on the public test set | Anyone | Score the published outputs (step 3) |
| Outputs of the four open-weight models | Anyone | Re-run the models on the public audio; settings we recorded are in `results/echonova_20h/systems.json` |
| Outputs of MAI-Transcribe-2, Gemini 3.5 Transcribe and gpt-transcribe | Approximately | Hosted APIs change without notice; ours are dated measurements (13 October 2026) |
| Outputs of Sada-ASR | Not externally | Proprietary model; its outputs are published so its metrics can be checked |
| Results on the unreleased five sixths (paper tables) | Not externally | Recomputed by EchoNova with this package from stored outputs |
| Sada-ASR on the leaderboard test sets | Protocol only | Test sets are public; Sada-ASR's outputs on them are not published |

## 1. Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install "arabic-asr-benchmark[hf] @ git+https://github.com/echonova-ai-solutions/arabic-asr-benchmark"
git clone https://github.com/echonova-ai-solutions/arabic-asr-benchmark   # for the published results
cd arabic-asr-benchmark
```

Check the installation on the bundled synthetic example (no download):

```bash
asr-bench evaluate --references examples/synthetic/references.jsonl \
    --predictions examples/synthetic/predictions_system_a.jsonl --system a
```

## 2. Get the test set

```python
from datasets import load_dataset

ds = load_dataset("echonova-ai/arabic-dialect-asr-benchmark", split="test")
```

Scoring only reads the `id`, `text`, `dialect` and `recording_id` columns.
Decoding audio with `datasets` 4.x or later requires `pip install "datasets[audio]"`.
To pin the exact version used for the published results, pass the revision
recorded in `results/echonova_20h/runs/*/*.json` (`dataset.revision`), e.g.
`--references hf:echonova-ai/arabic-dialect-asr-benchmark@<revision>`.

## 3. Recompute the published results

```bash
for f in results/echonova_20h/predictions/*.jsonl; do
  asr-bench evaluate --predictions "$f" --system "$(basename "$f" .jsonl)" \
      --system-meta results/echonova_20h/systems.json --output "my_runs/$(basename "$f" .jsonl).json"
done
asr-bench report my_runs --system-meta results/echonova_20h/systems.json
```

The table should match `results/echonova_20h/summary.csv` (rows with
`normalizer = echonova-v1`, `scoring = sada-paper`) exactly; the default
normalizer and scoring protocol are the paper's. Add `--normalizer echonova-v1.1`
or `--normalizer oual-2026-07` to reproduce the other rows, and `--scoring none`
to see the scores without the loop crop and whitespace canonicalization.

Confidence intervals (`results/echonova_20h/bootstrap.csv`):

```bash
asr-bench compare --baseline sada-asr --unit recording \
    --order msa,egyptian,saudi,emirati,kuwaiti,qatari,syrian,lebanese,omani \
    --predictions results/echonova_20h/predictions/*.jsonl --output my_bootstrap.csv
```

## 4. Evaluate your own system

1. Transcribe every clip of the `test` split. Feed the audio as provided
   (16 kHz mono); do not use the reference text, dialect labels or recording
   ids as input.
2. Write `predictions.jsonl`, one line per clip, with your system's raw output
   (no normalization; the scorer normalizes):

   ```json
   {"id": "msa_00001", "prediction": "..."}
   ```

3. Check and score it:

   ```bash
   asr-bench validate --predictions predictions.jsonl
   asr-bench evaluate --predictions predictions.jsonl --system my-system --output my-system.json
   ```

4. Compare with the published systems:

   ```bash
   asr-bench compare --baseline my-system --predictions my-system=predictions.jsonl \
       results/echonova_20h/predictions/*.jsonl \
       --order msa,egyptian,saudi,emirati,kuwaiti,qatari,syrian,lebanese,omani
   ```

When reporting results, state the normalizer, the dataset revision, the date
and settings of your run, and report per-dialect figures and macro WER
alongside the overall WER. Do not tune on this test set.

## Result record format

`asr-bench evaluate --output` writes JSON (schema version 1):

| Key | Content |
| :--- | :--- |
| `system` | Name plus any metadata passed with `--system-meta` |
| `dataset` | Source, config, split, revision, number of references |
| `normalizer` | Normalizer name |
| `scoring` | Scoring protocol applied after normalization (`sada-paper` or `none`) |
| `package` | Name and version of this package |
| `predictions_sha256` | Hash of the scored predictions file |
| `n_missing_predictions` | Clips scored as empty because `--allow-missing` was set |
| `overall` | `n_utterances`, `ref_words`, `hyp_words`, `word_errors`, `sub`, `del`, `ins`, `ref_chars`, `char_errors`, `empty_hypotheses`, `wer`, `cer`, `empty_rate` |
| `macro` | Unweighted mean `wer` and `cer` over `groups` (dialects) |
| `per_dialect` | The `overall` fields for each dialect |

Rates are fractions (multiply by 100 for %).

## Troubleshooting

- **`predictions do not match the references`**: the message lists missing,
  unknown and duplicate ids. Every clip needs exactly one prediction.
- **`To support decoding audio data, please install 'torchcodec'`**: install
  `datasets[audio]`, or use `datasets<4`.
- **Different numbers from another toolkit**: check the normalizer first (see
  [normalization.md](normalization.md)), then the scoring protocol (the default
  crops runaway repetition loops and canonicalizes whitespace; `--scoring none`
  turns this off), then whether the other toolkit averages per-utterance WER
  instead of pooling errors.
