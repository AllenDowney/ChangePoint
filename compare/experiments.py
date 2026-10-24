"""Compare CPP (corrected), BOCPD, and GLR.

With matching priors, converged iterative CPP and BOCPD compute the same exact
posterior (see test_cpp.py), so the detection experiments run BOCPD for the
exact version and CPP with one sweep per step, as in the paper.

Usage:
    python experiments.py examples           # P(i+) on the paper's examples
    python experiments.py detection          # mean delay vs. false alarms
    python experiments.py detection --runs 200 --sigmas 1.0

Results (CSV and PNG) are written to compare/results/.

The detection setup follows mta_vs_thresh / mta_vs_sigma in
code/Change4.py: the change time n is ceil(Exponential(mean 1/f)), the
data are n points from N(0, sigma) followed by 100 points from N(1, sigma),
and the delay is averaged with a 5% trimmed mean.

Scoring differs from Change4.py by one step: there, an alarm on the first
post-change point (index n) counted as a false alarm. Here an alarm is
false only if it comes before index n, and the delay k - n + 1 is the
number of post-change points seen, as in the paper's tau = t_a - t_0 + 1.
"""

import argparse
import os
from functools import partial
from multiprocessing import Pool

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from bocpd import BOCPD, KnownVarianceNormal, NormalInverseGamma
from cpp import CPP
from cpp_iterative import IterativeCPP
from glr import GLR

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results')
NILE = os.path.join(HERE, '..', 'code', 'nile.dat')

F = 0.02

# categorical slots 1-3 of the reference palette, in fixed order
STYLE = {
    'cpp1':       dict(color='#2a78d6', marker='o', label='CPP, 1 sweep/step (τ = 1)'),
    'bocpd':      dict(color='#eb6834', marker='s', label='Exact: BOCPD = converged CPP (τ = 1)'),
    'glr':        dict(color='#1baf7a', marker='^', label='GLR (ν_min = 0.5)'),
    'bocpd_tau3': dict(color='#eb6834', marker='s', label='Exact, τ = 3',
                       linestyle='--', markerfacecolor='white'),
}
INK = '#3d3d3a'
MUTED = '#8a8980'
GRID = '#e4e3dd'

PROB_THRESHES = np.array([0.3, 0.4, 0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9,
                          0.92, 0.94, 0.95, 0.96, 0.97, 0.98, 0.985, 0.99,
                          0.995, 0.998, 0.999, 0.9995])
GLR_THRESHES = np.arange(1.0, 12.01, 0.25)


def style_axes(ax):
    ax.grid(True, color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ['top', 'right']:
        ax.spines[side].set_visible(False)
    for side in ['left', 'bottom']:
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9)
    ax.xaxis.label.set_color(INK)
    ax.yaxis.label.set_color(INK)


# --- detection experiments ---

def make_detector(alg, sigma, seed):
    """Known mu0 = 0 before the change and known sigma; the mean of each
    later segment has prior N(0, tau^2)."""
    if alg == 'glr':
        return GLR(mu0=0.0, sigma=sigma, numin=0.5)
    tau = 3.0 if alg == 'bocpd_tau3' else 1.0
    model = KnownVarianceNormal(sigma=sigma, m0=0.0, tau=tau)
    first = model.known_mean(0.0)
    if alg == 'cpp1':
        return IterativeCPP(model, F, first=first, iters=1)
    if alg.startswith('bocpd'):
        return BOCPD(model, F, first=first)
    raise ValueError(alg)


def decision(det):
    return det.decision() if isinstance(det, GLR) else det.prob_change()


def trial(seed, alg, sigma, threshes):
    """Port of test_true_alarm: returns the delay per threshold, <= 0 for
    a false alarm, inf if the threshold was never crossed."""
    rng = np.random.default_rng(seed)
    n = int(np.ceil(rng.exponential(1 / F)))
    data = np.concatenate([rng.normal(0.0, sigma, n),
                           rng.normal(1.0, sigma, 100)])

    det = make_detector(alg, sigma, seed)
    tba = np.full(len(threshes), np.inf)
    for k, x in enumerate(data):
        det.add(x)
        g = decision(det)
        newly = np.isinf(tba) & (g > threshes)
        tba[newly] = k - n + 1
        if not np.isinf(tba).any():
            break
    return tba


def trimmed_average(t, percent=0.05):
    """Port of trimmed_average: drop the top and bottom 5% (at least 1)."""
    t = np.sort(t)
    trim = max(int(round(percent * len(t))), 1)
    t = t[trim:-trim]
    return t.mean() if len(t) else np.nan


