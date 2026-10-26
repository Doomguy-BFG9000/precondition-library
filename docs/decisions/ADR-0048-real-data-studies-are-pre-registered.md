# ADR-0048 — A study on data this project did not make is pre-registered, and bound by code

- **Status:** accepted
- **Date:** 2026-10-26
- **Supersedes:** nothing.
- **Deciders:** repository owner (#294, "open all the issues, and reconstruct everything").

## Context

The real-merge dataset (#296) is the first one whose labels this project did not write: they are
whatever the maintainers committed. It is only a test of the project's claim if the analysis is
fixed before any of it is seen. So the hypotheses, the unit, the label, the metric, the test, the
sample, the exclusions and what would falsify the claim must all be fixed first (#298).

A registration is only as strong as what stops it being edited after the fact. A date in the text
proves nothing.

## Decision

1. **`docs/preregistration/real-merges.md` registers the real-merge comparison.**
   - H1: arm 3 against lexical arm 2. H2: arm 3 against the state-reading control (ADR-0047).
   - The label is the maintainer's merged lock file, compared as line multisets with what each
     resolution produces. A case no resolution reproduces stays in, with an empty acceptable set.
   - A pilot stage sizes a confirmatory stage. The two are never pooled.
   - Four ordered decision rules: applicability, arm 3's reliability, H1, H2.
2. **`bench.preregistration` pins the registration's SHA-256.** `require(name)` refuses unless the
   document exists, matches the pin, is committed and has no uncommitted change. The real-merge
   measurement (#296) calls it before building any case.
3. **An amendment before measuring is a commit that changes both the document and the pin.** A
   change after measuring is a deviation, reported with the results, not written into the
   registration.
4. **The feasibility count is committed beside it.** That count is the only real-merge data seen
   before registering, and it reads no merge commit's tree.

## What the feasibility count found

Across 14 public repositories, 105 merges had a conflict that included a lock file. Six
repositories give the pilot 30 candidates. The confirmatory list's three counted repositories hold
75, and phpMyAdmin's share is capped at 25%. The registration's power target is 144 arm-3 fires,
so the confirmatory stage is likely underpowered unless the uncounted repositories yield. The
registration says how an underpowered stage is reported: every figure, and no hypothesis called
supported or refuted.

## Consequences

**Accepted:**
- The lock-file intent's resolutions are line operations on a lock-shaped file. On real lock
  files, the likeliest outcome is that the library hardly fires. The registration makes that a
  reported finding (rule 1, "does not transfer") rather than a reason to change the study.
- Posting to a public registry such as OSF is the owner's call. Until then, the commit is the
  only timestamp.

**Gained:** the first comparison whose answer this project cannot have written into its labels.

**New obligations:**
- No real-merge figure is produced except through code that calls `require("real-merges")`.
- The results directory lists every deviation.

## Alternatives rejected

| Alternative | Why rejected |
| --- | --- |
| Registration as a document only | Nothing would stop an edit after seeing results; the commit date proves when it was written, not that it was followed. |
| Label real merges by the intent's rule | That is the circularity #294 exists to break. |
| Drop cases no resolution can express | It would hide exactly what the real data could show; they stay in the denominator. |
| Size the confirmatory stage by a guess | Arm 3's coverage on real lock files is unknown; the pilot measures it and a pre-stated formula uses it. |

## What would reverse this decision

A registered study shown to be untestable as written: for example, a label definition that no
real case can meet. If that happens, the registration is amended before measuring, as decision 3
allows.
