"""Static guards: secret material is compared and reported safely.

Pairing secrets, proofs and device tokens must never be compared with ``==``;
hashes are compared with ``hmac.compare_digest`` (SRD 12.4, SEC-008).
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

_SECURITY_DIR = Path(__file__).resolve().parents[2] / "src" / "deckhand" / "security"

# Modules that compare secret material themselves and must use compare_digest.
_DIGEST_PATHS = (_SECURITY_DIR / "crypto.py", _SECURITY_DIR / "tokens.py")

# Every module that handles secrets, proofs, tokens or hashes. pairing.py and
# lockout.py delegate comparisons to crypto/tokens, so for them the guarantee is
# that they never reach for ``==`` on secret material, never log, and never put
# a token in an exception message.
_MODULE_PATHS = (*_DIGEST_PATHS, _SECURITY_DIR / "pairing.py", _SECURITY_DIR / "lockout.py")

_SENSITIVE_NAMES = frozenset(
    {
        "secret",
        "normalized_secret",
        "token",
        "plaintext_token",
        "token_sha256",
        "proof",
        "client_proof",
        "server_proof",
        "hash",
        "token_hash",
        "fp",
        "fingerprint",
        "digest",
        "compute_proof",
        "hash_token",
    }
)


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _identifiers(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            names.add(child.id.lower())
        elif isinstance(child, ast.Attribute):
            names.add(child.attr.lower())
    return names


@pytest.mark.parametrize("path", _MODULE_PATHS, ids=lambda path: path.name)
def test_no_equality_comparison_on_secrets_or_hashes(path: Path) -> None:
    offenders = [
        node.lineno
        for node in ast.walk(_parse(path))
        if isinstance(node, ast.Compare)
        and any(isinstance(operator, (ast.Eq, ast.NotEq)) for operator in node.ops)
        and _identifiers(node) & _SENSITIVE_NAMES
    ]

    assert offenders == [], f"use hmac.compare_digest instead at {path}:{offenders}"


@pytest.mark.parametrize("path", _DIGEST_PATHS, ids=lambda path: path.name)
def test_modules_use_compare_digest(path: Path) -> None:
    calls = [
        node
        for node in ast.walk(_parse(path))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "compare_digest"
    ]

    assert calls, f"{path} must compare secret material with hmac.compare_digest"


@pytest.mark.parametrize("path", _MODULE_PATHS, ids=lambda path: path.name)
def test_modules_do_not_import_logging(path: Path) -> None:
    imported_roots = {
        alias.name.split(".")[0]
        for node in ast.walk(_parse(path))
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_roots.update(
        (node.module or "").split(".")[0]
        for node in ast.walk(_parse(path))
        if isinstance(node, ast.ImportFrom)
    )

    assert "logging" not in imported_roots


@pytest.mark.parametrize("path", _MODULE_PATHS, ids=lambda path: path.name)
def test_exception_messages_do_not_embed_tokens(path: Path) -> None:
    messages = [
        child.value.lower()
        for node in ast.walk(_parse(path))
        if isinstance(node, ast.Raise)
        for child in ast.walk(node)
        if isinstance(child, ast.Constant) and isinstance(child.value, str)
    ]

    for message in messages:
        assert "token" not in message
