# Results: private test set (`echonova_private_120h`)

The figures of the paper (Tables 2, 3, 5 and 7): the twelve systems on
the full private test set, 53,597 clips and 119.86 h in nine varieties, normalizer
`echonova-v1` with the `sada-paper` scoring. They were recomputed by EchoNova with
this package from the systems' stored raw outputs and match the paper exactly
([docs/paper_consistency.md](../../docs/paper_consistency.md)).

**Status: reported, not externally reproducible.** One sixth of this test set is
public (`results/echonova_20h`); the audio, references and per-clip outputs of the
remaining five sixths are not released, so only aggregate results are given.

| File | Content |
| :--- | :--- |
| `runs/<system>.json` | Result records (aggregates only) |
| `summary.csv`, `per_dialect.csv` | As in `echonova_20h` |
