# Summary: the P(i⁺) changepoint algorithm

This summarizes the algorithm in [paper/paper.md](paper/paper.md) ("A novel changepoint detection algorithm", 2008) and its implementation in [code/Change4.py](code/Change4.py).

> The algorithm has been superseded by Bayesian online changepoint detection (Adams & MacKay 2007). See the [README](README.md) and "Conclusions (2026)" below.

## Motivation

Network measurements (throughput, delay, loss) tend to be stationary for a while and then change abruptly, because of routing changes, hardware failures, or the start and end of large transfers. If you want to predict the next value, data from before the most recent change is irrelevant. But you never know for sure whether a change happened, or exactly when.

The usual approach is to compute a test statistic (CUSUM, GLR), compare it with a threshold, and if it is exceeded, declare a changepoint and discard old data. The alternative proposed here is to keep the uncertainty: compute a probability for each possible changepoint location and use those probabilities to mix predictive distributions.

## The key quantity: P(i⁺)

- **P(i⁺)**: the probability that index *i* is the **last** (most recent) changepoint.
- **P(i⁺⁺)**: the probability that *i* is the **second-to-last** changepoint.

P(i⁺) is the quantity you need for prediction: given that *i* is the last changepoint, the next value comes from the distribution fitted to x<sub>i+1</sub> … x<sub>n</sub>. The predictive distribution is then a mixture over *i*, weighted by P(i⁺). (In modern terminology, P(i⁺) is the posterior distribution of the current *run length*.)

## Building it up

**1. Exactly one changepoint.** If there is exactly one changepoint and it is equally likely to be anywhere, the hypotheses *i⁺* are exclusive and exhaustive. Each has a likelihood: data before *i* come from N(μ₀, σ²), data after from N(μ₁, σ²). Normalize the likelihoods and you have P(i⁺).

**2. Zero or one changepoints.** Add the hypothesis H₀ (no change) with a prior based on *f*, the per-step probability of a changepoint: P(i⁺) ∝ f(1−f)ⁿ⁻¹ and P(H₀) ∝ (1−f)ⁿ.

**3. Any number of changepoints (the main idea).** Condition on the second-to-last changepoint. If *j* is the second-to-last changepoint, there is exactly one changepoint after *j*, so P(i⁺ | j⁺⁺) reduces to case 1 applied to the data after *j*. That gives a coupled pair of equations:

$$
\begin{aligned}
P(i^+) &= P(i^+ \mid H_\oslash)\, P(H_\oslash) + \sum_{j<i} P(i^+ \mid j^{++})\, P(j^{++}) \\
P(i^{++}) &= \sum_{k>i} P(i^{++} \mid k^+)\, P(k^+)
\end{aligned}
$$

where H<sub>⊘</sub> means "fewer than two changepoints so far" (handled by case 2) and P(H<sub>⊘</sub>) = 1 − Σ P(j⁺⁺).

The trick that makes this work: **P(i⁺⁺ | k⁺) = P<sub>k</sub>(i⁺)**. If *k* is the last changepoint, data after *k* tell you nothing about what came before, so the probability that *i* is the second-to-last changepoint now equals the probability that *i* was the last changepoint as computed at time *k*. Those values were already computed at earlier time steps, so you just look them up.

**4. Solving it.** At each new data point, recompute the likelihood terms P(i⁺ | j⁺⁺) and P(i⁺ | H<sub>⊘</sub>), then do one Jacobi-style sweep over the system, starting from the previous step's solution. One iteration is usually enough.

## Handling unknown parameters

- Segment statistics come from running sums of x and x², so each segment's sample mean and variance are O(1) to compute for any (start, end) pair.
- Unknown μ and σ² are not integrated out analytically. Instead, each likelihood evaluation **draws one random sample** from the posterior (σ² ~ scaled Inv-χ², μ | σ² ~ Normal, under the noninformative prior uniform on (μ, log σ)) and plugs it in. This is a one-sample Monte Carlo estimate of the marginal likelihood.
- Plugging in point estimates also works, but it overstates the probability of a changepoint.
- To detect changes in variance, σ is estimated separately on each side of the changepoint. This works on the example but becomes erratic when a run of similar values makes the variance estimate collapse.

## Cost

Each step takes O(n²) time, where *n* is the number of points since roughly the second-to-last changepoint, and it stores O(n²) values (all past P<sub>k</sub>(i⁺) and partial sums). The paper calls this feasible for fewer than ~1000 steps between changes at fewer than ~10 steps per second.

## Results in the paper

