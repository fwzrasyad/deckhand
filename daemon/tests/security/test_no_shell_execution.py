"""Guard: the daemon never asks a shell to interpret anything (SEC-004).

Param values reach a process as argv elements or environment variables. A
``shell=True`` call, ``os.system``, ``eval``, or ``exec`` anywhere in the daemon
would reopen the argument-injection hole this project exists to avoid.
"""

from __future__ import annotations

import re
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"

FORBIDDEN = {
    "shell=True": re.compile(r"shell\s*=\s*True"),
    "os.system": re.compile(r"\bos\.system\s*\("),
    "os.popen": re.compile(r"\bos\.popen\s*\("),
    "eval": re.compile(r"(?<![\w.])eval\s*\("),
    "exec": re.compile(r"(?<![\w.])exec\s*\("),
}


def _python_sources() -> list[Path]:
    return sorted(SRC.rglob("*.py"))


def test_source_tree_is_scanned() -> None:
    assert _python_sources(), "no Python sources found under src/"


def test_no_shell_or_dynamic_code_execution() -> None:
    offenders: list[str] = []

    for path in _python_sources():
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for name, pattern in FORBIDDEN.items():
                if pattern.search(line):
                    relative = path.relative_to(SRC.parent)
                    offenders.append(f"{relative}:{line_number}: {name}")

    assert not offenders, "forbidden execution primitives found:\n" + "\n".join(offenders)
