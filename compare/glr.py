"""GLR decision function, ported from calc_gk_glr in code/Change4.py.

Basseville and Nikiforov (1993), Equation 2.4.38: change in the mean of a
normal process with known mu0 and sigma, unknown change size with a
minimum magnitude numin.
"""

import numpy as np


class GLR:
    """Online GLR detector with the same interface as CPP and BOCPD."""

    def __init__(self, mu0=0.0, sigma=1.0, numin=0.5):
        self.mu0 = mu0
        self.sigma = sigma
        self.numin = numin
        self.x = []

    def add(self, x):
        self.x.append(x)

    def decision(self):
        """g_k, computed from scratch over all hypothesized change times j."""
        y = np.asarray(self.x) - self.mu0
        k = len(y) - 1
        counts = k - np.arange(k + 1) + 1

        # backward cumulative sums: co[j] = sum(y[j:])
        co = np.cumsum(y[::-1])[::-1]
        t2 = np.cumsum((np.abs(y) - self.numin)[::-1])[::-1]
        t4 = np.maximum(t2 / counts, 0) + self.numin
        nuhat = np.sign(co) * np.abs(t4)

        t5 = (co - nuhat / 2.0 * counts) * nuhat
        return t5.max() / self.sigma**2
