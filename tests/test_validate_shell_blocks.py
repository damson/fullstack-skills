"""The shell-block validator, exercised on blocks that must fail.

A parse gate nobody has watched fail is a green light with no bulb behind it,
so every rule below is stated as a block that breaks it.
"""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "validate_shell_blocks",
    Path(__file__).parent.parent / "scripts" / "validate-shell-blocks.py",
)
vsb = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(vsb)


def md(code, lang="bash", indent=""):
    body = "\n".join(indent + line if line else line for line in code.splitlines())
    return f"Prose above.\n\n{indent}```{lang}\n{body}\n{indent}```\n\nProse below.\n"


# ── blocks that must be rejected ─────────────────────────────────────────────

BROKEN = {
    "unbalanced single quote": "echo 'unterminated\n",
    "unterminated loop": "for i in 1 2 3; do\n  echo $i\n",
    "case without esac": 'case "$x" in\n  a) echo a ;;\n',
    "unterminated command substitution": 'n=$(gh pr view --json number\n',
    "stray fi": "echo hello\nfi\n",
    "unclosed brace group": 'true && { echo yes\n',
}


@pytest.mark.parametrize("label", sorted(BROKEN))
def test_real_syntax_errors_are_caught(label):
    assert vsb.parse_error(BROKEN[label]) is not None, label


# ── blocks that must be accepted ─────────────────────────────────────────────

VALID = {
    "angle-bracket placeholder": "git fetch <url> <branch>\n",
    "placeholder holding a space": "sha=<the pinned head>\n",
    "placeholder inside a path": "gh api repos/<owner>/<repo>/pulls/<n>\n",
    "process substitution": 'comm -13 <(echo "$a") <(echo "$b")\n',
    "here-string": 'jq -r length <<<"$s"\n',
    "stderr redirect": "cmd 2>&1 | head -1\n",
    "arrow in a string": 'echo "HEAD MOVED $a -> $b"\n',
    "heredoc": "cat <<'MSG'\nliteral <not-a-redirect> text\nMSG\n",
    "arithmetic comparison": '[ "$n" -lt 3 ] && echo few\n',
}


@pytest.mark.parametrize("label", sorted(VALID))
def test_documentation_shapes_are_not_errors(label):
    assert vsb.parse_error(VALID[label]) is None, label


# ── extraction ───────────────────────────────────────────────────────────────


def test_only_shell_blocks_are_collected():
    text = md("SELECT 1;", lang="sql") + md("echo hi")
    assert [code for _, code in vsb.iter_blocks(text)] == ["echo hi"]


@pytest.mark.parametrize("lang", ["bash", "sh", "shell"])
def test_every_shell_info_string_is_collected(lang):
    assert len(list(vsb.iter_blocks(md("echo hi", lang=lang)))) == 1


def test_a_fence_inside_a_line_does_not_close_the_block():
    # The mermaid audit skill really does match ``` inside a regex literal.
    code = 'src.matchAll(/```mermaid\\n([\\s\\S]*?)```/g)\necho done\n'
    blocks = [c for _, c in vsb.iter_blocks(md(code))]
    assert len(blocks) == 1 and blocks[0].endswith("echo done")


def test_indented_blocks_are_dedented_before_parsing():
    # Numbered-list steps indent their fences; the indent is not part of the shell.
    block = [c for _, c in vsb.iter_blocks(md("for i in 1; do\n  echo $i\ndone", indent="   "))]
    assert block == ["for i in 1; do\n  echo $i\ndone"]
    assert vsb.parse_error(block[0]) is None


def test_the_reported_line_number_points_at_the_opening_fence():
    text = md("echo hi")
    (lineno, _), = vsb.iter_blocks(text)
    assert text.splitlines()[lineno - 1].strip() == "```bash"


# ── the walk ─────────────────────────────────────────────────────────────────


def test_check_reports_and_fails_on_a_broken_block(tmp_path, capsys):
    skill = tmp_path / "plugins" / "p" / "skills" / "s"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(md("for i in 1; do\n  echo $i\n"))
    assert vsb.check(tmp_path) == 1
    assert "SKILL.md" in capsys.readouterr().err


def test_check_passes_a_clean_tree(tmp_path, capsys):
    skill = tmp_path / "plugins" / "p" / "skills" / "s"
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(md("git fetch <url> <branch>"))
    assert vsb.check(tmp_path) == 0
    assert "1 shell block(s) parse" in capsys.readouterr().out


def test_this_marketplace_parses():
    assert vsb.check(Path(__file__).parent.parent) == 0