def summarize(tbas, threshes):
    """Port of alarm_time: completion rate, false alarm rate, and mean
    alarm time of runs without a false alarm, for each threshold."""
    rows = []
    for i, thresh in enumerate(threshes):
        t = tbas[:, i]
        good = t[t > 0]
        rows.append(dict(thresh=thresh,
                         complete=np.isfinite(t).mean(),
                         fa=(t <= 0).mean(),
                         mat=trimmed_average(good) if len(good) else np.nan))
    return pd.DataFrame(rows)


def interpolate(df, fa):
    """Mean alarm time at false alarm rate fa, by linear interpolation
    between the thresholds that bracket it."""
    d = df.dropna().sort_values('fa')
    d = d[np.isfinite(d['mat'])]
    if len(d) < 2 or not d['fa'].min() <= fa <= d['fa'].max():
        return np.nan
    return np.interp(fa, d['fa'], d['mat'])


def run_detection(algs, sigmas, runs, processes):
    rows = []
    with Pool(processes) as pool:
        for sigma in sigmas:
            for alg in algs:
                threshes = GLR_THRESHES if alg == 'glr' else PROB_THRESHES
                func = partial(trial, alg=alg, sigma=sigma, threshes=threshes)
                tbas = np.array(pool.map(func, range(runs), chunksize=4))
                df = summarize(tbas, threshes)
                df['alg'], df['sigma'] = alg, sigma
                rows.append(df)
                print(f'sigma={sigma} {alg:10s} '
                      f'MAT@0.05={interpolate(df, 0.05):6.2f} '
                      f'MAT@0.10={interpolate(df, 0.10):6.2f}', flush=True)
    return pd.concat(rows, ignore_index=True)


def plot_matfar(results, sigma, path):
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for alg, df in results[results.sigma == sigma].groupby('alg', sort=False):
        d = df.dropna().sort_values('fa')
        d = d[(d.fa > 0) & (d.fa <= 0.3) & np.isfinite(d.mat)]
        ax.plot(d.fa, d.mat, linewidth=2, markersize=6, **STYLE[alg])
    ax.set_xlabel('False alarm probability α')
    ax.set_ylabel('Mean delay (time steps, trimmed)')
    ax.set_title(f'Mean delay vs. false alarm rate (S/N = {1 / sigma:g})',
                 color=INK, fontsize=11, loc='left')
    style_axes(ax)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_matsig(summary, fa, path):
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    for alg, df in summary.groupby('alg', sort=False):
        ax.plot(df.sigma, df[f'mat@{fa}'], linewidth=2, markersize=6,
                **STYLE[alg])
    ax.set_xlabel('σ (change size is 1, so S/N = 1/σ)')
    ax.set_ylabel(f'Mean delay at α = {fa}')
    ax.set_title(f'Mean delay vs. noise, false alarm rate {fa}',
                 color=INK, fontsize=11, loc='left')
    style_axes(ax)
    ax.legend(frameon=False, fontsize=9, labelcolor=INK)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def detection(args):
    results = run_detection(args.algs, args.sigmas, args.runs, args.processes)
    results.to_csv(os.path.join(RESULTS, 'detection.csv'), index=False)

    summary = []
    for (alg, sigma), df in results.groupby(['alg', 'sigma'], sort=False):
        summary.append({'alg': alg, 'sigma': sigma,
                        'mat@0.05': interpolate(df, 0.05),
                        'mat@0.1': interpolate(df, 0.10)})
    summary = pd.DataFrame(summary)
    summary.to_csv(os.path.join(RESULTS, 'detection_summary.csv'), index=False)
    print(summary.pivot(index='sigma', columns='alg', values='mat@0.05').round(2))

    if 1.0 in args.sigmas:
        plot_matfar(results, 1.0, os.path.join(RESULTS, 'matfar.png'))
    if len(args.sigmas) > 1:
        plot_matsig(summary, 0.05, os.path.join(RESULTS, 'matsig.png'))


# --- P(i+) examples ---

def run_models(data, snapshots):
    """Return {k: (exact P(i+), one-sweep CPP P(i+), exact P(i++))} with
    unknown mu and sigma, using a Normal-Inverse-Gamma prior scaled to the
    data."""
    model = NormalInverseGamma(mu0=np.mean(data), kappa0=1.0,
                               alpha0=1.0, beta0=np.var(data))
    exact = CPP(model, F)
    one = IterativeCPP(model, F, iters=1)
    boc = BOCPD(model, F)
    out = {}
    for k, x in enumerate(data):
        exact.add(x)
        one.add(x)
        boc.add(x)
        if k in snapshots:
            assert np.allclose(exact.p()[1:], boc.p()[1:], atol=1e-8)
            out[k] = (exact.p(), one.p(), exact.pp())
    return out


