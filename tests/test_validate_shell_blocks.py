"""The shell-block validator, exercised on blocks that must fail.

A parse gate nobody has watched fail is a green light with no bulb behind it,
so every rule below is stated as a block that breaks it.
"""

import importlib.util
import subprocess
import sys
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
    assert [b.code for b in vsb.iter_blocks(text)] == ["echo hi"]


@pytest.mark.parametrize("lang", ["bash", "sh", "shell"])
def test_every_shell_info_string_is_collected(lang):
    assert len(list(vsb.iter_blocks(md("echo hi", lang=lang)))) == 1


# A fence this checker does not recognise is not reported as bad, it is skipped,
# and the file reports success without ever having been read.

@pytest.mark.parametrize(
    "opener,closer",
    [("```bash", "```"), ("````bash", "````"), ("~~~bash", "~~~"), ("`````bash", "`````")],
)
def test_every_fence_length_and_character_is_collected(opener, closer):
    text = f"Prose.\n\n{opener}\nfor i in 1; do\n{closer}\n\nProse.\n"
    blocks = [b.code for b in vsb.iter_blocks(text)]
    assert blocks == ["for i in 1; do"]
    assert vsb.parse_error(blocks[0]) is not None


def test_a_block_does_not_close_on_the_other_fence_character():
    text = "```bash\n~~~\necho hi\n```\n"
    assert [b.code for b in vsb.iter_blocks(text)] == ["~~~\necho hi"]


def test_a_block_does_not_close_on_a_shorter_run_of_the_same_character():
    text = "````bash\n```\necho hi\n````\n"
    assert [b.code for b in vsb.iter_blocks(text)] == ["```\necho hi"]


def test_a_longer_closer_still_closes():
    assert [b.code for b in vsb.iter_blocks("```bash\necho hi\n`````\n")] == ["echo hi"]


def test_an_info_string_does_not_close_a_block():
    # The second fence carries a language, so it opens nothing and closes nothing;
    # the first is left unterminated, which is itself the failure.
    text = "```bash\necho one\n```bash\n"
    block, = vsb.iter_blocks(text)
    assert block.code == "echo one\n```bash" and not block.closed


def test_the_info_string_is_matched_case_insensitively():
    assert len(list(vsb.iter_blocks("```Bash\necho hi\n```\n"))) == 1


def test_a_fence_inside_a_line_does_not_close_the_block():
    # The mermaid audit skill really does match ``` inside a regex literal.
    code = 'src.matchAll(/```mermaid\\n([\\s\\S]*?)```/g)\necho done\n'
    blocks = [b.code for b in vsb.iter_blocks(md(code))]
    assert len(blocks) == 1 and blocks[0].endswith("echo done")


def test_indented_blocks_are_dedented_before_parsing():
    # Numbered-list steps indent their fences; the indent is not part of the shell.
    block = [b.code for b in vsb.iter_blocks(md("for i in 1; do\n  echo $i\ndone", indent="   "))]
    assert block == ["for i in 1; do\n  echo $i\ndone"]
    assert vsb.parse_error(block[0]) is None


def test_the_reported_line_number_points_at_the_opening_fence():
    text = md("echo hi")
    block, = vsb.iter_blocks(text)
    assert text.splitlines()[block.line - 1].strip() == "```bash"


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


def test_main_defaults_to_the_repository_root(capsys):
    assert vsb.main([]) == 0
    assert "shell block(s) parse" in capsys.readouterr().out


def test_main_accepts_a_directory_argument(tmp_path, capsys):
    (tmp_path / "SKILL.md").write_text(md("for i in 1; do\n  echo $i\n"))
    assert vsb.main([str(tmp_path)]) == 1
    assert "SKILL.md" in capsys.readouterr().err


def test_the_script_runs_as_a_command(tmp_path):
    script = Path(__file__).parent.parent / "scripts" / "validate-shell-blocks.py"
    (tmp_path / "SKILL.md").write_text(md("echo fine <placeholder>"))
    done = subprocess.run(
        [sys.executable, str(script), str(tmp_path)], capture_output=True, text=True
    )
    assert done.returncode == 0 and "1 shell block(s) parse" in done.stdout


# ── unterminated fences ──────────────────────────────────────────────────────
# A fence with no closer swallows the rest of the document, so every block after
# it vanishes from the walk and the file passes for having nothing left to check.


def test_an_unterminated_shell_fence_is_a_failure(tmp_path, capsys):
    (tmp_path / "SKILL.md").write_text("Prose.\n\n```bash\necho ok\n")
    assert vsb.main([str(tmp_path)]) == 1
    assert "unterminated bash fence" in capsys.readouterr().err


def test_an_unterminated_fence_of_another_language_is_a_failure(tmp_path, capsys):
    # It is not shell, but it hides the shell after it.
    (tmp_path / "SKILL.md").write_text("```python\nprint(1)\n\n```bash\nfor i in 1; do\n")
    assert vsb.main([str(tmp_path)]) == 1
    assert "unterminated python fence" in capsys.readouterr().err


def test_an_unterminated_fence_reports_its_opening_line():
    text = "one\ntwo\n```bash\necho hi\n"
    block, = vsb.iter_blocks(text)
    assert block.line == 3 and not block.closed


def test_a_closed_block_is_marked_closed():
    block, = vsb.iter_blocks("```bash\necho hi\n```\n")
    assert block.closed


def test_this_marketplace_parses():
    assert vsb.check(Path(__file__).parent.parent) == 0
