# Results: private test set (`echonova_private_115h`)

The figures of the EchoNova Sada paper (Tables 2, 3, 5): seven systems on the
full private test set, 44,407 clips and 115 h in eight varieties, normalizer
`echonova-v1`. They were recomputed by EchoNova with this package from the
systems' stored raw outputs and match the paper exactly
([docs/paper_consistency.md](../../docs/paper_consistency.md)).

**Status: reported, not externally reproducible.** One sixth of this test set is
public (`results/echonova_20h`); the audio, references and per-clip outputs of
the remaining five sixths are not released, so only aggregate results are given.

| File | Content |
| :--- | :--- |
| `runs/<system>.json` | Result records (aggregates only) |
| `summary.csv`, `per_dialect.csv` | As in `echonova_20h` |
| `bootstrap.csv` | Sada-ASR's margin over each system, clip-level paired bootstrap (the procedure of the paper's Table 3) |
| `with_omani.csv` | WER/CER including the Omani subset (paper Table 5) and on Omani alone |
