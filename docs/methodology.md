# Evaluation methodology

## Tracks

Results come from three evaluation tracks that are never combined into one
number:

| Track | Data | Systems | Verifiable by others |
| :--- | :--- | :--- | :--- |
| `echonova_20h` | The public test set: 8,925 clips, 19.95 h, 9 varieties | 12 | Metrics: yes for the 10 systems whose outputs are public |
| `echonova_private_120h` | The paper's private test set: 53,597 clips, 119.86 h, 9 varieties | 12 | No (five sixths unreleased); recomputed by EchoNova |
| `public_leaderboard` | Six test sets of the Open Universal Arabic ASR Leaderboard: 46,757 clips | Sada-ASR | Protocol: yes; outputs: not published |

The public test set is one sixth of the private one, so the first two tracks
measure the same systems on overlapping data. Their figures are close but not
identical and should not be mixed in one table.

The twelve systems are those compared in the paper: Sada-ASR, five commercial
APIs (MAI-Transcribe-2, ElevenLabs Scribe v2, Gemini 3.5 Transcribe,
gpt-transcribe, Speechmatics Enhanced) and six open-weight models (Jais-ASR,
Audar-ASR-V1-Turbo, FastConformer, Whisper large-v3, Nemotron-3.5, Cohere
Transcribe Arabic). All were run on identical audio on 13 October 2026, except
Jais-ASR and Speechmatics Enhanced (15 October 2026, UTC), with the settings
recorded in [`results/echonova_20h/systems.json`](../results/echonova_20h/systems.json).
No system, including Sada-ASR, used contextual biasing, custom vocabulary or other
adaptation. Per-clip outputs are published for ten systems; ElevenLabs Scribe
v2 and Speechmatics Enhanced are published as metrics only.

## Predictions

A system's output is a JSON Lines file with one `{"id", "prediction"}` object
per clip. Predictions are matched to references by `id`. A missing, duplicate or
unknown id is an error; `--allow-missing` scores missing clips as empty
transcripts instead and records how many there were. An empty transcript is a
valid prediction and is scored as deleting every reference word.

For the published systems, the prediction is the system's raw output before any
normalization, exactly as stored during the paper's evaluation. One collection
rule applied to every API: an output more than five times the reference's word
count and longer than 50 words was re-requested up to three times, and the first
normal output kept. This touched 2 Gemini clips on the full private set, both of
which returned the same output every time.

## Normalization and scoring

References and hypotheses are normalized identically before scoring. The
default, `echonova-v1`, is the paper's normalizer. With it, the `sada-paper`
scoring protocol is applied to every system:

1. **Loop crop (hypothesis only).** Any one- to three-word unit repeated more than
   ten times back-to-back is cut to ten copies. No reference repeats a unit more
   than seven times, so no correct transcript is altered.
2. **Whitespace canonicalization (both sides).** CER counts characters, not
   layout.

Stored predictions are never edited, and the reference is never used to change a
prediction. With the leaderboard normalizers the scoring is plain, as on the
leaderboard. See [normalization.md](normalization.md) for every rule. Results
under different normalizers or scoring protocols are reported in separate
tables.

## Metrics

For a set of clips with normalized references r and hypotheses h:

- **WER** = Σ edit distance between the word sequences / Σ reference words.
  Words are whitespace-separated tokens.
- **CER** = Σ edit distance between the character sequences / Σ reference
  characters. Characters include spaces.
- **Substitutions, deletions, insertions** come from a minimum-cost alignment
  (ties broken in that order) and sum to the edit distance.
- **Macro WER / CER** = unweighted mean of the per-variety corpus WER / CER
  over the nine varieties (computed from unrounded values).
- **Empty %** = share of clips whose normalized hypothesis is empty.

WER and CER are corpus-level micro averages, never a mean of per-clip error
rates, so long clips weigh more than short ones. Because MSA is about 41% of the
audio, the overall figure is dominated by MSA; read per-variety and macro figures
alongside it. A corpus whose references are all empty has no defined error rate
and raises an error.

## Confidence intervals

`asr-bench compare` gives a paired bootstrap confidence interval for one
system's WER margin over another:

delta = (errors_B − errors_A) / reference words × 100, positive when A is better.

Each of 2,000 resamples draws units with replacement; the interval is the 2.5th
and 97.5th percentile (linear interpolation). One random generator, seeded with
0, is consumed per comparison across the varieties in a fixed order, then for the
pooled set.

- **Recording-level** (default): the units are source recordings
  (`recording_id`); a recording's clips are summed before resampling. Clips from
  one recording share speakers and conditions, and Qatari, Lebanese and Syrian
  come from 41-75 recordings in the public set, so this is the honest default.
- **Clip-level** (`--unit clip`): the units are clips. Intervals are narrower.

The paper's intervals also resample source recordings, stratified by variety,
but with their own recording grouping and draw order. The package's intervals are
reported as its own and can differ from the paper's in the second decimal.

## Review status of the references

The MSA, Egyptian, Emirati and Saudi transcripts were reviewed by a second
person. Almost all Kuwaiti, Lebanese, Omani, Qatari and Syrian transcripts are
single-pass annotations. All nine varieties are part of every headline figure.
