# ChangePoint Project Board

Numbered tasks for tracking work. Each task has a permanent number; add new tasks at the end. Update status as work progresses.

**Status values:** `Pending`, `In progress`, `DONE`

### Current focus (2026-10-24)

Turn this folder into a public repo that updates the 2008 arXiv paper (0812.1237). It should send readers to BOCPD (Adams & MacKay 2007) and give them a correct, tested implementation. The repo acknowledges parallel work; it does not claim priority or novelty. The 2026 revisit found that the corrected algorithm computes the same posterior as BOCPD, more slowly. Its only extra output is the posterior over the second-to-last changepoint. Details are in `summary.md`, "Revisited in 2026".

### Getting started

```bash
conda env create -f environment.yml     # once; creates the ChangePoint env
conda activate ChangePoint
cd compare
python -m pytest test_cpp.py            # 7 tests, a few seconds
python experiments.py examples          # results/example.png, nile.png, var.png
python experiments.py detection         # results/matfar.png, matsig.png, CSVs; about a minute on 12 cores
```

How the folder fits together:

- `compare/` is the 2026 code, all Python 3:
  - `bocpd.py`: BOCPD plus the conjugate segment models (`log_ml`, `logpred`, `update`)
  - `cpp.py`: BOCPD plus P(i⁺⁺) from stored past posteriors
  - `cpp_iterative.py`: the paper's system of equations, corrected
  - `glr.py`: GLR, ported from `Change4.py`
- `code/` is the 2006–2008 Python 2 code. It doesn't run as-is: it imports `Gui` and `Hist` from `/home/downey/python`. `Change4.py` is the version behind the paper, and `notes.txt` records the commands that produced each result file.
- `paper/paper.tex` is the source of the 2008 version, and `paper/paper.md` its Markdown conversion.
- `papers/` holds third-party PDFs. **They must not go into the public repo** (Task 2).

### Traps

- `conda run` doesn't forward stdin, so `conda run -n ChangePoint python - <<EOF` silently runs nothing. Write a script file instead.
- `python experiments.py detection --sigmas 1.0` overwrites `results/detection*.csv` and `matfar.png` with partial results. The full run is deterministic, so rerunning it restores the published numbers exactly.
- In `cpp.py` and `bocpd.py`, index `i` means "x[i] is the first point of the new segment", and slot 0 means "no change". The original code was inconsistent about this.
- A run-length posterior with pruning still grows during a long stable segment. The number of live hypotheses tracks the length of the current regime, not a constant.

---

## Task 1: Decide the license and repo name

**Status:** DONE 2026-10-24

**Decided (Allen, 2026-10-24):** MIT for the code; CC BY 4.0 for the text and figures (paper, summary, README, results).

Repo name: `ChangePoint`.

- [x] Add `LICENSE` (MIT) and `LICENSE-text` (CC BY 4.0), and say in the README which applies to what

---

## Task 2: Prepare the repo locally

**Status:** DONE 2026-10-24 (first commit `8f5a2ef`; branch renamed to `main`)

