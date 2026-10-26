"""Mutation testing of the graders (#299 step 1).

The graders define every figure: a fault's `check`, and `recorded_state_intact`, which every
episode must pass first. A grader clause that no test exercises is one a regression can break
silently, and ADR-0045's four defects were exactly such clauses. This module mutates the graders
one small change at a time and runs the tests that read them; a mutant the tests still pass is
**surviving**, and names a clause nothing checks.

It is a targeted runner rather than a general tool such as mutmut, for two reasons. The graders
are a few hundred lines in seven functions, so the mutants can be listed exhaustively. And a
grader test builds real repositories, so running the whole suite per mutant would take days; the
selection below runs only the tests that grade.

**Mutants.** Inside each target function: a comparison flipped (`==`/`!=`, `<`/`>=`, `>`/`<=`,
`in`/`not in`, `is`/`is not`); `and`/`or` swapped; a `not` removed; `True`/`False` swapped; an
integer constant moved by one. Each mutant is written over the module's source, the selection
runs with `-x`, and the original is restored whatever happens.

    python -m precondition_library.bench.grader_mutation --out results/grader-mutation-<date>
"""

from __future__ import annotations

import argparse
import ast
import copy
import json
import subprocess
import sys
import time
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel

REPOSITORY = Path(__file__).resolve().parents[3]

TARGETS: dict[str, tuple[str, ...]] = {
    "src/precondition_library/tasks/invariants.py": (
        "recorded_state_intact",
        "_recorded",
        "_descends_from",
    ),
    "src/precondition_library/tasks/faults/lockfile_conflict.py": ("check",),
    "src/precondition_library/tasks/faults/dirty_tree.py": ("check",),
    "src/precondition_library/tasks/faults/diverged.py": ("check",),
    "src/precondition_library/tasks/faults/branch_renamed.py": ("check",),
    "src/precondition_library/tasks/faults/submodule_moved.py": ("check",),
    "src/precondition_library/tasks/faults/config_renamed.py": ("check",),
}
"""Each grader module, and the functions in it that are mutated."""

SELECTION = (
    "tests/test_checkers_against_gold.py",
    "tests/test_non_destructive_invariants.py",
    "tests/test_sandbox_diverged.py",
    "tests/test_sandbox_dirty_tree.py",
    "tests/test_sandbox_lockfile_conflict.py",
    "tests/test_sandbox_submodule_moved.py",
    "tests/test_sandbox_branch_renamed.py",
    "tests/test_lockfile_intent.py",
    "tests/test_lockfile_states.py",
    "tests/test_dirty_tree_intent.py",
    "tests/test_branch_renamed_intent.py",
    "tests/test_config_renamed_intent.py",
    "tests/test_gold_sweep.py",
    "tests/test_heldout_states.py",
    "tests/test_grader_properties.py",
)
"""The tests that grade: every test file that runs a checker or `recorded_state_intact`."""

_FLIPS: dict[type[ast.cmpop], type[ast.cmpop]] = {
    ast.Eq: ast.NotEq,
    ast.NotEq: ast.Eq,
    ast.Lt: ast.GtE,
    ast.GtE: ast.Lt,
    ast.Gt: ast.LtE,
    ast.LtE: ast.Gt,
    ast.In: ast.NotIn,
    ast.NotIn: ast.In,
    ast.Is: ast.IsNot,
    ast.IsNot: ast.Is,
}


@dataclass(frozen=True)
class Mutant:
    path: str
    function: str
    line: int
    kind: str
    """What changed, e.g. `== -> !=`."""
    index: int
    """Which mutable node in the function, in walk order, so the mutant can be rebuilt."""
    in_message: bool = False
    """The node is inside an f-string or a `detail=` argument: it can change what a verdict
    says, never whether it passes, so it is reported apart from the score."""


class MutantResult(BaseModel):
    path: str
    function: str
    line: int
    kind: str
    in_message: bool = False
    outcome: str
    """`killed` (a test failed), `survived` (every test passed), or `timeout` (counted killed)."""
    seconds: float


