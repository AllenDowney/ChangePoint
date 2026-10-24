"""Corrected version of the P(i+) / P(i++) recursion from code/Change4.py.

Notation: after observing x[0..N-1],
    p[i]    P(i+), probability that x[i] is the first point after the
            most recent changepoint (i >= 1; p[0] is always 0, and
            1 - sum(p) is the probability that there has been no change)
    pp[j]   P(j++), same for the second-to-last changepoint

The kernel is the system of equations from the paper:

    P(i+)  = P(i+ | H0/1) P(H0/1) + sum_{j<i} P(i+ | j++) P(j++)
    P(i++) = sum_{k>i} P(i++ | k+) P(k+)

where H0/1 is "fewer than two changepoints" and P(i++ | k+) = P_k(i+), the
estimate made from the data before x[k].  Under a product-partition model
with a constant hazard, each of these is an exact identity, so the solution
of the system is the exact posterior, the same quantity BOCPD computes.

Corrections relative to Change4.py:

- Segment likelihoods are marginal likelihoods under a proper conjugate
  prior, computed in closed form, instead of the likelihood at one random
  draw from the posterior (which uses the data twice and is noisy).
- The prior on the no-change hypothesis, (1-f)/f relative to each
  single-change hypothesis, is applied.
- Indices are consistent: P(i+ | j++), P(i+ | H0/1), and P_k all refer to
  x[i] as the first point of the new segment, and P_k uses x[0..k-1].
- Only the first segment uses the known initial mean, if there is one.
- Segments can have any length >= 1.
- The system is iterated to convergence by default.

The cost per step is still O(n^2) time and the stored P_k need O(n^2)
memory, versus O(n) for BOCPD.
"""

import numpy as np


def normalize_rows(L):
    """Exponentiate log weights and normalize each row to sum to 1.

    Rows that are entirely -inf become zeros.
    """
    m = L.max(axis=-1, keepdims=True)
    m = np.where(np.isfinite(m), m, 0)
    W = np.exp(L - m)
    total = W.sum(axis=-1, keepdims=True)
    return np.divide(W, total, out=np.zeros_like(W), where=total > 0)


class IterativeCPP:
    """Online estimator of P(i+) and P(i++).

    model: segment model with a log_ml method (see bocpd.py)
    hazard: prior probability of a changepoint at each step (f)
    first: prior parameters for the first segment, x[0..]; by default the
        model's prior, but it can encode a known initial mean
    iters: Gauss-Seidel sweeps per step; None means iterate until the
        largest change is below tol.  The paper used 1.
    """

    def __init__(self, model, hazard, first=None, iters=None, tol=1e-12,
                 max_iters=500):
        self.model = model
        self.f = hazard
        self.first = model.prior() if first is None else first
        self.iters = iters
        self.tol = tol
        self.max_iters = max_iters

        self.x = []
        self.S1 = [0.0]
        self.S2 = [0.0]
        # ests[L] = (p, pp) computed from x[0..L-1]
        self.ests = [(np.zeros(0), np.zeros(0))]
        self.sweeps = []

    def add(self, x):
        """Add a data point and update the estimates."""
        self.x.append(x)
        self.S1.append(self.S1[-1] + x)
        self.S2.append(self.S2[-1] + x * x)
        self.process()

    def p(self):
        """Current estimate of P(i+)."""
        return self.ests[-1][0]

    def pp(self):
        """Current estimate of P(i++)."""
        return self.ests[-1][1]

    def prob_change(self):
        """Probability that at least one changepoint has occurred."""
        return self.p().sum()

    def log_ml(self, start, end, params=None):
        """Log marginal likelihood of segments x[start:end]."""
        S1 = np.asarray(self.S1)
        S2 = np.asarray(self.S2)
        n = (end - start).astype(float)
        return self.model.log_ml(n, S1[end] - S1[start], S2[end] - S2[start],
                                 params)

    def likelihoods(self, N):
        """Compute W[j, a] = P(a+ | j++) and C[a] = P(a+ | H0/1)."""
        j, a = np.meshgrid(np.arange(N), np.arange(N), indexing='ij')
        mask = (j >= 1) & (a > j)
        js, as_ = j[mask], a[mask]
        end = np.full_like(as_, N)

        # given j++, there is exactly one change after j, equally likely
        # to be at any a, and the data before j are irrelevant
        L = np.full((N, N), -np.inf)
        L[mask] = self.log_ml(js, as_) + self.log_ml(as_, end)
        W = normalize_rows(L)

        # given fewer than two changes: no change (slot 0), or one change
        # at a; the first segment uses the first-segment prior
        a = np.arange(1, N)
        c = np.empty(N)
        c[0] = self.log_ml(np.array([0]), np.array([N]), self.first)[0]
        c[a] = (np.log(self.f / (1 - self.f)) +
                self.log_ml(np.zeros_like(a), a, self.first) +
                self.log_ml(a, np.full_like(a, N)))
        C = normalize_rows(c)
        C[0] = 0
        return W, C

    def process(self):
        N = len(self.x)
        W, C = self.likelihoods(N)

        # start from the previous solution
        prev_p, prev_pp = self.ests[-1]
        p = np.append(prev_p, 0.0)
        pp = np.append(prev_pp, 0.0)

        # E[k, i] = P_k(i+), estimated from x[0..k-1]
        E = np.zeros((N, N))
        for k in range(1, N):
            pk = self.ests[k][0]
            E[k, :len(pk)] = pk

        max_sweeps = self.iters or self.max_iters
        for sweep in range(1, max_sweeps + 1):
            old = np.concatenate([p, pp])
            p = pp @ W + (1 - pp.sum()) * C
            pp = p @ E
            if self.iters is None:
                if np.abs(np.concatenate([p, pp]) - old).max() < self.tol:
                    break
        self.sweeps.append(sweep)
        self.ests.append((p, pp))
