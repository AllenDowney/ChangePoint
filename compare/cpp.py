"""P(i+) and P(i++): the last and second-to-last changepoints.

Notation: after observing x[0..N-1],
    p[i]    P(i+), probability that x[i] is the first point after the
            most recent changepoint (i >= 1; p[0] is always 0, and
            1 - sum(p) is the probability that there has been no change)
    pp[j]   P(j++), same for the second-to-last changepoint

The 2008 paper computes both by iterating a coupled system of equations
(see cpp_iterative.py).  But given the exact P(i+), the second equation of
that system,

    P(j++) = sum_k P(k+) P_k(j+),

is a direct formula, where P_k is the posterior computed from x[0..k-1]:
if the last change is at k, the data from k on say nothing about what
came before.  And P(i+) itself is the BOCPD run-length posterior, which an
O(n) forward recursion computes exactly.  So this class runs BOCPD, keeps
the posterior from each step, and combines them.

Costs per step, with no pruning: O(n) for P(i+), and O(n^2) time and
memory for the full P(i++) vector.  With pruning, both are bounded by the
number of hypotheses that survive, and stored posteriors are discarded
when their start index is pruned, because they can never be needed again.
"""

import numpy as np

from bocpd import BOCPD


class CPP(BOCPD):
    """BOCPD that also tracks the second-to-last changepoint.

    Takes the same arguments as BOCPD.
    """

    def __init__(self, model, hazard, first=None, prune=0.0):
        super().__init__(model, hazard, first, prune)
        # history[k] = (starts, weights) of P_k, the posterior from
        # x[0..k-1], excluding the no-change hypothesis
        self.history = {}

    def add(self, x):
        super().add(x)
        changed = self.starts > 0
        self.history[self.n] = (self.starts[changed],
                                np.exp(self.log_w[changed]))

        # P_k is needed only while k is a live start; the newest
        # posterior is kept because the next point can start a segment
        live = set(self.starts.tolist()) | {self.n}
        for k in [k for k in self.history if k not in live]:
            del self.history[k]

    def p(self):
        p = super().p()
        p[0] = 0
        return p

    def pp(self):
        """P(j++) for each j, by the direct formula."""
        pp = np.zeros(self.n)
        for k, w in zip(self.starts, np.exp(self.log_w)):
            if k == 0:
                continue
            starts, weights = self.history[k]
            pp[starts] += w * weights
        return pp
