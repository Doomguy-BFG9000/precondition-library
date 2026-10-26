# ADR-0049 — The real-merge study is amended before stage B: clean merges are labelled by the maintainer

- **Status:** accepted
- **Date:** 2026-10-26
- **Supersedes:** the real-merge registration's §3.3 rule that any fire on a clean merge is wrong,
  and §8's sizing formula, for stage B only (Amendment 1). ADR-0048 decision 3 is the rule this
  follows.
- **Deciders:** repository owner ("Which you think is the best pick?"); the amendment is the one
  recommended.

## Context

Stage A (`results/real-merges-2026-10-26/stage-A/`) found no lock-file conflict expressible:
none of 30 maintainer merges is either resolution the intent defines. Under the registered rule
that any fire on a clean merge is wrong, every fire by every dispatcher was wrong, and H1 and H2
had no answer.

That rule was a design mistake. On every one of stage A's 14 clean merges, the maintainer's merge
commit has exactly the tree `git merge-tree` writes for its parents. Firing `merge` reproduces what
the maintainer did, and arm 3 fired it on 38 of the 42 clean decisions.

## Decision

Amendment 1, appended to `docs/preregistration/real-merges.md`, with its pin updated:

1. **A clean case accepts `merge`** where the merge commit's tree is the clean merge's.
   Conflicted cases are labelled as before.
2. **H3, a refusal hypothesis.** On inexpressible conflicts, arm 3 fires less often than the
   state-reading control.
3. **Stage B is 247 cases**, from stage A's `c` = 77/132, with the 25% cap applied to cases.
4. **Eight more repositories** are named, uncounted.
5. **Stage A is exploratory under the new labels.** It motivated the amendment, so it tests
   nothing.

## What stage A shows under the new labels (exploratory)

| library | arm 3 fires, wrong | H3 statistic |
| --- | --- | ---: |
| run 11 | 19, 8 | +0.83 |
| run 12 | 14, **0** | **+1.00** |
| run 13 | 44, 31 | 0.00 |

The state-reading control fires on all 30 conflicts and on no clean merge.

Run 12's library refuses every conflict and merges every clean case. Run 13's fires `keep_local`
on every conflict, as the control does. Executable checks *can* refuse what they do not fit;
whether a given library's checks do depends on the build. That is a hypothesis for stage B, not a
finding.

## Consequences

**Accepted:**
- The amendment was written with stage A's results in view. Only stage B's fresh cases can
  support or refute anything, and the README says so beside every stage-A figure.
- The original text's figures for stage A stay committed, unchanged.

**Gained:** a test that can separate the dispatchers on labels this project did not write. A
clean merge has a right answer; an inexpressible conflict has only refusal.

**New obligations:** stage B is reported against both readings of rule 1, and every deviation is
listed.

## Alternatives rejected

| Alternative | Why rejected |
| --- | --- |
| Run stage B as originally registered | With nothing expressible and every clean fire scored wrong, no hypothesis can be answered; stage B would cost hours to re-confirm stage A. |
| Add a regenerating resolution | No library has a program that regenerates, so every arm would still fail. It needs ecosystem toolchains (#297) and a build. |
| Re-score stage A as the test | It motivated the amendment, so it cannot test it. |

## What would reverse this decision

Clean merges whose merge tree is not the one `git merge-tree` writes. That would mean the
maintainer did something a clean `merge` does not reproduce. The label already handles such a
case ("clean merge changed"), so the amendment would stand but the clean side would carry less.
