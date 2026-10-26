# Real lock-file merges, stage A (pilot), 2026-10-26 (#296)

This is the first measurement on states and labels this project did not make. The states are
merge commits in six public repositories whose two sides conflicted in a lock file. The label is
what the maintainer committed. The study was registered before any case was built
(`docs/preregistration/real-merges.md`, ADR-0048), and the code refuses to run without that
registration. Stage A is the pilot: by §7 it is reported descriptively and tests nothing.

```bash
python -m precondition_library.bench.real_merges --out results/real-merges-2026-10-26/stage-A
```

- `manifest.json`: each repository's pinned tip, default branch, licence and counts, and each
  case's merge, parents and base. It holds SHAs and paths only, never content.
- `labels.jsonl`: each case's acceptable resolutions and descriptive class (§4).
- `decisions.jsonl`: each case's arm 3 and arm 2 decisions per committed library, the control's
  decision, and the intent's own rule label.
- `report.json` and `summary.txt`: the figures.

## The cases

| repository | tip | merges | positives | negatives | excluded |
| --- | --- | ---: | ---: | ---: | ---: |
| `sharkdp/bat` | `a9aa73d2` | 543 | 5 | 5 | 0 |
| `sharkdp/fd` | `c44735ec` | 451 | 3 | 3 | 0 |
| `alacritty/alacritty` | `54214706` | 39 | 1 | 1 | 0 |
| `python-poetry/poetry` | `1fe5e0a5` | 131 | 6 | 1 | 0 |
| `helix-editor/helix` | `ba40e547` | 73 | 1 | 1 | 0 |
| `tauri-apps/tauri` | `0ed29984` | 57 | 14 | 3 | 0 |
| **total** | | 1294 | **30** | **14** | 0 |

The positives match the feasibility count (§11) repository by repository. No case was excluded.
poetry has only one clean merge in which both sides changed the lock file, so it contributes one
negative (§3.3: "or all of them if it has fewer").

## What the maintainers did

| class (§4) | positives |
| --- | ---: |
| regenerated: the merged file has lines in none of the three inputs | 18 |
| other | 8 |
| took local | 3 |
| took upstream | 1 |
| matches `take_upstream` | 0 |
| matches `keep_local` | 0 |

**Expressible: 0 of 30** (95% Wilson interval 0 to 0.114). On no positive does either
resolution the lock-file intent defines reproduce the maintainer's lock files. The commonest
outcome, 18 of 30, is a regenerated file. That is the resolution `lockfile_conflict.py`'s own
docstring calls right ("regenerate it with the ecosystem's own tool"), but the intent offers no
such resolution, only the two line unions. Taking one side whole (4 cases) is not one of the
intent's resolutions either.

The labels were recomputed by an independent script, using `git show` and sorted lists rather
than `bench.real_merges`. It agreed on all 30 acceptable sets and classes.

**The intent's rule and the maintainer disagree on 4 positives.** On those, the rule labels a
resolution and the maintainer did something else:

| case | repository | rule | maintainer's class |
| --- | --- | --- | --- |
| 4 | `sharkdp/bat` `da101666` | `take_upstream` | regenerated |
| 12 | `sharkdp/fd` `cdc6a37e` | `take_upstream` | regenerated |
| 25 | `helix-editor/helix` `458b89e2` | `keep_local` | other |
| 40 | `tauri-apps/tauri` `ad91e302` | `take_upstream` | took local, with 16 other files also conflicted |

On the other 26 positives the rule labels nothing: both sides dropped lines of the base, as
version bumps do, so neither of its resolutions is decided.

## What the dispatchers fired

| | arm 3 fires, positives / negatives | arm 3 fired | wrong |
| --- | ---: | --- | ---: |
| run 11's library | 5 / 14 | `take_upstream` ×5; on negatives `merge` ×11, `take_upstream` ×3 | 19 of 19 |
| run 12's library | 0 / 14 | on negatives `merge` ×14 | 14 of 14 |
| run 13's library | 30 / 14 | `keep_local` ×27, `init` ×3; on negatives `merge` ×13, `discard` ×1 | 44 of 44 |
| state-reading control | 30 / 0 | `keep_local` ×27, `take_upstream` ×3 | 30 of 30 |

