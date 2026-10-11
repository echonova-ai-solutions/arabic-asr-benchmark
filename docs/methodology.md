# Evaluation methodology

## Tracks

Results come from three evaluation tracks that are never combined into one
number:

| Track | Data | Systems | Verifiable by others |
| :--- | :--- | :--- | :--- |
| `echonova_20h` | The public test set: 7,396 clips, 19.16 h, 8 varieties | 7 | Metrics: yes (references and outputs public) |
| `echonova_private_115h` | The paper's private test set: 44,407 clips, 115 h, 8 varieties | 7 | No (data unreleased); recomputed by EchoNova |
| `public_leaderboard` | Six test sets of the Open Universal Arabic ASR Leaderboard: 46,757 clips | Sada-ASR | Protocol: yes; outputs: not published |

The public test set is one sixth of the private one, so the first two tracks
measure the same systems on overlapping data. Their figures are close but not
identical and should not be mixed in one table.

## Predictions

A system's output is a JSON Lines file with one `{"id", "prediction"}` object
per clip. Predictions are matched to references by `id`. A missing, duplicate or
unknown id is an error; `--allow-missing` scores missing clips as empty
transcripts instead and records how many there were. An empty transcript is a
valid prediction and is scored as deleting every reference word.

For the seven published systems, the prediction is the system's raw output
before any normalization, exactly as stored during the paper's evaluation runs
(September 2026). Every clip of every system has an output; no run failed.

## Normalization

References and hypotheses are normalized identically before scoring. The
default, `echonova-v1`, is the paper's normalizer; see
[normalization.md](normalization.md) for all normalizers and their rules.
Results under different normalizers are reported in separate tables.

## Metrics

For a set of clips with normalized references r and hypotheses h:

- **WER** = Σ edit distance between the word sequences / Σ reference words.
  Words are whitespace-separated tokens.
- **CER** = Σ edit distance between the character sequences / Σ reference
  characters. Characters include spaces.
- **Substitutions, deletions, insertions** come from a minimum-cost alignment
  (ties broken in that order) and sum to the edit distance.
- **Macro WER / CER** = unweighted mean of the per-dialect corpus WER / CER
  over the eight varieties (computed from unrounded values).
- **Empty %** = share of clips whose normalized hypothesis is empty.

WER and CER are corpus-level micro averages, never a mean of per-clip error
rates, so long clips weigh more than short ones. Because MSA is 43.5% of the
audio, the overall figure is dominated by MSA; read per-dialect and macro
figures alongside it. A corpus whose references are all empty has no defined
error rate and raises an error.

## Confidence intervals

`asr-bench compare` gives a paired bootstrap confidence interval for one
system's WER margin over another:

delta = (errors_B − errors_A) / reference words × 100, positive when A is better.

Each of 2,000 resamples draws units with replacement; the interval is the 2.5th
and 97.5th percentile (linear interpolation). One random generator, seeded with
0, is consumed per comparison across the dialects in a fixed order (MSA,
Egyptian, Saudi, Emirati, Kuwaiti, Qatari, Syrian, Lebanese), then for the
pooled set.

- **Recording-level** (default): the units are source recordings
  (`recording_id`); a recording's clips are summed before resampling. Clips
  from one recording share speakers and conditions, and Qatari, Lebanese and
  Syrian come from 23-49 recordings in the public set, so this is the honest
  default.
- **Clip-level** (`--unit clip`): the units are clips. This is the procedure of
  the paper's Table 3, which it reproduces exactly; its intervals are narrower
  than recording-level ones.

## Omani

The Omani references did not pass EchoNova's label verification. Omani clips
are released only in the separate `omani_unverified` configuration and are
excluded from every headline figure, macro average and bootstrap.
Results on it are in `results/echonova_20h/omani_unverified.csv` and
`results/echonova_private_115h/with_omani.csv` for completeness.

## Systems and settings

Every system was run on the same audio: each clip decoded, resampled to
16 kHz mono and, for the APIs, sent as 16-bit PCM WAV. No system, including
Sada-ASR, used contextual biasing, custom vocabulary or other adaptation. The
recorded settings and dates of each system are in
[`results/echonova_20h/systems.json`](../results/echonova_20h/systems.json);
anything that was not recorded is `null` there rather than guessed. Commercial
APIs change without notice, so their figures describe the API on the date
given.
