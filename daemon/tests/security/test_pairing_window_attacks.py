"""Pairing attacks against the window state machine (SRD 12.4, 4.2 T2/T3, SEC-007/010/016).

Covers: five wrong proofs close the window; replayed proof rejected; wrong
fingerprint rejected on both sides; simulated MITM; expired window; second
pairing after success refused until a new window is opened. The shared
``pairing.json`` vectors are replayed through the state machine, so the daemon's
handshake is checked against values computed independently of this code.
"""

from __future__ import annotations

import hashlib
import json
import logging
import secrets
from pathlib import Path
from typing import Any

import pytest

from deckhand.core.clock import FakeClock
from deckhand.protocol.errors import ErrorCode
from deckhand.security.crypto import (
    CROCKFORD_ALPHABET,
    b64url_decode,
    b64url_encode,
    compute_proof,
    verify_proof,
)
from deckhand.security.lockout import LockoutTracker
from deckhand.security.pairing import (
    COOLDOWN_SEC,
    MAX_FAILED_PROOFS,
    WINDOW_SEC,
    Challenge,
    PairingFailure,
    PairingSuccess,
    PairingWindow,
    WindowState,
)

FP = "ab" * 32
MITM_FP = "cd" * 32
IP = "192.168.1.50"
DEVICE_ID = "3f2b1c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
CLIENT_NONCE = "AAECAwQFBgcICQoLDA0ODw"
WRONG_PROOF = b64url_encode(bytes(32))
_VECTORS = Path(__file__).resolve().parents[3] / "protocol" / "test_vectors" / "pairing.json"


class CountingRng:
    def __init__(self) -> None:
        self._count = 0

    def __call__(self, size: int) -> bytes:
        self._count += 1
        return hashlib.sha256(b"attack" + self._count.to_bytes(4, "big")).digest()[:size]


class ScriptedRng:
    """Returns exactly the bytes a vector needs, checking each requested size."""

    def __init__(self, *outputs: bytes) -> None:
        self._outputs = list(outputs)

    def __call__(self, size: int) -> bytes:
        output = self._outputs.pop(0)
        assert len(output) == size
        return output


def make_window(fp: str = FP, rng: Any = None) -> tuple[FakeClock, LockoutTracker, PairingWindow]:
    clock = FakeClock()
    lockout = LockoutTracker(clock)
    window = PairingWindow(clock, lockout, fp, rng=CountingRng() if rng is None else rng)
    return clock, lockout, window


def begin(window: PairingWindow, source: str = IP, device_id: str = DEVICE_ID) -> Challenge:
    result = window.begin(source, device_id, "Phone", CLIENT_NONCE)
    assert isinstance(result, Challenge)
    return result


def proof(secret: str, challenge: Challenge, fp: str = FP, device_id: str = DEVICE_ID) -> str:
    return compute_proof(secret, "client", fp, CLIENT_NONCE, challenge.server_nonce, device_id)


def ip(n: int) -> str:
    return f"10.2.0.{n}"


# ── Five wrong proofs close the window ─────────────────────────────────────


def test_five_wrong_proofs_close_the_window_and_the_right_secret_no_longer_works() -> None:
    _, _, window = make_window()
    secret = window.open().secret
    for n in range(MAX_FAILED_PROOFS):
        challenge = begin(window, ip(n))
        assert window.submit(ip(n), challenge.handle, WRONG_PROOF) == PairingFailure(
            ErrorCode.PAIR_BAD_PROOF
        )

    assert window.state is WindowState.COOLDOWN
    late = window.begin(ip(80), DEVICE_ID, "Phone", CLIENT_NONCE)
    assert isinstance(late, PairingFailure)
    assert late.code is ErrorCode.PAIR_LOCKED_OUT
    # Not even the right secret helps now: there is nothing to pair with.
    right = window.submit(ip(81), "any-handle", compute_proof(secret, "client", FP, "n", "m", "d"))
    assert isinstance(right, PairingFailure)
    assert right.code is ErrorCode.PAIR_LOCKED_OUT
    assert window.cancel() is False


def test_a_single_attacker_is_stopped_after_five_guesses() -> None:
    _, lockout, window = make_window()
    window.open()
    outcomes: list[ErrorCode] = []
    for _ in range(100):
        guess = "".join(secrets.choice(CROCKFORD_ALPHABET) for _ in range(12))
        started = window.begin(IP, DEVICE_ID, "Phone", CLIENT_NONCE)
        outcome = (
            window.submit(IP, started.handle, proof(guess, started))
            if isinstance(started, Challenge)
            else started
        )
        assert isinstance(outcome, PairingFailure)
        outcomes.append(outcome.code)

    assert outcomes.count(ErrorCode.PAIR_BAD_PROOF) == MAX_FAILED_PROOFS
    assert set(outcomes) <= {ErrorCode.PAIR_BAD_PROOF, ErrorCode.PAIR_LOCKED_OUT}
    assert lockout.check(IP).blocked


