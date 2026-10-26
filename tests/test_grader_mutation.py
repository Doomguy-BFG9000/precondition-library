"""The grader mutation runner makes the mutants it says it makes (#299 step 1)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from precondition_library.bench import grader_mutation as gm

TOY = """
def check(state, n):
    if state.ready and not state.lost:
        return n == 3 or n in (4, 5)
    return False
"""


@pytest.fixture
def toy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "toy.py").write_text(TOY, encoding="utf-8")
    monkeypatch.setattr(gm, "REPOSITORY", tmp_path)
    monkeypatch.setattr(gm, "TARGETS", {"toy.py": ("check",)})
    return tmp_path


def test_every_kind_of_mutant_is_listed(toy: Path) -> None:
    kinds = sorted(m.kind for m in gm.mutants())
    assert kinds == sorted(
        [
            "and -> or",
            "not removed",
            "Eq -> NotEq",
            "3 -> 4",
            "3 -> 2",
            "or -> and",
            "In -> NotIn",
            "4 -> 5",
            "4 -> 3",
            "5 -> 6",
            "5 -> 4",
            "False -> True",
        ]
    )


@pytest.mark.parametrize(
    ("kind", "expected"),
    [
        ("and -> or", "if state.ready or not state.lost:"),
        ("not removed", "if state.ready and state.lost:"),
        ("Eq -> NotEq", "return n != 3 or n in (4, 5)"),
        ("or -> and", "return n == 3 and n in (4, 5)"),
        ("In -> NotIn", "return n == 3 or n not in (4, 5)"),
        ("3 -> 4", "return n == 4 or n in (4, 5)"),
        ("False -> True", "return True"),
    ],
)
def test_each_mutant_changes_exactly_its_node(toy: Path, kind: str, expected: str) -> None:
    mutant = next(m for m in gm.mutants() if m.kind == kind)
    source = gm.mutated_source(mutant)
    assert expected in source
    original = ast.unparse(ast.parse(TOY)).splitlines()
    changed = [a for a, b in zip(original, source.splitlines(), strict=True) if a != b]
    assert len(changed) == 1, changed


def test_a_stale_mutant_is_refused(toy: Path) -> None:
    mutant = next(m for m in gm.mutants() if m.kind == "Eq -> NotEq")
    (toy / "toy.py").write_text(TOY.replace("n == 3", "n"), encoding="utf-8")
    with pytest.raises(ValueError, match="no longer matches"):
        gm.mutated_source(mutant)


def test_the_real_targets_and_selection_exist() -> None:
    for path, names in gm.TARGETS.items():
        tree = ast.parse((gm.REPOSITORY / path).read_text(encoding="utf-8"))
        defined = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        assert set(names) <= defined, path
    for path in gm.SELECTION:
        assert (gm.REPOSITORY / path).is_file(), path
    assert len(gm.mutants()) > 100


def test_a_mutant_inside_a_verdicts_message_is_marked_and_left_out_of_the_score(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "toy.py").write_text(
        "def check(sha, n):\n    return Verdict(ok=n == 1, detail=f'{sha[:12]} {n or 0}')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(gm, "REPOSITORY", tmp_path)
    monkeypatch.setattr(gm, "TARGETS", {"toy.py": ("check",)})
    marked = {(m.kind, m.in_message) for m in gm.mutants()}
    assert marked == {
        ("Eq -> NotEq", False),
        ("1 -> 2", False),
        ("1 -> 0", False),
        ("12 -> 13", True),
        ("12 -> 11", True),
        ("or -> and", True),
        ("0 -> 1", True),
        ("0 -> -1", True),
    }
    outcome = {"Eq -> NotEq": "killed", "1 -> 2": "survived", "1 -> 0": "killed"}
    results = [
        gm.MutantResult(
            path="toy.py",
            function="check",
            line=2,
            kind=m.kind,
            in_message=m.in_message,
            outcome=outcome.get(m.kind, "survived"),
            seconds=0.0,
        )
        for m in gm.mutants()
    ]
    report = gm.summarise(results, 1.0)
    assert (report.mutants, report.message_only, report.survived) == (8, 5, 6)
    assert report.score == pytest.approx(2 / 3)
