"""Tests for scripts/release_notes.py.

The script's only external dependency is `git`, wrapped in one function; the
unit tests replace that wrapper with a canned fake so they exercise the
assembly logic deterministically, plus one real call to prove the wrapper
itself talks to git.
"""
import sys


def blob(version):
    return f'{{"name": "p", "version": "{version}"}}'


def fake_git(responses):
    """A git() stand-in keyed on the subcommand plus its first argument."""

    def git(*args):
        return responses.get(args[:2], "")

    return git


def test_git_wrapper_runs_real_git(notes):
    assert notes.git("rev-parse", "--is-inside-work-tree") == "true"


def test_git_wrapper_swallows_failures(notes):
    assert notes.git("rev-parse", "--verify", "no-such-ref-anywhere") == ""


def test_version_at(notes, monkeypatch):
    monkeypatch.setattr(notes, "git", fake_git({("show", "v1:plugins/p/.claude-plugin/plugin.json"): blob("1.2.3")}))
    assert notes.version_at("v1", "p") == "1.2.3"
    assert notes.version_at("v1", "absent") is None
    assert notes.version_at("", "p") is None  # empty ref: plugin predates history


def test_version_at_without_version_field(notes, monkeypatch):
    monkeypatch.setattr(notes, "git", fake_git({("show", "v1:plugins/p/.claude-plugin/plugin.json"): '{"name": "p"}'}))
    assert notes.version_at("v1", "p") is None


def test_version_table_marks_new_and_updated_only(notes, monkeypatch):
    monkeypatch.setattr(
        notes,
        "git",
        fake_git(
            {
                # "gone" is in the tree listing but has no readable manifest
                # at either ref; it must be skipped, not crash the table.
                ("ls-tree", "--name-only"): "plugins/fresh\nplugins/gone\nplugins/moved\nplugins/same",
                ("show", "old:plugins/moved/.claude-plugin/plugin.json"): blob("1.0.0"),
                ("show", "old:plugins/same/.claude-plugin/plugin.json"): blob("2.0.0"),
                ("show", "new:plugins/fresh/.claude-plugin/plugin.json"): blob("0.1.0"),
                ("show", "new:plugins/moved/.claude-plugin/plugin.json"): blob("1.0.1"),
                ("show", "new:plugins/same/.claude-plugin/plugin.json"): blob("2.0.0"),
            }
        ),
    )
    table = notes.version_table("old", "new")
    assert table[0].startswith("| Plugin |")
    assert "| `fresh` | — | 0.1.0 | new |" in table
    assert "| `moved` | 1.0.0 | 1.0.1 | updated |" in table
    assert not any("same" in row or "gone" in row for row in table)


def test_version_table_when_nothing_moved(notes, monkeypatch):
    monkeypatch.setattr(notes, "git", fake_git({("ls-tree", "--name-only"): ""}))
    assert notes.version_table("old", "new") == ["_No plugin versions changed._"]


def test_commits_truncates_loudly(notes, monkeypatch):
    subjects = "\n".join(f"- change {i}" for i in range(45))
    monkeypatch.setattr(notes, "git", fake_git({("log", "a..b"): subjects}))
    lines = notes.commits("a..b")
    assert len(lines) == 41
    assert lines[-1] == "- …and 5 more"


def test_commits_empty_range(notes, monkeypatch):
    monkeypatch.setattr(notes, "git", fake_git({}))
    assert notes.commits("a..b") == ["_No direct commits._"]
    assert notes.commits("") == ["_No direct commits._"]


def test_merged_prs_sees_both_merge_shapes(notes, monkeypatch):
    log = "\n".join(
        [
            "Merge pull request #12 from damson/topic",
            "Squashed subject (#7)",
            "Another squashed subject (#12)",  # duplicate PR number collapses
            "Plain commit with (#5) not at the end, kind of",
        ]
    )
    monkeypatch.setattr(notes, "git", fake_git({("log", "a..b"): log}))
    assert notes.merged_prs("a..b") == "#7 #12"


def test_merged_prs_without_prs_or_range(notes, monkeypatch):
    monkeypatch.setattr(notes, "git", fake_git({("log", "a..b"): "boring subject"}))
    assert notes.merged_prs("a..b") == "(none — direct commits only)"
    assert notes.merged_prs("") == "(none)"


def release_git():
    return fake_git(
        {
            ("ls-tree", "--name-only"): "plugins/p",
            ("show", "HEAD:plugins/p/.claude-plugin/plugin.json"): blob("1.1.0"),
            ("show", "v1:plugins/p/.claude-plugin/plugin.json"): blob("1.0.0"),
            ("show", "origin/develop:plugins/p/.claude-plugin/plugin.json"): blob("1.1.0"),
            ("show", "origin/main:plugins/p/.claude-plugin/plugin.json"): blob("1.0.0"),
            ("log", "v1..HEAD"): "- Ship it (#3)",
            ("log", "HEAD"): "- First commit",
            ("log", "origin/main..origin/develop"): "- Ship it (#3)",
            # The git() wrapper strips output; canned values must arrive stripped.
            ("diff", "--shortstat"): "3 files changed, 9 insertions(+)",
        }
    )


def run_main(notes, monkeypatch, capsys, *argv):
    monkeypatch.setattr(notes, "git", release_git())
    monkeypatch.setattr(sys, "argv", ["release_notes.py", *argv])
    assert notes.main() == 0
    return capsys.readouterr().out


def test_main_since_tag(notes, monkeypatch, capsys):
    out = run_main(notes, monkeypatch, capsys, "--since", "v1")
    assert "| `p` | 1.0.0 | 1.1.0 | updated |" in out
    assert "**Pull requests:** #3" in out
    assert "_Since v1._" in out


def test_main_first_release_covers_everything(notes, monkeypatch, capsys):
    out = run_main(notes, monkeypatch, capsys, "--since", "")
    assert "| `p` | — | 1.1.0 | new |" in out
    assert "- First commit" in out
    assert "_Since" not in out


def test_main_pr_body(notes, monkeypatch, capsys):
    out = run_main(notes, monkeypatch, capsys, "--pr-body")
    assert out.startswith("## What is being released")
    assert "| `p` | 1.0.0 | 1.1.0 | updated |" in out
    assert "**Pull requests in this batch:** #3" in out
    assert "**Diffstat:** 3 files changed, 9 insertions(+)" in out
    assert "<details><summary>Commits</summary>" in out
