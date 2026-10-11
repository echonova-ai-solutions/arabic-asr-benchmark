import numpy as np
import pytest

from arabic_asr_benchmark.bootstrap import compare_by_group, paired_bootstrap


def _data(n=500, seed=1):
    r = np.random.default_rng(seed)
    L = r.integers(1, 20, n)
    a = r.binomial(L, 0.15)
    b = r.binomial(L, 0.20)
    return a, b, L


def test_point_estimate_and_ci_contains_it():
    a, b, L = _data()
    res = paired_bootstrap(a, b, L)
    assert res.delta == pytest.approx((b.sum() - a.sum()) / L.sum() * 100)
    assert res.ci_low < res.delta < res.ci_high
    assert res.unit == "clip" and res.n_units == 500


def test_deterministic_and_matches_legacy_procedure():
    a, b, L = _data()
    res = paired_bootstrap(a, b, L, rng=np.random.default_rng(0))
    # The procedure used for the paper's Table 3.
    rng = np.random.default_rng(0)
    idx = rng.integers(0, len(L), size=(2000, len(L)))
    diff = (b[idx].sum(1) - a[idx].sum(1)) / L[idx].sum(1) * 100
    lo, hi = np.percentile(diff, [2.5, 97.5])
    assert (res.ci_low, res.ci_high) == (lo, hi)


def test_chunking_does_not_change_results(monkeypatch):
    import arabic_asr_benchmark.bootstrap as bs

    a, b, L = _data()
    full = paired_bootstrap(a, b, L, rng=np.random.default_rng(3))
    monkeypatch.setattr(bs, "_CHUNK_ELEMENTS", 7 * len(L))
    chunked = paired_bootstrap(a, b, L, rng=np.random.default_rng(3))
    assert (full.ci_low, full.ci_high) == (chunked.ci_low, chunked.ci_high)


def test_cluster_bootstrap_is_wider_for_correlated_groups():
    r = np.random.default_rng(5)
    groups = np.repeat(np.arange(20), 50)
    effect = r.normal(0, 3, 20)[groups]  # recording-level effect on B
    L = np.full(1000, 10)
    a = r.binomial(L, 0.2)
    b = np.clip(r.binomial(L, 0.2) + np.round(effect).astype(int), 0, 10)
    clip = paired_bootstrap(a, b, L)
    rec = paired_bootstrap(a, b, L, groups=groups.astype(str))
    assert rec.unit == "recording" and rec.n_units == 20
    assert (rec.ci_high - rec.ci_low) > (clip.ci_high - clip.ci_low)


def test_compare_by_group_consumes_one_rng_in_order():
    a, b, L = _data(300)
    per_group = {"x": (a[:100], b[:100], L[:100], ["r"] * 100), "y": (a[100:], b[100:], L[100:], ["r"] * 200)}
    res = compare_by_group(per_group, order=["x", "y"])
    rng = np.random.default_rng(0)
    rx = paired_bootstrap(a[:100], b[:100], L[:100], rng=rng)
    ry = paired_bootstrap(a[100:], b[100:], L[100:], rng=rng)
    assert res["x"] == rx and res["y"] == ry
    assert res["overall"].n_units == 300


def test_errors():
    with pytest.raises(ValueError):
        paired_bootstrap([1], [1, 2], [1])
    with pytest.raises(ValueError):
        paired_bootstrap([0], [0], [0])
