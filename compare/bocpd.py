"""Bayesian online changepoint detection (Adams & MacKay 2007).

Hypotheses are indexed by the start of the current segment: after
observing x[0..t], weight[s] is the posterior probability that x[s] is the
first point after the most recent changepoint. That is the same quantity
as P(s+) in the CPP algorithm. s = 0 means no changepoint has occurred.

Marginal likelihoods are computed in closed form with conjugate priors,
so the cost per step is O(t) and the results are deterministic.

The changepoint is placed before the observation that starts the new
segment, so each hypothesis s is scored by how well its own segment
predicts x[s].
"""

import numpy as np
from scipy import stats
from scipy.special import gammaln, logsumexp


class KnownVarianceNormal:
    """Normal segments with known sigma and a Normal prior on the mean.

    Each parameter set is (m, lam): the posterior mean of mu and the
    posterior precision of mu.
    """

    def __init__(self, sigma, m0, tau):
        self.sigma2 = sigma**2
        self.m0 = m0
        self.lam0 = 1 / tau**2

    def prior(self, m0=None, lam0=None):
        return dict(m=np.array([self.m0 if m0 is None else m0]),
                    lam=np.array([self.lam0 if lam0 is None else lam0]))

    def known_mean(self, mu):
        """Parameters for a segment whose mean is known."""
        return self.prior(m0=mu, lam0=1e12)

    def logpred(self, params, x):
        scale = np.sqrt(self.sigma2 + 1 / params['lam'])
        return stats.norm.logpdf(x, params['m'], scale)

    def log_ml(self, n, s1, s2, params=None):
        """Log marginal likelihood of segments with length n, sum s1, and
        sum of squares s2, integrating mu over its prior."""
        params = self.prior() if params is None else params
        m0, lam0 = params['m'][0], params['lam'][0]
        lam = 1 / self.sigma2
        d1 = s1 - n * m0
        d2 = s2 - 2 * m0 * s1 + n * m0**2
        return (-n / 2 * np.log(2 * np.pi * self.sigma2)
                + 0.5 * np.log(lam0 / (lam0 + n * lam))
                - 0.5 * (lam * d2 - lam**2 * d1**2 / (lam0 + n * lam)))

    def update(self, params, x):
        m, lam = params['m'], params['lam']
        lam1 = lam + 1 / self.sigma2
        m1 = (lam * m + x / self.sigma2) / lam1
        return dict(m=m1, lam=lam1)


class NormalInverseGamma:
    """Normal segments with unknown mean and variance.

    Conjugate Normal-Inverse-Gamma prior; the predictive distribution is
    Student t.
    """

    def __init__(self, mu0, kappa0, alpha0, beta0):
        self.hyper = dict(mu=mu0, kappa=kappa0, alpha=alpha0, beta=beta0)

    def prior(self):
        return {k: np.array([v], dtype=float) for k, v in self.hyper.items()}

    def logpred(self, params, x):
        mu, kappa = params['mu'], params['kappa']
        alpha, beta = params['alpha'], params['beta']
        scale = np.sqrt(beta * (kappa + 1) / (alpha * kappa))
        return stats.t.logpdf(x, 2 * alpha, mu, scale)

    def log_ml(self, n, s1, s2, params=None):
        """Log marginal likelihood of segments with length n, sum s1, and
        sum of squares s2, integrating mu and sigma over their prior."""
        params = self.prior() if params is None else params
        mu0, kappa0 = params['mu'][0], params['kappa'][0]
        alpha0, beta0 = params['alpha'][0], params['beta'][0]
        xbar = s1 / n
        ss = np.maximum(s2 - s1 * xbar, 0)
        kappa = kappa0 + n
        alpha = alpha0 + n / 2
        beta = beta0 + ss / 2 + kappa0 * n * (xbar - mu0)**2 / (2 * kappa)
        return (gammaln(alpha) - gammaln(alpha0)
                + alpha0 * np.log(beta0) - alpha * np.log(beta)
                + 0.5 * np.log(kappa0 / kappa) - n / 2 * np.log(2 * np.pi))

    def update(self, params, x):
        mu, kappa = params['mu'], params['kappa']
        alpha, beta = params['alpha'], params['beta']
        return dict(mu=(kappa * mu + x) / (kappa + 1),
                    kappa=kappa + 1,
                    alpha=alpha + 0.5,
                    beta=beta + kappa * (x - mu)**2 / (2 * (kappa + 1)))


def concat(params1, params2):
    return {k: np.concatenate([params1[k], params2[k]]) for k in params1}


def select(params, keep):
    return {k: v[keep] for k, v in params.items()}


class BOCPD:
    """Online run-length posterior with a constant hazard.

    model: segment model (see above)
    hazard: prior probability of a changepoint at each step
    first: parameters for the segment that starts at x[0]; by default the
        model's prior, but it can encode a known initial mean
    prune: drop hypotheses whose probability falls below this; 0 keeps
        everything, which makes the cost per step O(n)
    """

    def __init__(self, model, hazard, first=None, prune=0.0):
        self.model = model
        self.log_h = np.log(hazard)
        self.log_1mh = np.log1p(-hazard)
        self.first = model.prior() if first is None else first
        self.log_prune = np.log(prune) if prune > 0 else -np.inf
        self.n = 0
        self.starts = np.zeros(0, dtype=int)
        self.log_w = np.zeros(0)
        self.params = None

    def add(self, x):
        """Add a data point and update the posterior."""
        model = self.model
        t = self.n
        self.n += 1
        if t == 0:
            self.params = model.update(self.first, x)
            self.starts = np.zeros(1, dtype=int)
            self.log_w = np.zeros(1)
            return

        prior = model.prior()
        log_new = (self.log_h + logsumexp(self.log_w) +
                   model.logpred(prior, x))
        log_grow = self.log_1mh + self.log_w + model.logpred(self.params, x)

        log_w = np.append(log_grow, log_new)
        self.log_w = log_w - logsumexp(log_w)
        self.starts = np.append(self.starts, t)
        self.params = concat(model.update(self.params, x),
                             model.update(prior, x))

        keep = self.log_w >= self.log_prune
        if not keep.all():
            self.starts = self.starts[keep]
            self.params = select(self.params, keep)
            self.log_w = self.log_w[keep] - logsumexp(self.log_w[keep])

    def p(self):
        """P(s+) for each start index s (s = 0 means no change)."""
        p = np.zeros(self.n)
        p[self.starts] = np.exp(self.log_w)
        return p

    def prob_change(self):
        """Probability that at least one changepoint has occurred."""
        if self.starts[0] != 0:
            return 1.0
        return 1 - np.exp(self.log_w[0])
