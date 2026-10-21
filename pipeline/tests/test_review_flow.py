import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from overcount import cli


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway copy of content/ with empty staging/, bank, and log, wired into the CLI."""
    shutil.copytree(cli.CONTENT_DIR, tmp_path / "content")
    paths = {
        "CONTENT_DIR": tmp_path / "content",
        "FAMILIES_DIR": tmp_path / "content" / "families",
        "STAGING_DIR": tmp_path / "staging",
        "REVIEW_DIR": tmp_path / "needs_review",
        "BANK_DIR": tmp_path / "bank",
        "GENERATION_LOG": tmp_path / "log.jsonl",
        "REPO_ROOT": tmp_path,
    }
    for name, value in paths.items():
        monkeypatch.setattr(cli, name, value)
    return tmp_path


def stage(repo: Path, family_id: str, edit: dict[str, str] | None = None) -> Path:
    folder = repo / "staging" / family_id
    shutil.copytree(repo / "content" / "families" / family_id, folder)
    if edit:
        data = json.loads((folder / "family.json").read_text())
        data["problems"][0].update(edit)
        (folder / "family.json").write_text(json.dumps(data))
    return folder


def statuses(repo: Path) -> list[str]:
    return [json.loads(line)["status"] for line in (repo / "log.jsonl").read_text().splitlines()]


def test_review_writes_a_side_by_side_page_without_moving_anything(repo: Path) -> None:
    stage(repo, "round-table", {"title": "Round table, regenerated"})
    result = CliRunner().invoke(cli.app, ["review"])
    assert result.exit_code == 0, result.output
    page = (repo / "staging" / "review.html").read_text()
    assert "replaces the live version" in page and "Old (live)" in page and "Round table, regenerated" in page
    assert (repo / "staging" / "round-table").exists()
    assert statuses(repo) == ["verified_pass"]


def test_approve_replaces_the_live_family_and_rebuilds_the_bank(repo: Path) -> None:
    stage(repo, "round-table", {"title": "Round table, regenerated"})
    result = CliRunner().invoke(cli.app, ["approve", "round-table"])
    assert result.exit_code == 0, result.output
    live = json.loads((repo / "content" / "families" / "round-table" / "family.json").read_text())
    assert live["problems"][0]["title"] == "Round table, regenerated"
    assert not (repo / "staging" / "round-table").exists()
    assert (repo / "bank" / "families" / "round-table.json").exists()
    assert statuses(repo)[-1] == "approved"


def test_approve_refuses_a_family_that_fails_a_gate(repo: Path) -> None:
    stage(repo, "round-table", {"title": "Wrong answer"})
    data = json.loads((repo / "staging" / "round-table" / "family.json").read_text())
    data["problems"][0]["answer"]["expr"] = "n!"
    (repo / "staging" / "round-table" / "family.json").write_text(json.dumps(data))
    result = CliRunner().invoke(cli.app, ["approve", "round-table"])
    assert result.exit_code == 1
    live = json.loads((repo / "content" / "families" / "round-table" / "family.json").read_text())
    assert live["problems"][0]["answer"]["expr"] == "n!/n"


def test_reject_deletes_the_draft_and_keeps_the_live_version(repo: Path) -> None:
    stage(repo, "round-table")
    result = CliRunner().invoke(cli.app, ["reject", "round-table"])
    assert result.exit_code == 0
    assert not (repo / "staging" / "round-table").exists()
    assert (repo / "content" / "families" / "round-table" / "family.json").exists()
    assert statuses(repo) == ["rejected"]
