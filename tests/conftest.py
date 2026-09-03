"""Shared plumbing for the script tests.

The scripts under scripts/ are standalone files (one with a hyphen in its
name), so they are loaded via importlib rather than imported. Each test loads
a fresh module: validate-marketplace.py accumulates findings in a module-level
`problems` list, and a shared module would leak state between tests.

Every script computes ROOT at module level but only *reads* it inside its
functions, so a test retargets a fresh module at a fixture tree by assigning
`mod.ROOT`. No script needed changes to be testable, which keeps the behaviour
CI depends on byte-for-byte identical.
"""
import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"


def load_script(filename):
    """Load scripts/<filename> as a fresh module object."""
    spec = importlib.util.spec_from_file_location(
        filename.replace("-", "_").removesuffix(".py"), SCRIPTS / filename
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def validator():
    """A fresh validate-marketplace module (clean `problems` list)."""
    return load_script("validate-marketplace.py")


@pytest.fixture
def bump():
    return load_script("bump_version.py")


@pytest.fixture
def notes():
    return load_script("release_notes.py")
