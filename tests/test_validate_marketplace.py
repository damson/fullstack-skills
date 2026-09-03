"""Tests for scripts/validate-marketplace.py against fixture trees.

Checked-in fixtures live in tests/fixtures/: one minimal valid marketplace and
four broken variants that are inert when the real validator runs over this
repo (its manifest and README checks read only paths relative to its ROOT).
The broken-relative-link variant is the exception: check_links walks every
non-hidden markdown file under ROOT, so a checked-in broken link would fail
the repo's own validation run. That variant is derived from the valid fixture
into a temp tree at test time instead.
"""
import shutil

from conftest import FIXTURES, REPO_ROOT


def run(validator, root):
    validator.ROOT = root
    return validator.main(), validator.problems


def test_default_root_is_the_repo(validator):
    # The scripts must keep resolving the real repo when run untouched: CI
    # invokes them with no arguments and no environment.
    assert validator.ROOT == REPO_ROOT


def test_valid_marketplace_passes(validator, capsys):
    code, problems = run(validator, FIXTURES / "valid_marketplace")
    assert code == 0
    assert problems == []
    assert "1 plugin(s), 2 skill(s)" in capsys.readouterr().out


def test_wrong_table_count_fails(validator, capsys):
    code, problems = run(validator, FIXTURES / "wrong_table_count")
    assert code == 1
    assert any("table says alpha has 3 skills" in p and "tree has 2" in p for p in problems)
    assert "1 problem(s)" in capsys.readouterr().err


def test_missing_skill_in_section_fails(validator):
    code, problems = run(validator, FIXTURES / "missing_section_skill")
    assert code == 1
    assert any("does not mention skill 'skill-two'" in p for p in problems)


def test_bad_semver_fails(validator):
    code, problems = run(validator, FIXTURES / "bad_semver")
    assert code == 1
    assert any("version '1.2' is not MAJOR.MINOR.PATCH" in p for p in problems)


def test_wrong_welcome_total_fails(validator):
    code, problems = run(validator, FIXTURES / "wrong_welcome_total")
    assert code == 1
    assert any("welcome line says 5 skills" in p and "tree has 2" in p for p in problems)
    # The plugin count half of the welcome line is right, so only the skill
    # total may be reported.
    assert not any("welcome line says" in p and "plugins" in p for p in problems)


def broken_copy(tmp_path):
    """A mutable copy of the valid fixture tree."""
    root = tmp_path / "marketplace"
    shutil.copytree(FIXTURES / "valid_marketplace", root)
    return root


def test_broken_relative_link_fails(validator, tmp_path):
    root = broken_copy(tmp_path)
    readme = root / "plugins" / "alpha" / "README.md"
    readme.write_text(readme.read_text() + "\nSee [the missing page](no-such-file.md).\n")
    code, problems = run(validator, root)
    assert code == 1
    assert problems == [
        "plugins/alpha/README.md: broken relative link → no-such-file.md"
    ]


def test_links_inside_code_are_ignored(validator, tmp_path):
    root = broken_copy(tmp_path)
    readme = root / "plugins" / "alpha" / "README.md"
    readme.write_text(
        readme.read_text()
        + "\nExample: `[dead](nope.md)`\n\n```\n[dead](also-nope.md)\n```\n"
        + "\n<!-- [dead](commented-out.md) -->\n"
    )
    code, problems = run(validator, root)
    assert code == 0
    assert problems == []


def test_phantom_plugin_listing_fails(validator, tmp_path):
    root = broken_copy(tmp_path)
    manifest = root / ".claude-plugin" / "marketplace.json"
    manifest.write_text(
        manifest.read_text().replace(
            "  ]",
            '    ,{"name": "ghost", "description": "not on disk",'
            ' "source": "./plugins/ghost"}\n  ]',
        )
    )
    code, problems = run(validator, root)
    assert code == 1
    assert "marketplace.json lists 'ghost' but plugins/ghost/ does not exist" in problems
    assert any("source does not exist" in p for p in problems)


def test_unlisted_plugin_dir_fails(validator, tmp_path):
    root = broken_copy(tmp_path)
    # No skills/ dir either: a plugin may ship only commands, so that alone
    # is not a problem and skills_of() must treat it as empty.
    (root / "plugins" / "beta").mkdir()
    code, problems = run(validator, root)
    assert code == 1
    assert "plugins/beta/ exists but marketplace.json does not list it" in problems
    assert "plugins/beta/ has no .claude-plugin/plugin.json" in problems
    assert not any("skills" in p and "beta" in p for p in problems)


def test_manifest_field_problems_are_each_reported(validator, tmp_path):
    root = broken_copy(tmp_path)
    manifest = root / ".claude-plugin" / "marketplace.json"
    manifest.write_text(
        manifest.read_text().replace(
            '      "description": "A fixture plugin with two skills",\n', ""
        )
    )
    pj = root / "plugins" / "alpha" / ".claude-plugin" / "plugin.json"
    pj.write_text('{"name": "renamed", "version": "1.0.0"}')
    (root / "plugins" / "alpha" / "README.md").unlink()
    code, problems = run(validator, root)
    assert code == 1
    assert "marketplace.json: plugin 'alpha' has no description" in problems
    assert any("name is 'renamed'" in p for p in problems)
    assert "plugins/alpha/ has no README.md" in problems


def test_invalid_plugin_json_is_reported_not_raised(validator, tmp_path):
    root = broken_copy(tmp_path)
    (root / "plugins" / "alpha" / ".claude-plugin" / "plugin.json").write_text("{oops")
    code, problems = run(validator, root)
    assert code == 1
    assert any("plugin.json is invalid" in p for p in problems)


def test_missing_welcome_line_fails(validator, tmp_path):
    root = broken_copy(tmp_path)
    readme = root / "README.md"
    readme.write_text(
        readme.read_text().replace("**2 skills in 1 themed plugins**", "some skills")
    )
    code, problems = run(validator, root)
    assert code == 1
    assert "README.md: no welcome line stating the skill and plugin totals" in problems


def test_unreadable_marketplace_json_is_one_problem_not_a_crash(validator, tmp_path):
    root = broken_copy(tmp_path)
    (root / ".claude-plugin" / "marketplace.json").write_text("{not json")
    code, problems = run(validator, root)
    assert code == 1
    assert any("marketplace.json is unreadable" in p for p in problems)


def test_stale_skill_name_in_section_fails(validator, tmp_path):
    root = broken_copy(tmp_path)
    shutil.rmtree(root / "plugins" / "alpha" / "skills" / "skill-two")
    code, problems = run(validator, root)
    assert code == 1
    assert any(
        "names 'skill-two', which is not in the tree" in p for p in problems
    )


def test_the_real_marketplace_validates(validator, capsys):
    # The repo itself is the one tree the validator exists for; a regression
    # that green-lights fixtures but breaks on real content must fail here.
    code, problems = run(validator, REPO_ROOT)
    assert code == 0, problems