**Context:** The folder isn't under git yet. Several things must stay out of the public repo:
- **Copyrighted papers:** all of `papers/` (journal PDFs and the Basseville & Nikiforov book) and `code/simulation.pdf` (Perros's textbook).
- **Generated files:** about 16 MB in `code/` (`chi2`, `invs`, `sic2`, `sums` and their `.cdf` files).
- **Editor and build leftovers:** Emacs backups (`*~`, `#notes.txt#`), the dangling `.#notes.txt` lock link, `*.pyc`, and LaTeX build files.

- [x] `.gitignore` for all of the above (214 files, 3.3 MB to be tracked)
- [x] `REFERENCES.md`: "use these instead", plus the collected papers the 2008 paper cites (7 of 25, per Allen 2026-10-24); DOIs, volumes and pages checked against Crossref
- [x] `paper/sigmetrics/` was a submission only, never published, so it can be included (Allen, 2026-10-24)
- [x] Include everything else: the original code, `notes.txt`, and the paper sources and PDFs, minus build files and generated data (Allen, 2026-10-24)
- [x] `git init` (no commits yet)
- [x] Allen reviewed and revised the README, summary, and REFERENCES; first commit `8f5a2ef`

---

## Task 3: Rewrite the README for outside readers

**Status:** DONE 2026-10-24 (pending Allen's review)

**Context:** The current README is an inventory written for Allen. Visitors will mostly arrive from the arXiv paper or allendowney.com.

- [x] Open with: "If you came here from the 2008 paper, use BOCPD", with the reason in two sentences and links to the BOCPD paper and maintained implementations
- [x] Say what the repo contains: the corrected algorithm, the brute-force tests showing it equals BOCPD, and the reproduced experiments with their figures
- [x] Present `compare/` as a teaching and verification aid, not a library
- [x] Keep the inventory, shortened, lower in the README

---

## Task 4: Reword the acknowledgment and record conclusions in `summary.md`

**Status:** DONE 2026-10-24 (pending Allen's review)

**Context:** The "Priority" paragraph in `summary.md` says BOCPD was posted "without citing it". That reads as a complaint, which isn't the intent.

- [x] Rewrite it as a plain acknowledgment of parallel work: the 2006 draft, Fearnhead (2006), Adams & MacKay (2007), Fearnhead & Liu (2007); point readers to the latter three
- [x] Add a "Conclusions (2026)" section with the verdict: CPP offers nothing beyond BOCPD unless the second-to-last changepoint matters. Note that the detection advantage over GLR is the kind theory leads one to expect for a Bayesian detector whose prior on the change time matches the simulation (Shiryaev's problem), and not something specific to CPP.
- [x] "I haven't seen that in the BOCPD literature" was only said in conversation; nothing to remove

---

## Task 5: Create the GitHub repo and push

**Status:** DONE 2026-10-24 — public at https://github.com/AllenDowney/ChangePoint (Allen approved)

- [x] Create `AllenDowney/ChangePoint`; set the description and topics (changepoint, bayesian, bocpd, time-series)
- [x] Push; GitHub detects the MIT license, and the README figure is served
- [x] Allen checked in a browser that the math renders in `paper/paper.md` and `summary.md` (GitHub renders it client-side, so it can't be checked from the API)

---

## Task 6: Post arXiv v2 of 0812.1237

**Status:** In progress — submitted 2026-10-24; waiting for arXiv to announce v2

**Decided (Allen, 2026-10-24):** no effort on fixing the paper. v2 only acknowledges that it has been superseded and points to BOCPD and the repo. The known problems are documented in the repo, not in the paper.

**Context:** v1 stays available, but readers usually land on the latest version.

- [x] Comments field and the first line of the abstract: superseded; see Adams & MacKay (2007) and Fearnhead (2006); code at the repo URL. Text in `paper/arxiv/v2_submission.md` (abstract 1,289 of 1,920 characters)
- [x] The same notice at the top of the paper (`paper/arxiv/paper.tex`); the body is otherwise unchanged
- [x] Keep the title "A novel changepoint detection algorithm" (Allen, 2026-10-24)
- [x] Build and check the PDF: builds clean with `latex`, 12 pages
- [x] Allen submitted the replacement on arXiv (2026-10-24), using `paper/arxiv/downey-changepoint-arxiv-v2.zip` and the text in `v2_notice.txt` / `v2_submission.md`
- [ ] Check that v2 is announced at https://arxiv.org/abs/0812.1237 and that the notice shows on the abstract page and in the PDF

Known problems, for the repo's documentation (not the paper):
1. **The novelty claims are wrong.** "There are no previous algorithms for computing P(i⁺)" and the conclusion's "novel contribution" are incorrect. The BOCPD run-length posterior is exactly P(i⁺) (Adams & MacKay 2007), and exact recursions appear in Fearnhead (2006).
2. **The likelihood approximation uses the wrong distribution.** It draws μ (and σ) from the *posterior* given the same data, not the prior. That uses the data twice and favors changepoints. The paper also says the integral is impractical; with a proper conjugate prior it has a closed form. A proper prior is required anyway: with the improper prior, the comparison of "no change" against "one change" is undefined.
3. **The code doesn't match the paper's equations.** The prior on "no change" is never applied. The two terms of the P(i⁺) equation refer to changepoints one step apart. P_k includes x_k. Every segment, not just the first, is given the known mean μ₀. An undocumented `--fudge=0.5` scales f.
4. **One iteration per step is not usually sufficient.** Full convergence takes a median of about 60 sweeps. With one sweep, P(i⁺) is off by up to 0.08 (P(change) much less). No iteration is needed at all: P(i⁺) has a direct O(n) recursion, and P(i⁺⁺) = Σ_k P(k⁺)·P_k(i⁺).
5. **The evaluation scoring disagrees with the text.** The code counted an alarm on the first post-change point as a false alarm and measured delay as k − n. Corrected results at σ = 1, α = 0.05: exact Bayesian 10.6, GLR 11.2 (the paper reported 9.7 and 10.7). The qualitative conclusion holds, with the crossover near σ ≈ 0.75. The advantage is the kind theory leads one to expect for a Bayesian detector whose prior on the change time matches the simulation (Shiryaev's problem), so it isn't specific to this algorithm.
6. **Figures 1–5 came from the buggy implementation.** Corrected versions are in the repo.
7. **The variance-change instability (Section 3.7)** is probably a symptom of the plug-in likelihood on short segments. Proper marginal likelihoods should largely remove it, though this hasn't been tested yet.

---

## Task 7: Update allendowney.com/research/changepoint

**Status:** DONE 2026-10-24

**Context:** The page described the work as current, linked the 2008 PDF and slides, and said "Software: Coming soon". Its source is in `~/AllenDowneyCom`, which is deploy-only: commit there, then deploy.

- [x] Add a notice at the top: superseded by BOCPD, with links to the repo and arXiv. Source is `~/AllenDowneyCom/allendowney/research/changepoint/index.html`; the change went into that repo's commit `354c039`, made by a concurrent session
- [x] Replace "Coming soon" with the repo link
- [x] Deployed 2026-10-24 (`scripts/deploy_ad.sh research/changepoint/index.html` in `~/AllenDowneyCom`); live page checked

---

## Task 8: Blog post on *Probably Overthinking It* (optional)

**Status:** Pending

**Context:** The story: a 2006 draft; BOCPD in 2007; the bugs found in 2026; the corrected recursion turning out to be exactly BOCPD. Figures and tests already exist. It could help readers find BOCPD, which is the point of the whole effort.

- [ ] Allen decides after the repo is public (decided 2026-10-24: later)
- [ ] Find related posts (`related-articles` skill)

---

## Task 9: Changepoints that look like autocorrelation (optional research)

**Status:** Pending

**Context:** The paper's open question 4, independent of CPP: if a series has abrupt changes but no correlation within segments, it looks autocorrelated when the changes are ignored. Segment real measurement data with BOCPD, then check whether the autocorrelation survives within segments.

- [ ] Find a dataset (network measurements, or something else with suspected regime changes)
- [ ] Compare autocorrelation before and after segmentation; simulate the null case to calibrate

---

## Task 10: Error bars on the detection results (optional)

**Status:** Pending

**Context:** `summary.md` warns that differences of a few tenths in mean delay may be noise. Bootstrapping over trials would settle which differences are real, especially the GLR crossover.

- [ ] Bootstrap the interpolated mean delay at α = 0.05 per method and σ; add intervals to `matsig.png` and `detection_summary.csv`
