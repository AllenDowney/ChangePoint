# arXiv v2 of 0812.1237

Replacement for "A novel changepoint detection algorithm". The only change from v1 is a notice at the start of the abstract; the title and body are unchanged.

## Files to upload

`paper.tex`, `paper.bbl`, and the five figures (`example.eps`, `nile.eps`, `var.eps`, `matfar.eps`, `matsig.eps`). arXiv builds it with `latex`, as in v1.

## Abstract field

Note added in version 2 (2026): this paper has been superseded. The probability it computes, that each index is the most recent changepoint, is the run-length posterior of Bayesian online changepoint detection (Adams and MacKay, arXiv:0710.3742, 2007), which computes it exactly and efficiently; see also Fearnhead, Statistics and Computing 16:203-213, 2006. The implementation used for the results in this paper contained errors, so those results should not be relied on. A corrected implementation, tests, and a description of the errors are at https://github.com/AllenDowney/ChangePoint. The rest of the paper is unchanged from version 1.

We propose an algorithm for simultaneously detecting and locating changepoints in a time series, and a framework for predicting the distribution of the next point in the series. The kernel of the algorithm is a system of equations that computes, for each index i, the probability that the last (most recent) change point occurred at i. We evaluate this algorithm by applying it to the change point detection problem and comparing it to the generalized likelihood ratio (GLR) algorithm. We find that our algorithm is as good as GLR, or better, over a wide range of scenarios, and that the advantage increases as the signal-to-noise ratio decreases.

## Comments field

12 pages. v2: adds a notice that this paper is superseded by Bayesian online changepoint detection (Adams and MacKay 2007); corrected code at https://github.com/AllenDowney/ChangePoint
