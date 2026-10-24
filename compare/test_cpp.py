"""Check CPP and BOCPD against the exact posterior, computed by brute-force
enumeration of every set of changepoints, and check GLR against a literal
transcription of calc_gk_glr in code/Change4.py.
"""

from itertools import combinations

import numpy as np
import pytest
from scipy.special import logsumexp

from bocpd import BOCPD, KnownVarianceNormal, NormalInverseGamma
from cpp import CPP
from cpp_iterative import IterativeCPP
from glr import GLR

F = 0.1


def brute_force(xs, model, first, f):
    """Exact P(i+) and P(i++) for the data xs by enumerating all
    partitions; i = 0 / j = 0 stand for 'fewer than one / two changes'."""
    N = len(xs)
    S1 = np.concatenate([[0], np.cumsum(xs)])
    S2 = np.concatenate([[0], np.cumsum(np.square(xs))])

    def seg(a, b, params=None):
        return model.log_ml(np.array([b - a], float), np.array([S1[b] - S1[a]]),
                            np.array([S2[b] - S2[a]]), params)[0]

    logp, last, second = [], [], []
    for c in range(N):
        for cps in combinations(range(1, N), c):
            bounds = (0,) + cps + (N,)
            lp = c * np.log(f) + (N - 1 - c) * np.log(1 - f)
            lp += seg(bounds[0], bounds[1], first)
            lp += sum(seg(a, b) for a, b in zip(bounds[1:-1], bounds[2:]))
            logp.append(lp)
            last.append(cps[-1] if c >= 1 else 0)
            second.append(cps[-2] if c >= 2 else 0)

    w = np.exp(np.array(logp) - logsumexp(logp))
    p = np.bincount(last, weights=w, minlength=N)
    pp = np.bincount(second, weights=w, minlength=N)
    p[0] = pp[0] = 0
    return p, pp


def make_data(seed, N):
    rng = np.random.default_rng(seed)
    return np.concatenate([rng.normal(0, 1, N // 2), rng.normal(2, 0.7, N - N // 2)])


MODELS = {
    'nig': lambda: (NormalInverseGamma(0.5, 1.0, 1.0, 1.0), None),
    'known_sigma': lambda: (KnownVarianceNormal(1.0, 0.0, 1.0), None),
    'known_first_mean': lambda: (KnownVarianceNormal(1.0, 0.0, 1.0), 'known'),
}


@pytest.mark.parametrize('name', MODELS)
def test_cpp_and_bocpd_match_brute_force(name):
    model, first = MODELS[name]()
    if first == 'known':
        first = model.known_mean(0.0)
    xs = make_data(1, 9)

    cpp = CPP(model, F, first=first)
    itr = IterativeCPP(model, F, first=first)
    boc = BOCPD(model, F, first=first)
    for N in range(1, len(xs) + 1):
        for det in [cpp, itr, boc]:
            det.add(xs[N - 1])
        p, pp = brute_force(xs[:N], model, first if first else model.prior(), F)

        for det in [cpp, itr]:
            np.testing.assert_allclose(det.p(), p, atol=1e-9)
            np.testing.assert_allclose(det.pp(), pp, atol=1e-9)
        np.testing.assert_allclose(boc.p()[1:], p[1:], atol=1e-9)
        np.testing.assert_allclose(boc.p()[0], 1 - p.sum(), atol=1e-9)


def long_series():
    rng = np.random.default_rng(2)
    return np.concatenate([rng.normal(mu, 1, 40) for mu in [-0.5, 0.5, 0.0]])


def test_direct_matches_iterative_on_long_series():
    model = NormalInverseGamma(0.0, 1.0, 1.0, 1.0)
    cpp = CPP(model, 0.02)
    itr = IterativeCPP(model, 0.02)
    for x in long_series():
        cpp.add(x)
        itr.add(x)
        np.testing.assert_allclose(cpp.p(), itr.p(), atol=1e-8)
        np.testing.assert_allclose(cpp.pp(), itr.pp(), atol=1e-8)


def test_pruning_is_accurate_and_bounds_memory():
    model = NormalInverseGamma(0.0, 1.0, 1.0, 1.0)
    rng = np.random.default_rng(6)
    xs = np.concatenate([rng.normal(mu, 1, 300) for mu in [0, 2, 0, 3]])
    exact = CPP(model, 0.01)
    pruned = CPP(model, 0.01, prune=1e-8)
    sizes = []
    for x in xs:
        exact.add(x)
        pruned.add(x)
        sizes.append(len(pruned.starts))
    np.testing.assert_allclose(pruned.p(), exact.p(), atol=1e-6)
    np.testing.assert_allclose(pruned.pp(), exact.pp(), atol=1e-6)
    # live hypotheses grow within a segment and collapse after each change
    for change in [300, 600, 900]:
        assert sizes[change + 20] < 100
    assert len(pruned.history) <= len(pruned.starts) + 1


def test_log_ml_matches_sequential_predictive():
    rng = np.random.default_rng(4)
    xs = rng.normal(1, 2, 12)
    for model in [NormalInverseGamma(0.3, 0.5, 2.0, 3.0),
                  KnownVarianceNormal(1.5, 0.2, 2.0)]:
        params, total = model.prior(), 0.0
        for x in xs:
            total += model.logpred(params, x)[0]
            params = model.update(params, x)
        ml = model.log_ml(np.array([12.0]), np.array([xs.sum()]),
                          np.array([np.square(xs).sum()]))[0]
        assert np.isclose(total, ml)


def test_glr_matches_loop():
    rng = np.random.default_rng(5)
    xs = rng.normal(0.3, 1, 40)
    glr = GLR(mu0=0.0, sigma=1.0, numin=0.5)
    for k, x in enumerate(xs):
        glr.add(x)
        # literal calc_gk_glr
        t1 = list(xs[:k + 1])
        co = [sum(y for y in t1[j:]) for j in range(k + 1)]
        t2 = [sum(abs(y) - 0.5 for y in t1[j:]) for j in range(k + 1)]
        t4 = [max(t2[j] / (k - j + 1), 0) + 0.5 for j in range(k + 1)]
        nuhat = [np.sign(co[j]) * abs(t4[j]) for j in range(k + 1)]
        t5 = [(co[j] - nuhat[j] / 2.0 * (k - j + 1)) * nuhat[j] for j in range(k + 1)]
        assert np.isclose(glr.decision(), max(t5))
