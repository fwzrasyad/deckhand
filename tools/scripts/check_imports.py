#!/usr/bin/env python3
"""Check the mobile import layering rules from SRD 3.4.

Dependencies point inward:

    presentation -> application -> domain
    data -> domain

``core/`` and ``shared/`` are shared kernels and are always allowed. Files in
``app/``, ``core/`` and ``shared/`` are not checked as importers. Third-party
packages and ``dart:`` imports are ignored.

Rules reported (each line is ``file:line: rule: message``):

- ``layer-direction``: a layer imports a layer it may not depend on.
- ``cross-feature-internal``: a feature imports another feature's
  ``application/`` or ``domain/``. Only ``presentation/`` is public surface.

Usage: python tools/scripts/check_imports.py [mobile_lib_dir]
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from pathlib import Path

LAYERS = ("presentation", "application", "domain", "data")

# Importing layer -> layers it must not depend on.
FORBIDDEN: dict[str, frozenset[str]] = {
    "presentation": frozenset({"data"}),
    "application": frozenset({"data", "presentation"}),
    "domain": frozenset({"data", "application", "presentation"}),
    "data": frozenset({"application", "presentation"}),
}

IMPORT_RE = re.compile(r"^\s*(?:import|export)\s+['\"]([^'\"]+)['\"]")


@dataclass(frozen=True)
class Violation:
    """One forbidden import."""

    path: Path
    line: int
    rule: str
    message: str

    def __str__(self) -> str:
        """Render the violation for CI logs."""
        return f"{self.path}:{self.line}: {self.rule}: {self.message}"


def _lib_relative(
    root: Path, importer: Path, spec: str
) -> tuple[str, ...] | None:
    """Return the import spec as path parts below ``root``, or None if external."""
    if spec.startswith("package:deckhand/"):
        return tuple(spec.removeprefix("package:deckhand/").split("/"))
    if not spec.startswith("."):
        return None  # dart: or a third-party package
    resolved = (importer.parent / spec).resolve()
    try:
        return tuple(resolved.relative_to(root.resolve()).parts)
    except ValueError:
        return None


def _feature_layer(parts: tuple[str, ...]) -> tuple[str | None, str | None]:
    """Return ``(feature, layer)`` for ``features/<name>/<layer>/...`` paths."""
    if len(parts) > 2 and parts[0] == "features" and parts[2] in LAYERS:
        return parts[1], parts[2]
    return None, None


def _top_level_layer(parts: tuple[str, ...]) -> str | None:
    """Return the layer for a top-level ``domain/`` or ``data/`` path."""
    return parts[0] if parts and parts[0] in LAYERS else None


def _violation(
    root: Path,
    path: Path,
    line: int,
    spec: str,
    source_feature: str | None,
    source_layer: str,
) -> Violation | None:
    """Return a violation when ``spec`` breaks the rules for the importer."""
    target = _lib_relative(root, path, spec)
    if target is None:
        return None
    target_feature, target_layer = _feature_layer(target)
    if target_layer is None:
        target_layer = _top_level_layer(target)
    if target_layer is None:
        return None  # core/, shared/, app/ and anything else is always allowed

    if target_layer in FORBIDDEN[source_layer]:
        return Violation(
            path,
            line,
            "layer-direction",
            f"{source_layer}/ must not import {target_layer}/ ({spec})",
        )
    if (
        source_feature is not None
        and target_feature not in (None, source_feature)
        and target_layer != "presentation"
    ):
        return Violation(
            path,
            line,
            "cross-feature-internal",
            f"features/{source_feature}/ may only use "
            f"features/{target_feature}/presentation/, not {target_layer}/ ({spec})",
        )
    return None


def check(root: Path) -> list[Violation]:
    """Return every layering violation found under ``root``."""
    violations: list[Violation] = []
    for path in sorted(root.rglob("*.dart")):
        parts = path.relative_to(root).parts
        source_feature, source_layer = _feature_layer(parts)
        if source_layer is None:
            source_layer = _top_level_layer(parts)
            if source_layer is None:
                continue
        for number, text in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            match = IMPORT_RE.match(text)
            if match is None:
                continue
            violation = _violation(
                root, path, number, match.group(1), source_feature, source_layer
            )
            if violation is not None:
                violations.append(violation)
    return violations


def main(argv: list[str]) -> int:
    """Run the check and return a process exit code."""
    root = Path(argv[0]) if argv else Path("mobile/lib")
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 2
    violations = check(root)
    for violation in violations:
        print(violation)
    print(f"==> {len(violations)} import violation(s) in {root}")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