class MutationReport(BaseModel):
    selection: list[str]
    baseline_seconds: float
    mutants: int
    killed: int
    survived: int
    timeout: int
    message_only: int = 0
    """Mutants inside a verdict's message, whatever their outcome; not in the score."""
    score: float
    """Killed or timed out, over every mutant that can change a verdict."""
    results: list[MutantResult]


def _functions(tree: ast.Module, names: Sequence[str]) -> Iterator[ast.FunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name in names:
            yield node


def _mutations(node: ast.AST) -> list[str]:
    """The ways one node can be mutated, as descriptions; empty when it has none."""
    if isinstance(node, ast.Compare) and len(node.ops) == 1 and type(node.ops[0]) in _FLIPS:
        before = type(node.ops[0]).__name__
        return [f"{before} -> {_FLIPS[type(node.ops[0])].__name__}"]
    if isinstance(node, ast.BoolOp):
        return ["and -> or" if isinstance(node.op, ast.And) else "or -> and"]
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return ["not removed"]
    if isinstance(node, ast.Constant) and isinstance(node.value, bool):
        return [f"{node.value} -> {not node.value}"]
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return [f"{node.value} -> {node.value + 1}", f"{node.value} -> {node.value - 1}"]
    return []


def _message_nodes(function: ast.FunctionDef) -> set[int]:
    """The ids of every node inside an f-string or a `detail=` argument of `function`."""
    inside: set[int] = set()
    for node in ast.walk(function):
        roots: list[ast.AST] = []
        if isinstance(node, ast.JoinedStr):
            roots.append(node)
        if isinstance(node, ast.keyword) and node.arg == "detail":
            roots.append(node.value)
        for root in roots:
            inside.update(id(child) for child in ast.walk(root))
    return inside


def mutants() -> list[Mutant]:
    """Every mutant of every target, in a fixed order."""
    found = []
    for path, names in TARGETS.items():
        tree = ast.parse((REPOSITORY / path).read_text(encoding="utf-8"))
        for function in _functions(tree, names):
            messages = _message_nodes(function)
            for index, node in enumerate(ast.walk(function)):
                for kind in _mutations(node):
                    found.append(
                        Mutant(
                            path=path,
                            function=function.name,
                            line=getattr(node, "lineno", function.lineno),
                            kind=kind,
                            index=index,
                            in_message=id(node) in messages,
                        )
                    )
    return found


def summarise(results: Sequence[MutantResult], baseline_seconds: float) -> MutationReport:
    """The report over `results`: the score leaves out message-only mutants."""
    scored = [r for r in results if not r.in_message]
    caught = sum(r.outcome in ("killed", "timeout") for r in scored)
    return MutationReport(
        selection=list(SELECTION),
        baseline_seconds=baseline_seconds,
        mutants=len(results),
        killed=sum(r.outcome == "killed" for r in results),
        survived=sum(r.outcome == "survived" for r in results),
        timeout=sum(r.outcome == "timeout" for r in results),
        message_only=len(results) - len(scored),
        score=caught / len(scored) if scored else 0.0,
        results=list(results),
    )


def classify(report: Path) -> MutationReport:
    """Mark a report's message-only mutants from the current source, and rescore it.

    For a report written before mutants carried `in_message`: each result is matched to the
    mutant listed at the same path, function, line and kind, so the source must be the one the
    report was run on.
    """
    old = MutationReport.model_validate_json(report.read_text(encoding="utf-8"))
    listed: dict[tuple[str, str, int, str], list[bool]] = {}
    for mutant in mutants():
        key = (mutant.path, mutant.function, mutant.line, mutant.kind)
        listed.setdefault(key, []).append(mutant.in_message)
    seen: dict[tuple[str, str, int, str], int] = {}
    results = []
    for result in old.results:
        key = (result.path, result.function, result.line, result.kind)
        position = seen.get(key, 0)
        seen[key] = position + 1
        results.append(result.model_copy(update={"in_message": listed[key][position]}))
    return summarise(results, old.baseline_seconds)


class _Apply(ast.NodeTransformer):
    def __init__(self, target: ast.AST, kind: str) -> None:
        self.target, self.kind = target, kind

    def generic_visit(self, node: ast.AST) -> ast.AST:
        node = super().generic_visit(node)
        if node is not self.target:
            return node
        if isinstance(node, ast.Compare):
            node.ops = [_FLIPS[type(node.ops[0])]()]
        elif isinstance(node, ast.BoolOp):
            node.op = ast.Or() if isinstance(node.op, ast.And) else ast.And()
        elif isinstance(node, ast.UnaryOp):
            return node.operand
        elif isinstance(node, ast.Constant) and isinstance(node.value, bool):
            node.value = not node.value
        elif isinstance(node, ast.Constant):
            node.value = int(self.kind.split(" -> ")[1])
        return node


def mutated_source(mutant: Mutant) -> str:
    """The module's source with exactly this mutant applied."""
    tree = ast.parse((REPOSITORY / mutant.path).read_text(encoding="utf-8"))
    tree = copy.deepcopy(tree)
    function = next(_functions(tree, (mutant.function,)))
    target = list(ast.walk(function))[mutant.index]
    if mutant.kind not in _mutations(target):
        raise ValueError(f"{mutant} no longer matches the source")
    return ast.unparse(ast.fix_missing_locations(_Apply(target, mutant.kind).visit(tree))) + "\n"


def _run_selection(timeout: float, workers: int) -> tuple[str, float]:
    started = time.monotonic()
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-x",
                "-q",
                "-p",
                "no:cacheprovider",
                "-n",
                str(workers),
                *SELECTION,
            ],
            cwd=REPOSITORY,
            capture_output=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return "timeout", time.monotonic() - started
    outcome = "survived" if result.returncode == 0 else "killed"
    return outcome, time.monotonic() - started