Arm 2 at arm 3's coverage was wrong on every fire, in every replicate. With nothing expressible,
any fire on a positive is wrong. Only abstaining is right, and no dispatcher abstained on every
positive.

- **Arm 3 depends on the library.** Run 12's library fires on no positive; run 13's fires on all
  30. `c`, the share of positives arm 3 fires on pooled over replicates (§8), is 35/90 = 0.389.
- **The control does not stay within its rule.** It fires on every positive, 26 of which the rule
  leaves unlabelled. Its tree (`results/state-classifier-2026-10-26/trees.txt`) fires whenever a
  file upstream touched would conflict, and picks `keep_local` whenever the local side dropped a
  line. It never tests whether upstream dropped one too, which the rule's `keep_local` requires,
  because in the 56 synthetic states it was fit on the two never occur together. On real lock
  files they do, on 26 of the 30 positives.
- **Arm 3 fires on negatives; the control does not.** A negative here is a diverged state with a
  clean merge. To the `diverged` intent's programs, which read only the environment by design,
  that is their own situation, so they fire `merge`. The registration counts any fire on a
  negative as wrong (§3.3), and it is reported so. This is a cost of the registered design, not
  something the measurement found out about arm 3: Figure 1 never pairs a request with another
  family's state unless that request's rule labels it (ADR-0022), and these negatives do exactly
  that.

## What it shows

- **The lock-file intent does not express what maintainers do.** No positive's merged lock file
  is either of its resolutions, so no dispatcher choosing between them can be right on these
  states. That holds whatever the dispatcher.
- **Arm 3, arm 2 and the control are indistinguishable here: all wrong whenever they fire.** The
  question H1 and H2 ask, which dispatcher mis-fires less, has no answer on states where every
  fire is wrong.
- **Stage B's sizing (§8) needs `ceil(144 / 0.389)` = 371 positives.** The counted confirmatory
  repositories hold 75 (§11), and phpMyAdmin is capped at 25%. Unless the seven uncounted
  repositories yield about 300, stage B will be reported as underpowered.

## What it does not show

- **Anything tested.** Stage A tests nothing (§7). Every figure here is descriptive.
- **That executable preconditions fail on real repositories in general.** This is one intent,
  whose resolutions are line unions of a toy file format. The finding is about that intent's
  action space, not about dispatching by checks.
- **What a regenerating resolution would score.** None exists in the library, and adding one
  would be a change to the study. It could be made only before stage B, as an amendment that
  changes the registration and its pin (ADR-0048 decision 3).

## Under Amendment 1's labels: exploratory, not evidence

Stage A led to the registration's Amendment 1 (ADR-0049). Under it, a clean merge accepts
`merge` where the maintainer's tree is the clean merge's. All 14 clean cases here qualify.
Because this data motivated the amendment, it cannot test it. The figures below are computed
from the committed decisions, with nothing re-dispatched, by the tests stage B will run. They are
marked underpowered, so no verdict is drawn from them (`amendment-1-exploratory/`):

```bash
python -m precondition_library.bench.real_merges --relabel-pilot results/real-merges-2026-10-26/stage-A
```

| library | arm 3 fires / wrong | arm 2 at matched coverage, fires / wrong | H1 (arm 2 − arm 3 mismatch) | H3: fires on the 30 inexpressible conflicts, arm 3 / control |
| --- | --- | --- | --- | --- |
| run 11 | 19 / 8 | 19 / 17 | +0.47, interval [+0.14, +0.63] | 5 / 30 |
| run 12 | 14 / **0** | 14 / 14 | +1.00 | **0 / 30** |
| run 13 | 44 / 31 | 44 / 44 | +0.30, interval [+0.16, +0.50] | 30 / 30 |

The control fires on 30 cases at every operating point, all of them conflicts and all wrong. Its
matched coverage is therefore 30 whatever arm 3's is, so H2 compares unequal coverages here.

- **Run 12's library is what a precondition dispatcher is meant to be.** It refused every real
  lock-file conflict, where no resolution it has is right, and merged every clean case, which is
  what the maintainer did.
- **Run 13's library is not.** It fired `keep_local` on every conflict, exactly as the
  state-reading control did.
- **So on real states the effect depends on the build.** Whether a dispatcher refuses what it does
  not fit depends on which library it is, not on its method alone. Stage B, on cases nobody has
  seen, is where that is tested.