def test_a_blocked_ip_is_refused_until_its_block_ends() -> None:
    clock, lockout, window = make_window()
    window.open()
    for _ in range(MAX_FAILED_PROOFS):
        lockout.record_failure(IP)

    result = window.begin(IP, DEVICE_ID, "Phone", CLIENT_NONCE)

    assert isinstance(result, PairingFailure)
    assert result.code is ErrorCode.PAIR_LOCKED_OUT
    clock.advance(61)
    assert isinstance(window.begin(IP, DEVICE_ID, "Phone", CLIENT_NONCE), Challenge)


# ── Replay ─────────────────────────────────────────────────────────────────


def test_a_proof_cannot_be_replayed_on_the_same_challenge() -> None:
    _, _, window = make_window()
    secret = window.open().secret
    challenge = begin(window)
    valid = proof(secret, challenge)
    first = window.submit(IP, challenge.handle, valid)

    again = window.submit(IP, challenge.handle, valid)

    assert isinstance(first, PairingSuccess)
    assert again == PairingFailure(ErrorCode.PAIR_WINDOW_CLOSED)


def test_a_captured_proof_is_useless_in_a_later_window() -> None:
    _, _, window = make_window()
    secret = window.open().secret
    challenge = begin(window)
    captured = proof(secret, challenge)
    assert isinstance(window.submit(IP, challenge.handle, captured), PairingSuccess)

    window.open()
    replayed = begin(window, ip(7))  # same device id and client nonce, new server nonce
    result = window.submit(ip(7), replayed.handle, captured)

    assert replayed.server_nonce != challenge.server_nonce
    assert result == PairingFailure(ErrorCode.PAIR_BAD_PROOF)


# ── Wrong fingerprint and MITM ─────────────────────────────────────────────


def test_daemon_rejects_a_proof_made_over_a_different_certificate() -> None:
    _, _, window = make_window()
    secret = window.open().secret
    challenge = begin(window)

    result = window.submit(IP, challenge.handle, proof(secret, challenge, fp=MITM_FP))

    assert result == PairingFailure(ErrorCode.PAIR_BAD_PROOF)
    assert window.is_open


def test_phone_rejects_the_server_proof_when_it_saw_a_different_certificate() -> None:
    _, _, window = make_window()
    secret = window.open().secret
    challenge = begin(window)
    result = window.submit(IP, challenge.handle, proof(secret, challenge))
    assert isinstance(result, PairingSuccess)

    honest = verify_proof(
        secret, "server", FP, CLIENT_NONCE, challenge.server_nonce, DEVICE_ID, result.server_proof
    )
    intercepted = verify_proof(
        secret,
        "server",
        MITM_FP,
        CLIENT_NONCE,
        challenge.server_nonce,
        DEVICE_ID,
        result.server_proof,
    )

    assert honest
    assert not intercepted


def test_a_relaying_mitm_with_its_own_certificate_fails_without_the_secret() -> None:
    _, _, window = make_window()
    secret = window.open().secret
    challenge = begin(window)
    # The phone (typed code) accepts the MITM certificate and proves over what it saw.
    phone_proof = proof(secret, challenge, fp=MITM_FP)
    relayed = window.submit(IP, challenge.handle, phone_proof)
    assert relayed == PairingFailure(ErrorCode.PAIR_BAD_PROOF)

    # Without the secret the MITM cannot forge a proof for the daemon...
    second = begin(window, ip(3))
    forged = proof("0000-0000-0000", second)
    assert window.submit(ip(3), second.handle, forged) == PairingFailure(ErrorCode.PAIR_BAD_PROOF)
    # ...nor a server proof the phone would accept.
    fake_server = compute_proof(
        "0000-0000-0000", "server", MITM_FP, CLIENT_NONCE, challenge.server_nonce, DEVICE_ID
    )
    assert not verify_proof(
        secret, "server", MITM_FP, CLIENT_NONCE, challenge.server_nonce, DEVICE_ID, fake_server
    )


# ── Expiry and single use ──────────────────────────────────────────────────


def test_requests_after_the_window_expires_are_refused() -> None:
    clock, _, window = make_window()
    window.open()
    clock.advance(WINDOW_SEC + 1)

    result = window.begin(IP, DEVICE_ID, "Phone", CLIENT_NONCE)

    assert result == PairingFailure(ErrorCode.PAIR_WINDOW_CLOSED)


def test_a_correct_proof_that_arrives_after_expiry_is_refused() -> None:
    clock, _, window = make_window()
    secret = window.open().secret
    challenge = begin(window)
    valid = proof(secret, challenge)
    clock.advance(WINDOW_SEC)

    result = window.submit(IP, challenge.handle, valid)

    assert result == PairingFailure(ErrorCode.PAIR_WINDOW_CLOSED)