- **Synthetic mean shift** (changes at t = 50 and 100): P(i⁺) has its main mode at 100, a smaller one at 50, and a spurious one at 142.
- **Nile data** (1871–1970): high P(i⁺) near 1898, consistent with the literature. The algorithm is "mercurial": it picks up a possible change near 1920 at k = 66 and then drops it by k = 99.
- **Detection vs. GLR.** The decision rule is g<sub>k</sub> = Σ P(i⁺), the probability that some change has occurred, compared with a threshold. This variant is called CPP. With μ₀ and σ known, S/N = 1, and the change time geometric with mean 50, CPP's mean delay is 0.5–1.0 steps shorter than GLR's at a fixed false-alarm rate (9.7 vs. 10.7 at α = 0.05). The advantage grows as S/N decreases. GLR is better when σ < 0.7 (S/N > 1.4).

## Revisited in 2026: corrected implementation and comparison

The code is in [compare/](compare/). Its main findings:

**Once corrected, the recursion is exact.** Under a product-partition model with a constant hazard, each equation in the system is an exact conditioning identity. P(i⁺ | j⁺⁺) depends only on the data after *j*, and P(i⁺⁺ | k⁺) = P<sub>k</sub>(i⁺) holds exactly. The fixed point is therefore the exact posterior. The tests check this against brute-force enumeration of every possible set of changepoints. The corrected iterative algorithm ([compare/cpp_iterative.py](compare/cpp_iterative.py)) matches it to 1e-9 for both P(i⁺) and P(i⁺⁺), with known or unknown μ and σ, and so does BOCPD. The original code fell short of this because of the errors listed below.

**So P(i⁺) is the BOCPD run-length posterior.** BOCPD computes it in O(n) per step without iteration. CPP needs O(n²) per step and O(n²) memory, and it takes a median of ~60 Gauss-Seidel sweeps to converge fully. With one sweep, as in the paper, P(i⁺) is off by about 0.005 typically and up to 0.08 just after a change. P(change), which drives detection, is barely affected.

**Detection results** (2000 trials per condition, same data for every method; mean delay at false-alarm rate α = 0.05; change size 1, so S/N = 1/σ):

| σ | Exact (BOCPD = converged CPP), τ = 1 | CPP, 1 sweep | GLR, ν<sub>min</sub> = 0.5 |
|---|---|---|---|
| 0.25 | 1.34 | 1.35 | 1.29 |
| 0.50 | 3.74 | 3.76 | 3.55 |
| 0.75 | 6.73 | 6.74 | 6.71 |
| 1.00 | 10.64 | 10.63 | 11.21 |
| 1.25 | 14.83 | 14.85 | 17.13 |
| 1.50 | 19.70 | 19.45 | 24.14 |

The paper's qualitative claim holds: the Bayesian detector beats GLR when S/N ≤ 1, and the advantage grows as noise increases. GLR is slightly better when S/N ≥ 2. The advantage belongs to Bayesian run-length inference in general, which BOCPD already provides, not to CPP specifically. A wider prior on the new mean (τ = 3) changes little. No error bars were computed, so differences of a few tenths should not be read as meaningful.

**What the recursion offers beyond BOCPD:** the exact posterior over the second-to-last changepoint, P(i⁺⁺), which BOCPD does not provide directly. See `compare/results/*.png`.

**The iteration isn't needed.** Given the exact P(i⁺), the second equation, P(j⁺⁺) = Σ<sub>k</sub> P(k⁺)·P<sub>k</sub>(j⁺), is a direct formula. [compare/cpp.py](compare/cpp.py) therefore runs BOCPD, which is O(n) per step for P(i⁺), and stores each step's posterior. That gives:
- the full P(i⁺⁺) vector at O(n²) cost;
- any fixed summary of it, such as its mean, at O(n), by storing one number per step.

With pruning, the live hypotheses and stored posteriors shrink to roughly the data since the second-to-last change. This matches the cost the paper described, but without iteration. The iterative version is kept in [compare/cpp_iterative.py](compare/cpp_iterative.py).

**Parallel work.** The system of equations first appeared in a November 2006 draft (`paper/downey06changepoint.pdf`). Fearnhead (2006) and Adams & MacKay (2007) developed the same posterior independently, along with correct and efficient ways to compute it. Those papers are the ones to read and cite (see [REFERENCES.md](REFERENCES.md)).



## Conclusions (2026)

- **The algorithm is superseded.** Corrected, it computes the BOCPD run-length posterior by a slower route. For P(i⁺), use BOCPD (Adams & MacKay 2007) or Fearnhead (2006).
- **The only extra output is P(i⁺⁺),** the posterior over the second-to-last changepoint, and it doesn't need the iterative system: it follows from BOCPD's stored posteriors (`compare/cpp.py`). It could matter if you care about the size of the most recent change, which needs the segment before it. But established alternatives exist for most related questions, such as outlier models for transient blips, switching models for recurring regimes, and hazard learning (Wilson et al. 2010) for the change rate.
- **The detection result is not specific to this algorithm.** The paper's evaluation puts a geometric prior on the change time, and a Bayesian detector whose prior matches it is the kind of method theory leads one to expect to do well (Shiryaev 1963). BOCPD performs the same.

