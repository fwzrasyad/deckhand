"""Tests for tools/scripts/check_imports.py (SRD 3.4 mobile layering)."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import check_imports  # noqa: E402


def _write(root: Path, relative: str, body: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body + "\n", encoding="utf-8")


def test_forbidden_import_is_reported(tmp_path: Path, capsys) -> None:
    """presentation/ importing data/ fails and names file, line and rule."""
    _write(
        tmp_path,
        "features/deck/presentation/deck_screen.dart",
        "import 'package:deckhand/data/network/deckhand_client.dart';",
    )

    assert check_imports.main([str(tmp_path)]) == 1

    out = capsys.readouterr().out
    assert "deck_screen.dart:1: layer-direction" in out
    assert "presentation/ must not import data/" in out


def test_legal_imports_pass(tmp_path: Path) -> None:
    """Inward dependencies and cross-feature presentation imports are fine."""
    _write(
        tmp_path,
        "features/deck/presentation/deck_screen.dart",
        "import 'package:deckhand/features/deck/application/deck_controller.dart';\n"
        "import 'package:deckhand/features/runs/presentation/runs_screen.dart';\n"
        "import 'package:deckhand/domain/entities/deck_layout.dart';",
    )
    _write(
        tmp_path,
        "features/deck/application/deck_controller.dart",
        "import 'package:deckhand/domain/entities/deck_layout.dart';",
    )
    _write(
        tmp_path,
        "data/repositories/host_repository.dart",
        "import 'package:deckhand/domain/entities/host.dart';",
    )

    assert check_imports.main([str(tmp_path)]) == 0


def test_cross_feature_internal_import_is_reported(tmp_path: Path) -> None:
    """A relative import of another feature's application/ is caught."""
    _write(
        tmp_path,
        "features/deck/presentation/deck_screen.dart",
        "import '../../runs/application/runs_controller.dart';",
    )

    violations = check_imports.check(tmp_path)

    assert [violation.rule for violation in violations] == [
        "cross-feature-internal"
    ]