def plot_example(name, data, xs, changes, snapshots, title):
    """Plot the series, and at each snapshot the exact P(i+), the
    one-sweep CPP estimate, and the exact P(i++)."""
    results = run_models(data, snapshots)

    nrows = 1 + len(snapshots)
    fig, axes = plt.subplots(nrows, 1, figsize=(7, 1.9 + 1.7 * nrows),
                             sharex=True,
                             gridspec_kw=dict(height_ratios=[1.6] + [1] * len(snapshots)))
    ax = axes[0]
    ax.plot(xs, data, color=INK, linewidth=1, marker='o', markersize=2.5)
    for c in changes:
        for a in axes:
            a.axvline(xs[c], color=MUTED, linewidth=1, linestyle=':')
    ax.set_ylabel('value')
    ax.set_title(title, color=INK, fontsize=11, loc='left')
    style_axes(ax)

    rows = []
    for ax, k in zip(axes[1:], snapshots):
        p, p1, pp = results[k]
        i = np.arange(len(p))
        ax.plot(xs[i], p, color=STYLE['bocpd']['color'], linewidth=2,
                label='P(i+), exact (BOCPD = converged CPP)')
        ax.plot(xs[i], p1, color=STYLE['cpp1']['color'], linewidth=1.5,
                linestyle='--', label='P(i+), CPP with 1 sweep per step')
        ax.plot(xs[i], pp, color=STYLE['glr']['color'], linewidth=2,
                label='P(i++), second-to-last change (exact)')
        ax.axvline(xs[k], color=INK, linewidth=1)
        ax.text(0.01, 0.92, f'after {k + 1} points', transform=ax.transAxes,
                color=INK, fontsize=9, va='top')
        ax.set_ylabel('probability')
        style_axes(ax)
        for j in i:
            rows.append(dict(snapshot=k, i=j, x=xs[j], p_exact=p[j],
                             p_cpp_1sweep=p1[j], pp_exact=pp[j]))

    handles, labels = axes[1].get_legend_handles_labels()
    fig.legend(handles, labels, frameon=False, fontsize=8, labelcolor=INK,
               loc='lower center', ncol=2)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(os.path.join(RESULTS, f'{name}.png'), dpi=150)
    plt.close(fig)
    pd.DataFrame(rows).to_csv(os.path.join(RESULTS, f'{name}.csv'), index=False)


def examples(args):
    rng = np.random.default_rng(args.seed)

    # Figure 1 of the paper: means -0.5, 0.5, 0.0, 50 points each, sigma 1
    data = np.concatenate([rng.normal(mu, 1.0, 50) for mu in [-0.5, 0.5, 0.0]])
    xs = np.arange(len(data))
    plot_example('example', data, xs, [50, 100], [149],
                 'Synthetic: mean shifts at t = 50 and 100')

    # Figure 2: Nile flow at Aswan, snapshots after 33, 66, 99 years
    nile = np.array([float(line) for line in open(NILE) if line.strip()])
    years = np.arange(1871, 1871 + len(nile))
    plot_example('nile', nile, years, [1898 - 1871], [33, 66, 99],
                 'Nile annual flow at Aswan, 1871–1970')

    # Figure 3: change in mean, then change in variance, 40 points each
    data = np.concatenate([rng.normal(1.0, 1.0, 40), rng.normal(0.0, 1.0, 40),
                           rng.normal(0.0, 0.5, 40)])
    xs = np.arange(len(data))
    plot_example('var', data, xs, [40, 80], [119],
                 'Synthetic: change in mean at 40, in variance at 80')


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('examples')
    p.add_argument('--seed', type=int, default=1)

    p = sub.add_parser('detection')
    p.add_argument('--runs', type=int, default=1000)
    p.add_argument('--sigmas', type=float, nargs='+',
                   default=[0.25, 0.5, 0.75, 1.0, 1.25, 1.5])
    p.add_argument('--algs', nargs='+',
                   default=['cpp1', 'bocpd', 'glr', 'bocpd_tau3'])
    p.add_argument('--processes', type=int, default=os.cpu_count())

    args = parser.parse_args()
    os.makedirs(RESULTS, exist_ok=True)
    if args.cmd == 'examples':
        examples(args)
    else:
        detection(args)


if __name__ == '__main__':
    main()
