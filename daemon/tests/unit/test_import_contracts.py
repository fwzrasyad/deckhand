"""Proves the import-linter contracts in ``pyproject.toml`` are actually enforced.

SRD 3.3 fixes the daemon layering and the allowlisted cross-service imports, and
requires CI to fail on a violation. A contract that silently stops working is
worse than no contract, so this module checks both directions:

1. the real project satisfies its contracts;
2. a deliberate violation in a throwaway project is reported as a failure.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

DAEMON_ROOT = Path(__file__).resolve().parents[2]

CONFIG_TEMPLATE = """\
[tool.importlinter]
root_packages = ["{package}"]

[[tool.importlinter.contracts]]
name = "{package} layering"
type = "layers"
layers = ["{package}.transport", "{package}.core"]
"""


def _sibling_script(name: str) -> str | None:
    """Resolve a console script installed next to the running interpreter."""
    suffix = ".exe" if sys.platform == "win32" else ""
    candidate = Path(sys.executable).parent / f"{name}{suffix}"

    return str(candidate) if candidate.is_file() else None


def _lint_imports(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run the import-linter CLI in ``cwd``."""
    executable = shutil.which("lint-imports") or _sibling_script("lint-imports")
    if executable is None:  # pragma: no cover - guards a broken environment
        pytest.fail("lint-imports is not installed; run `uv sync` first")

    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(cwd), env.get("PYTHONPATH", "")]))

    return subprocess.run(
        [executable, *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_project_satisfies_its_contracts() -> None:
    result = _lint_imports(DAEMON_ROOT)

    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"


def test_deliberate_forbidden_import_is_caught(tmp_path: Path) -> None:
    package = tmp_path / "fakeapp"
    package.mkdir()
    (package / "__init__.py").write_text('"""Throwaway package."""\n', encoding="utf-8")
    (package / "transport.py").write_text('"""Higher layer."""\n', encoding="utf-8")
    (package / "core.py").write_text(
        '"""Lower layer that illegally imports the layer above it."""\n'
        "\n"
        "from fakeapp import transport\n"
        "\n"
        "IMPORTED = transport\n",
        encoding="utf-8",
    )
    config = tmp_path / "importlinter.toml"
    config.write_text(CONFIG_TEMPLATE.format(package="fakeapp"), encoding="utf-8")

    result = _lint_imports(tmp_path, "--config", str(config))
    combined = result.stdout + result.stderr

    assert result.returncode != 0, f"import-linter missed a violation:\n{combined}"
    assert "fakeapp.core" in combined
    assert "fakeapp.transport" in combined