def test_second_pairing_is_refused_until_a_new_window_is_opened() -> None:
    clock, _, window = make_window()
    secret = window.open().secret
    first = begin(window, ip(1))
    second = begin(window, ip(2), device_id="4a3c2d5e-6f70-4b8c-9dae-1f2a3b4c5d6e")
    done = window.submit(ip(1), first.handle, proof(secret, first))
    assert isinstance(done, PairingSuccess)

    # The other phone was mid-handshake with a correct proof: too late.
    late = window.submit(
        ip(2),
        second.handle,
        proof(secret, second, device_id="4a3c2d5e-6f70-4b8c-9dae-1f2a3b4c5d6e"),
    )
    brand_new = window.begin(ip(3), DEVICE_ID, "Phone", CLIENT_NONCE)

    assert late == PairingFailure(ErrorCode.PAIR_WINDOW_CLOSED)
    assert brand_new == PairingFailure(ErrorCode.PAIR_WINDOW_CLOSED)

    clock.advance(1)
    new_secret = window.open().secret
    again = begin(window, ip(4))
    assert window.submit(ip(4), again.handle, proof(secret, again)) == PairingFailure(
        ErrorCode.PAIR_BAD_PROOF
    )  # the old secret is dead
    fresh = begin(window, ip(5))
    result = window.submit(ip(5), fresh.handle, proof(new_secret, fresh))
    assert isinstance(result, PairingSuccess)
    assert result.device_token != done.device_token


def test_after_a_lockout_the_owner_must_open_a_new_window() -> None:
    clock, _, window = make_window()
    window.open()
    for n in range(MAX_FAILED_PROOFS):
        challenge = begin(window, ip(n))
        window.submit(ip(n), challenge.handle, WRONG_PROOF)
    clock.advance(COOLDOWN_SEC)

    assert window.state is WindowState.CLOSED
    assert window.begin(ip(60), DEVICE_ID, "Phone", CLIENT_NONCE) == PairingFailure(
        ErrorCode.PAIR_WINDOW_CLOSED
    )


# ── Secrecy (SEC-016) ──────────────────────────────────────────────────────


def test_nothing_secret_is_logged_during_a_full_pairing(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG):
        _, _, window = make_window()
        opened = window.open()
        wrong = begin(window, ip(1))
        window.submit(ip(1), wrong.handle, WRONG_PROOF)
        challenge = begin(window)
        result = window.submit(IP, challenge.handle, proof(opened.secret, challenge))
    assert isinstance(result, PairingSuccess)

    logged = "\n".join(record.getMessage() for record in caplog.records)
    assert opened.secret not in logged
    assert opened.secret.replace("-", "") not in logged
    assert result.device_token not in logged


# ── Shared vectors through the state machine ───────────────────────────────


def _secret_as_random_bytes(normalized: str) -> bytes:
    """Random bytes that make ``generate_pairing_secret`` return ``normalized``."""
    value = 0
    for char in normalized:
        value = value * 32 + CROCKFORD_ALPHABET.index(char)
    return (value << 4).to_bytes(8, "big")


def _cases() -> list[dict[str, Any]]:
    document: Any = json.loads(_VECTORS.read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = document["cases"]
    return cases


def _vector_window(case: dict[str, Any], fp: str) -> PairingWindow:
    rng = ScriptedRng(
        _secret_as_random_bytes(case["normalized_secret"]),
        b64url_decode(case["server_nonce"]),
        bytes(16),
        bytes(32),
    )
    return make_window(fp, rng)[2]


@pytest.mark.parametrize("case", _cases(), ids=lambda case: str(case["name"]))
def test_state_machine_reproduces_the_shared_vectors(case: dict[str, Any]) -> None:
    window = _vector_window(case, case["fingerprint"])
    normalized = case["normalized_secret"]

    opened = window.open()
    challenge = window.begin(IP, case["device_id"], "Vector phone", case["client_nonce"])
    assert isinstance(challenge, Challenge)
    result = window.submit(IP, challenge.handle, case["client_proof"])

    assert opened.secret == f"{normalized[:4]}-{normalized[4:8]}-{normalized[8:]}"
    assert challenge.server_nonce == case["server_nonce"]
    assert isinstance(result, PairingSuccess)
    assert result.server_proof == case["server_proof"]
    assert result.device_token == "00" * 32


@pytest.mark.parametrize("case", _cases(), ids=lambda case: str(case["name"]))
def test_state_machine_rejects_the_vector_proof_under_a_different_fingerprint(
    case: dict[str, Any],
) -> None:
    other = case["fingerprint"][:-1] + ("0" if case["fingerprint"][-1] != "0" else "1")
    window = _vector_window(case, other)

    window.open()
    challenge = window.begin(IP, case["device_id"], "Vector phone", case["client_nonce"])
    assert isinstance(challenge, Challenge)
    result = window.submit(IP, challenge.handle, case["client_proof"])

    assert result == PairingFailure(ErrorCode.PAIR_BAD_PROOF)
