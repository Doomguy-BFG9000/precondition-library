"""The real-`Cargo.lock` fault (#306): each state conflicts, and different actions are right.

Requires `cargo` (it resolves from vendored crates, offline). GitHub's Ubuntu runners and the
development container have it; without it these tests fail rather than skip, so a missing
toolchain is seen.
"""

from __future__ import annotations

import pytest

from precondition_library.bench.lock_actions import three_way, unify
from precondition_library.sandbox import Sandbox, create, git_out, run_git
from precondition_library.tasks.faults import cargo_lock_conflict as fault
from precondition_library.tasks.invariants import record_refs_at_start, recorded_state_intact
from precondition_library.tasks.spec import GroundTruth

SEED_FOR = {
    state: next(s for s in range(50) if fault.state_for_seed(s) == state)
    for state in fault.INJECTED_STATES
}


def _build(seed: int) -> Sandbox:
    box = create(seed, [fault.SPEC.name])
    fault.SPEC.inject(seed, box)
    record_refs_at_start(box)
    return box


@pytest.fixture
def built():
    boxes: list[Sandbox] = []

    def build(state: str) -> Sandbox:
        boxes.append(_build(SEED_FOR[state]))
        return boxes[-1]

    yield build
    for box in boxes:
        box.destroy()


def _grade(box: Sandbox, state: str) -> GroundTruth:
    """Both of the episode's clauses, the recorded state first."""
    intact = recorded_state_intact(box, surface=fault.SPEC.change_surface_for_seed(SEED_FOR[state]))
    return intact if not intact.ok else fault.SPEC.check(box)


def _resolve(box: Sandbox, action: str) -> None:
    """Merge upstream, then settle `Cargo.lock` the way `action` does, and commit."""
    work = box.work
    run_git(("merge", "--no-edit", "upstream/main"), cwd=work, check=False)
    side = "--theirs" if "upstream" in action else "--ours"
    run_git(("checkout", side, "--", fault.LOCK), cwd=work)
    if action.startswith("reconcile"):
        fault.cargo(work, "update", "--workspace")
    if action == "local_then_update_alder":
        fault.cargo(work, "update", "-p", "alder")
    run_git(("add", "-A"), cwd=work)
    run_git(("commit", "-q", "--no-edit"), cwd=work)


ACTIONS = (
    "take_local",
    "take_upstream",
    "reconcile_local",
    "reconcile_upstream",
    "local_then_update_alder",
)
RIGHT = {
    "both_added": {"reconcile_local", "reconcile_upstream", "local_then_update_alder"},
    "local_removed": {"reconcile_upstream", "local_then_update_alder"},
    "same_crate_bumped": {"local_then_update_alder"},
}


def test_every_state_is_reachable() -> None:
    assert set(SEED_FOR) == set(fault.INJECTED_STATES)


@pytest.mark.parametrize("state", fault.INJECTED_STATES)
def test_the_sync_conflicts_in_the_lock_and_the_injected_state_fails(state: str, built) -> None:
    box = built(state)
    merged = run_git(
        ("merge-tree", "--write-tree", "--name-only", "-z", "upstream/main", "HEAD"),
        cwd=box.work,
        check=False,
    )
    assert merged.returncode == 1
    assert merged.stdout.split("\0\0", 1)[0].split("\0")[1:] == [fault.LOCK]
    assert not fault.SPEC.check(box).ok


@pytest.mark.parametrize("state", fault.INJECTED_STATES)
@pytest.mark.parametrize("action", ACTIONS)
def test_exactly_the_right_actions_pass(state: str, action: str, built) -> None:
    box = built(state)
    _resolve(box, action)
    verdict = _grade(box, state)
    assert verdict.ok == (action in RIGHT[state]), f"{state}/{action}: {verdict.detail}"


def test_a_lock_cargo_would_rewrite_is_refused_even_with_the_right_set(built) -> None:
    """The set alone is not enough. Drop `birch` from the manifest after a right resolution:
    the lock still resolves the expected set, and cargo refuses it for the manifest it is in."""
    box = built("both_added")
    _resolve(box, "reconcile_upstream")
    assert _grade(box, "both_added").ok
    manifest = box.work / fault.MANIFEST
    text = manifest.read_text(encoding="utf-8")
    manifest.write_text(text.replace('birch = "0.2"\n', ""), encoding="utf-8")
    run_git(("commit", "-q", "-am", "drop a dependency the lock still lists"), cwd=box.work)

    verdict = fault.SPEC.check(box)
    assert not verdict.ok
    assert "cargo refuses" in verdict.detail, verdict.detail


@pytest.mark.parametrize("state", fault.INJECTED_STATES)
def test_the_package_level_merge_is_right_except_where_a_removal_must_win(
    state: str, built
) -> None:
    """The expected sets against `bench.lock_actions`' three-way merge, unified: equal where the
    design says the package merge is right, and different where local removed what upstream
    bumped -- the merge keeps upstream's `birch`, which nothing requires any more."""
    box = built(state)

    def lock_at(revision: str) -> set[tuple[str, str]]:
        text = git_out("show", f"{revision}:{fault.LOCK}", cwd=box.work)
        return fault.packages_of(text)

    merged = unify(
        fault.LOCK,
        three_way(
            lock_at(box.recorded["base"]),
            lock_at(box.recorded["local-tip"]),
            lock_at("upstream/main"),
        ),
    )
    assert (merged == fault.EXPECTED[state]) == (state != "local_removed")


def test_the_same_seed_builds_the_same_commits() -> None:
    seed = SEED_FOR["same_crate_bumped"]
    first = _build(seed)
    try:
        tips = (git_out("rev-parse", "HEAD", cwd=first.work), first.recorded["local-tip"])
    finally:
        first.destroy()
    second = _build(seed)
    try:
        assert (git_out("rev-parse", "HEAD", cwd=second.work), second.recorded["local-tip"]) == tips
    finally:
        second.destroy()
