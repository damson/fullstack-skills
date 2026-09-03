"""Tests for scripts/bump_version.py."""
import json
import sys


MANIFEST = (
    '{\n'
    '  "name": "alpha",\n'
    '  "version": "1.0.9",\n'
    '  "description": "caf\\u00e9 fixture with \\u2014 escapes"\n'
    '}\n'
)


def plugin_tree(tmp_path, text=MANIFEST):
    path = tmp_path / "plugins" / "alpha" / ".claude-plugin" / "plugin.json"
    path.parent.mkdir(parents=True)
    path.write_text(text)
    return path


def run(bump, monkeypatch, root, *argv):
    monkeypatch.setattr(bump, "ROOT", root)
    monkeypatch.setattr(sys, "argv", ["bump_version.py", *argv])
    return bump.main()


def test_bumps_patch_and_touches_nothing_else(bump, monkeypatch, tmp_path, capsys):
    path = plugin_tree(tmp_path)
    assert run(bump, monkeypatch, tmp_path, "alpha") == 0
    text = path.read_text()
    # Targeted substitution: only the version changed, the surrounding
    # formatting and escapes survived byte for byte.
    assert text == MANIFEST.replace("1.0.9", "1.0.10")
    assert json.loads(text)["version"] == "1.0.10"
    assert "alpha: 1.0.9 → 1.0.10" in capsys.readouterr().out


def test_missing_plugin_fails(bump, monkeypatch, tmp_path, capsys):
    assert run(bump, monkeypatch, tmp_path, "nope") == 1
    assert "No such plugin manifest" in capsys.readouterr().err


def test_non_semver_version_is_refused(bump, monkeypatch, tmp_path, capsys):
    path = plugin_tree(tmp_path, MANIFEST.replace('"1.0.9"', '"2.0"'))
    assert run(bump, monkeypatch, tmp_path, "alpha") == 1
    assert "no MAJOR.MINOR.PATCH version to bump" in capsys.readouterr().err
    assert path.read_text() == MANIFEST.replace('"1.0.9"', '"2.0"')


def test_wrong_argument_count_prints_usage(bump, monkeypatch, tmp_path, capsys):
    assert run(bump, monkeypatch, tmp_path) == 2
    assert "Usage:" in capsys.readouterr().err