def run(out: Path, *, workers: int = 4, limit: int | None = None) -> MutationReport:
    """Run the selection once clean, then once per mutant; write `out/report.json`."""
    if out.exists():
        raise ValueError(f"{out} already exists; the run writes a fresh directory")
    # The baseline runs on the targets as `ast.unparse` writes them, unmutated, so a mutant's
    # outcome is the mutation's and never the rewrite's.
    originals = {path: (REPOSITORY / path).read_text(encoding="utf-8") for path in TARGETS}
    try:
        for path, text in originals.items():
            (REPOSITORY / path).write_text(ast.unparse(ast.parse(text)) + "\n", encoding="utf-8")
        baseline, seconds = _run_selection(timeout=3600, workers=workers)
    finally:
        for path, text in originals.items():
            (REPOSITORY / path).write_text(text, encoding="utf-8")
    if baseline != "survived":
        raise RuntimeError("the selection fails on the unmutated, rewritten graders; fix that")
    timeout = max(120.0, 3 * seconds)
    results = []
    for mutant in mutants()[:limit]:
        source = REPOSITORY / mutant.path
        original = source.read_text(encoding="utf-8")
        try:
            source.write_text(mutated_source(mutant), encoding="utf-8")
            outcome, took = _run_selection(timeout, workers)
        finally:
            source.write_text(original, encoding="utf-8")
        results.append(
            MutantResult(
                path=mutant.path,
                function=mutant.function,
                line=mutant.line,
                kind=mutant.kind,
                in_message=mutant.in_message,
                outcome=outcome,
                seconds=round(took, 1),
            )
        )
        print(
            f"{outcome:8} {mutant.path}:{mutant.line} {mutant.function} {mutant.kind}", flush=True
        )
    report = summarise(results, round(seconds, 1))
    out.mkdir(parents=True)
    (out / "report.json").write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    return report


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m precondition_library.bench.grader_mutation")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--list", action="store_true", help="list the mutants and stop")
    parser.add_argument(
        "--classify",
        type=Path,
        default=None,
        metavar="REPORT",
        help="mark an older report's message-only mutants and rescore it, in place",
    )
    args = parser.parse_args(argv)
    if args.classify is not None:
        report = classify(args.classify)
        args.classify.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
        print(json.dumps({k: v for k, v in report.model_dump().items() if k != "results"}))
        return 0
    if args.list:
        listed = mutants()
        for mutant in listed:
            print(f"{mutant.path}:{mutant.line} {mutant.function} {mutant.kind}")
        print(json.dumps({"mutants": len(listed)}))
        return 0
    report = run(args.out, workers=args.workers)
    print(json.dumps({k: v for k, v in report.model_dump().items() if k != "results"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
