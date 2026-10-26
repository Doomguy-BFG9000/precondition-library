# Pre-registration: dispatch on real lock-file merges

- **Registered:** 2026-10-26, by the commit that adds this file (#298, part of #294).
- **Bound by code.** `bench.preregistration` pins this file's SHA-256. The real-merge measurement
  calls `require("real-merges")`, which refuses to run if this file is missing, uncommitted, or
  different from the pinned text.
- **Before registration:** no real-merge case was built, labelled or scored. The only real-merge
  data looked at is the feasibility count in [§11](#11-feasibility-done-before-registration),
  which reads no maintainer resolution and runs no arm.
- **Public registry:** posting this text to OSF is the repository owner's decision. If it is
  posted, the OSF identifier is added under [Amendments](#amendments) before any case is scored.

## 1. Question

Every state measured so far was built by this project's injectors and labelled by its own rules
(#294). ADR-0047 showed that, on those labels, a dispatcher that reads the state without running
any compiled program matches arm 3. This study asks the question again on states and labels the
project did not make: merge commits in public repositories whose two sides conflicted in a lock
file, labelled by what the maintainer committed.

## 2. Hypotheses

- **H1 (primary).** At matched coverage, arm 3 (precondition dispatch) mis-fires less than arm 2
  (lexical text similarity, as in Figure 1).
- **H2 (secondary).** At matched coverage, arm 3 mis-fires less than the state-reading control
  (ADR-0047).

Each null is no difference. Only H2 can license a sentence saying that *executing* preconditions,
rather than reading the state, is what wins (ADR-0047). If H1 holds and H2 does not, the result is
reported as "a dispatcher that reads the state beats similarity on real merges", not as a win for
executability.

## 3. Cases

### 3.1 Repositories

Repositories are taken from the lists below, in order, and nowhere else. A repository is pinned
at the tip of its default branch on the day it is first mined; the tip's SHA is recorded in the
dataset manifest, and history is read up to that commit only.

**Pilot (stage A):**

1. [`sharkdp/bat`](https://github.com/sharkdp/bat)
2. [`sharkdp/fd`](https://github.com/sharkdp/fd)
3. [`alacritty/alacritty`](https://github.com/alacritty/alacritty)
4. [`python-poetry/poetry`](https://github.com/python-poetry/poetry)
5. [`helix-editor/helix`](https://github.com/helix-editor/helix)
6. [`tauri-apps/tauri`](https://github.com/tauri-apps/tauri)

**Confirmatory (stage B), in order:**

1. [`phpmyadmin/phpmyadmin`](https://github.com/phpmyadmin/phpmyadmin)
2. [`jupyterlab/jupyterlab`](https://github.com/jupyterlab/jupyterlab)
3. [`babel/babel`](https://github.com/babel/babel)
4. [`nextcloud/server`](https://github.com/nextcloud/server)
5. [`jupyter/notebook`](https://github.com/jupyter/notebook)
6. [`voila-dashboards/voila`](https://github.com/voila-dashboards/voila)
7. [`composer/composer`](https://github.com/composer/composer)
8. [`nushell/nushell`](https://github.com/nushell/nushell)
9. [`rust-lang/cargo`](https://github.com/rust-lang/cargo)
10. [`servo/servo`](https://github.com/servo/servo)

The first three were counted in §11. The rest were named before any count, and have not been
counted.

Every listed repository is public, and its licence is recorded in the manifest. Only SHAs and
derived labels are committed, never the repositories' content (as ADR-0043 does).

### 3.2 A positive case

A merge commit `M` reachable from the pinned tip, such that all of these hold:

1. `M` has exactly two parents. `P1`, the first, is the local side. `P2`, the second, is upstream.
2. `P1` and `P2` have exactly one merge base, `B`.
3. `git merge-tree --write-tree --name-only -z P1 P2` exits 1.
4. At least one conflicted path is a lock file.

A **lock file** is a path whose final component is one of `package-lock.json`,
`npm-shrinkwrap.json`, `yarn.lock`, `pnpm-lock.yaml`, `Cargo.lock`, `poetry.lock`, `Pipfile.lock`,
`uv.lock`, `Gemfile.lock` or `composer.lock`.

A case whose conflict also includes files that are not lock files stays in. No intent here
resolves those files, so §4 gives it no acceptable resolution.

### 3.3 A negative case

A merge commit meeting conditions 1 and 2 where both sides changed the same lock file since `B`
and `git merge-tree` exits 0, so no conflict occurs. Per repository, the negatives are the most
recent such merges by committer date, as many as that repository has positives, or all of them if
it has fewer. On a negative the correct decision is not to fire.

### 3.4 The state

For each case, a checkout of `P1` on a branch that tracks upstream's default branch, whose
remote-tracking ref is at `P2`, with the merge base reachable. It is built by the real-host
machinery (`sandbox.fetch_real_host`, ADR-0043) and observed by `StateFingerprint.observe`,
unchanged. Each case is one pair, with the
lock-file intent `sync_through_a_conflicting_lockfile` and its uninformed request, phrased as
`INTENT.task_text(i)` for the case's index `i` in the manifest.

### 3.5 Exclusions

Only mechanical exclusions are allowed. Each is counted per repository and reported:

- a merge with more than one merge base (criss-cross);
- a parent that cannot be fetched;
- a conflict involving a submodule or a binary file;
- a state whose checkout cannot be built.

**Nothing else is dropped.** In particular, a case that none of this project's resolutions can
express stays in the denominator, with an empty acceptable set (§4).

## 4. The label: what the maintainer committed

For each conflicted lock file `f`, read four versions as multisets of lines: `B_f`, `L_f` (at
`P1`), `U_f` (at `P2`) and `M_f` (at `M`). Write `+` for multiset sum and `-` for multiset
difference. Each of the lock-file intent's two resolutions produces, by its own rationale:

| resolution | produces |
| --- | --- |
| `take_upstream` | `U_f + (L_f - B_f)`: upstream's file, plus the lines the local side added |
| `keep_local` | `L_f + (U_f - B_f)`: the local file, plus the lines upstream added |

A resolution is **acceptable** on a case if what it produces equals `M_f` for every conflicted
lock file, and every conflicted path is a lock file. The acceptable set may be empty: for example,
when the maintainer regenerated the file. A fire is right if the fired resolution is in the
acceptable set. A fire from a program of another intent is wrong, and so is any fire on a
negative.

The maintainer's commit is the label, not the intent's rule. The rule's own label
(`INTENT.correct_variant` on the observed state) is recorded beside it, and every case where the
two disagree is listed one by one.

Each positive is also put in exactly one descriptive class, using the first that matches:

1. **took local** (`M_f = L_f` for every `f`);
2. **took upstream** (`M_f = U_f`);
3. **matches `take_upstream`**;
4. **matches `keep_local`**;
5. **regenerated** (some line of `M_f` appears in none of `B_f`, `L_f` or `U_f`);
6. **other**.

These classes are reported, not tested.

## 5. Arms and controls, frozen

None of these is refit, retuned or rebuilt on real-merge data.

- **Arm 3.** Each committed library,
  `results/replicates-2026-10-05/run-{11,12,13}/library-two-sided`, is one replicate. It fires the
  first program whose preconditions accept the state, as Figure 1 and `bench.consequences` do.
- **Arm 2.** Lexical similarity between the request and each library's program descriptions, as
  in Figure 1, scored per replicate. The embedding and reranker scorers are reported as well, but
  are not in any hypothesis.
- **State-reading control.** `bench.state_classifier`, fit exactly as committed on the build's 56
  states (ADR-0047). Its score is the leaf's class probability.
- **LLM state judge (#295).** It runs only if the owner provides a key, and is reported as a
  control outside any hypothesis.

## 6. Metric

**Mismatch at matched coverage**, computed by `bench.coverage`. Each arm's per-fire mismatch is
read at the point of its curve nearest arm 3's coverage (`matched_comparison`), separately per
replicate. Its interval is Wilson's.

## 7. Analysis

The tests run on stage B only. Stage A is reported descriptively and never pooled into stage B.

- **H1.** `d = mismatch(arm 2) - mismatch(arm 3)` at matched coverage. The interval is a 95%
  cluster bootstrap that resamples repositories (`BOOTSTRAP_RESAMPLES` = 2000, `BOOTSTRAP_SEED` =
  0). H1 is supported if the interval's lower bound is above 0 **in every replicate**.
- **Paired check.** An exact two-sided McNemar test, α = 0.05, on the cases both arms fire on at
  the matched threshold. It is reported beside each interval and does not overrule it.
- **H2.** The same, with the state-reading control in arm 2's place. It is labelled secondary,
  with no correction for multiplicity.

## 8. Sample size and power

The aim is to detect a mismatch difference of 0.20 at a base rate of 0.5, with two-sided α = 0.05
and power 0.80. By the formula of `bench.coverage.detectable_difference`, that needs 99 fires per
arm. Assuming an intraclass correlation of 0.05 within a repository and about 10 fires per
repository, the design effect is 1.45, so **144 arm-3 fires**. The exact McNemar test then needs
about 60 jointly fired cases for power 0.80 when the discordant rates are 0.25 and 0.05.

Stage B's size is set from stage A:

- **Positives.** With `c` the share of stage A positives arm 3 fires on, pooled over replicates,
  stage B mines repositories in list order until it has `ceil(144 / c)` positives and at least 8
  repositories with a positive.
- **Concentration.** No single repository may contribute more than 25% of the positives. Beyond
  that share, a repository's most recent positives are kept.
- **Short list.** If the list runs out first, stage B is reported as **underpowered**: every
  figure is given, but no hypothesis is called supported or refuted.

## 9. Decision rules and what would falsify the claim

These are applied in order, per replicate.

1. **Applicability.** If arm 3 fires on fewer than 20 of a replicate's positives, H1 and H2 are not
   tested in that replicate. If this happens in every replicate, the finding is that **the
   library does not transfer to real lock files**. That falsifies the claim that it dispatches
   them at all, and is reported as the primary result.
2. **Arm 3's own reliability.** If the lower bound of arm 3's Wilson interval for mismatch exceeds
   0.10 in any replicate, "arm 3 rarely mis-fires" is falsified on real merges.
3. **Against similarity.** If H1's lower bound is at or below 0 in any replicate, H1 is not
   supported.
4. **Against reading the state.** If H2's lower bound is at or below 0, the state-reading control
   matches arm 3 on real merges. That falsifies the claim that executability adds anything there,
   and ADR-0047's wording stands.

Expressibility, the share of positives with a non-empty acceptable set, is reported in every
case. It is not a gate.

## 10. Reporting

`results/real-merges-<date>/` holds the following:

- the manifest: repository URL, pinned tip, licence, and each case's `M`, `P1`, `P2` and `B`;
- per-repository counts of positives, negatives and exclusions, with each exclusion's reason;
- the descriptive classes;
- the table of rule against maintainer, case by case;
- each arm's figures per replicate and stage;
- the decisions under §9, in order.

Anything done differently from this document is listed as a deviation, with its reason.

## 11. Feasibility, done before registration

To set §8, merges were counted in blobless clones, by `git rev-list --merges` and `git merge-tree`
(`real-merges-feasibility.py`, beside this file). They never read a merge commit's own tree,
so no maintainer resolution, and they ran no arm. They are the number of two-parent merges, those where both sides
changed the same lock file, and those whose conflict includes a lock file:

| repository | two-parent merges | both sides changed a lock file | conflict includes a lock file | listed in |
| --- | ---: | ---: | ---: | --- |
| `sharkdp/bat` | 543 | 24 | 5 | stage A |
| `sharkdp/fd` | 451 | 145 | 3 | stage A |
| `BurntSushi/ripgrep` | 62 | 0 | 0 | not listed (no positive) |
| `alacritty/alacritty` | 39 | 2 | 1 | stage A |
| `python-poetry/poetry` | 131 | 8 | 6 | stage A |
| `jestjs/jest` | 259 | 0 | 0 | not listed (no positive) |
| `babel/babel` | 1396 | 18 | 12 | stage B |
| `phpmyadmin/phpmyadmin` | 16670 | 65 | 44 | stage B |
| `mozilla/pdf.js` | 10070 | 31 | 0 | not listed (no positive) |
| `jupyterlab/jupyterlab` | 4699 | 64 | 19 | stage B |
| `mastodon/mastodon` | 426 | 1 | 0 | not listed (no positive) |
| `owncloud/core` | 14051 | 98 | 0 | not listed (no positive) |
| `tauri-apps/tauri` | 57 | 19 | 14 | stage A |
| `helix-editor/helix` | 73 | 14 | 1 | stage A |
| **total** | 48927 | 489 | **105** | |

These counts were taken at each default branch's tip on 2026-10-26, before §3.2's merge-base
condition and §3.5's exclusions were applied, so a stage's positives can be fewer. Repositories with
no lock-file conflict are not listed in either stage. Stage A has 30 candidates, "tens of merges" as
#296 asks. Stage B's counted repositories hold 75, and the 25% cap in §8 limits phpMyAdmin's share.
So stage B is underpowered unless the uncounted repositories yield, and §8 says how that is
reported.

## Amendments

None.
