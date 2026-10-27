"""Pairing window state machine (SRD 4.4, SEC-007, SEC-010, SEC-016)."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

import pytest

from deckhand.core.clock import FakeClock
from deckhand.protocol.errors import ErrorCode
from deckhand.security.crypto import b64url_encode, compute_proof, normalize_secret, verify_proof
from deckhand.security.lockout import LockoutTracker
from deckhand.security.pairing import (
    COOLDOWN_SEC,
    MAX_FAILED_PROOFS,
    MAX_PENDING_CHALLENGES,
    WINDOW_SEC,
    Challenge,
    CloseReason,
    PairingFailure,
    PairingSuccess,
    PairingUnavailableError,
    PairingWindow,
    WindowState,
)
from deckhand.security.tokens import verify_token

FP = "ab" * 32
IP = "192.168.1.50"
DEVICE_ID = "3f2b1c4d-5e6f-4a7b-8c9d-0e1f2a3b4c5d"
CLIENT_NONCE = "AAECAwQFBgcICQoLDA0ODw"
WRONG_PROOF = b64url_encode(bytes(32))
GROUPED_SECRET = re.compile(r"[0-9A-HJKMNP-TV-Z]{4}-[0-9A-HJKMNP-TV-Z]{4}-[0-9A-HJKMNP-TV-Z]{4}")


class CountingRng:
    """Deterministic, never-repeating byte source for tests."""

    def __init__(self) -> None:
        self._count = 0

    def __call__(self, size: int) -> bytes:
        self._count += 1
        return hashlib.sha256(self._count.to_bytes(4, "big")).digest()[:size]


class Recorder:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, ...]] = []

    def window_opened(self, expires_in_sec: float) -> None:
        self.calls.append(("opened", expires_in_sec))

    def window_closed(self, reason: CloseReason) -> None:
        self.calls.append(("closed", reason))

    def pair_success(self, device_id: str, source_ip: str) -> None:
        self.calls.append(("success", device_id, source_ip))

    def pair_failure(self, code: ErrorCode, source_ip: str) -> None:
        self.calls.append(("failure", code, source_ip))


@dataclass
class Rig:
    clock: FakeClock = field(default_factory=FakeClock)
    events: Recorder = field(default_factory=Recorder)
    lockout: LockoutTracker = field(init=False)
    window: PairingWindow = field(init=False)

    def __post_init__(self) -> None:
        self.lockout = LockoutTracker(self.clock)
        self.window = PairingWindow(
            self.clock, self.lockout, FP, rng=CountingRng(), events=self.events
        )


def ip(n: int) -> str:
    return f"10.1.0.{n}"


def start(rig: Rig, source: str = IP, *, device_id: str = DEVICE_ID) -> Challenge:
    result = rig.window.begin(source, device_id, "Pixel 8", CLIENT_NONCE)
    assert isinstance(result, Challenge), result
    return result


def good_proof(secret: str, challenge: Challenge, *, fp: str = FP) -> str:
    return compute_proof(secret, "client", fp, CLIENT_NONCE, challenge.server_nonce, DEVICE_ID)


def pair_ok(rig: Rig, secret: str, source: str = IP) -> PairingSuccess:
    challenge = start(rig, source)
    result = rig.window.submit(source, challenge.handle, good_proof(secret, challenge))
    assert isinstance(result, PairingSuccess), result
    return result


def fail_once(rig: Rig, source: str) -> PairingFailure:
    challenge = start(rig, source)
    result = rig.window.submit(source, challenge.handle, WRONG_PROOF)
    assert isinstance(result, PairingFailure)
    return result


def test_spec_constants() -> None:
    assert (WINDOW_SEC, MAX_FAILED_PROOFS, COOLDOWN_SEC) == (120.0, 5, 30.0)


# ── Window lifecycle ───────────────────────────────────────────────────────


def test_a_new_window_is_closed() -> None:
    rig = Rig()

    assert rig.window.state is WindowState.CLOSED
    assert not rig.window.is_open
    assert rig.window.remaining_sec == 0.0
    assert repr(rig.window) == "PairingWindow(state='closed')"


def test_open_returns_a_grouped_secret_and_a_120_second_window() -> None:
    rig = Rig()

    opened = rig.window.open()

    assert GROUPED_SECRET.fullmatch(opened.secret)
    assert opened.expires_in_sec == pytest.approx(120.0)
    assert rig.window.is_open
    assert rig.events.calls == [("opened", 120.0)]


def test_opening_an_open_window_returns_the_same_window() -> None:
    rig = Rig()
    first = rig.window.open()
    rig.clock.advance(20)

    second = rig.window.open()

    assert second.secret == first.secret
    assert second.expires_in_sec == pytest.approx(100.0)
    assert rig.events.calls == [("opened", 120.0)]


def test_window_expires_at_exactly_120_seconds() -> None:
    rig = Rig()
    rig.window.open()

    rig.clock.advance(119.9)
    assert rig.window.is_open
    rig.clock.advance(0.1)

    assert rig.window.state is WindowState.CLOSED
    assert rig.events.calls[-1] == ("closed", CloseReason.EXPIRED)


def test_expire_if_due_delivers_the_closed_event_without_other_calls() -> None:
    rig = Rig()
    rig.window.open()
    rig.clock.advance(500)

    rig.window.expire_if_due()
    rig.window.expire_if_due()

    assert rig.events.calls.count(("closed", CloseReason.EXPIRED)) == 1


def test_a_reopened_window_gets_a_new_secret() -> None:
    rig = Rig()
    first = rig.window.open()
    rig.clock.advance(WINDOW_SEC)

    second = rig.window.open()

    assert second.secret != first.secret
    assert rig.window.is_open


def test_cancel_closes_an_open_window() -> None:
    rig = Rig()
    rig.window.open()

    assert rig.window.cancel() is True

    assert rig.window.state is WindowState.CLOSED
    assert rig.events.calls[-1] == ("closed", CloseReason.CANCELLED)
    assert rig.window.cancel() is False


def test_cancel_does_nothing_during_cooldown() -> None:
    rig = Rig()
    rig.window.open()
    for n in range(MAX_FAILED_PROOFS):
        fail_once(rig, ip(n))

    assert rig.window.cancel() is False
    assert rig.window.state is WindowState.COOLDOWN


# ── begin() ────────────────────────────────────────────────────────────────


def test_begin_on_a_closed_window_is_refused_and_counts_against_the_ip() -> None:
    rig = Rig()

    result = rig.window.begin(IP, DEVICE_ID, "Pixel 8", CLIENT_NONCE)

    assert result == PairingFailure(ErrorCode.PAIR_WINDOW_CLOSED)
    assert rig.events.calls == [("failure", ErrorCode.PAIR_WINDOW_CLOSED, IP)]
    for _ in range(MAX_FAILED_PROOFS - 1):
        rig.window.begin(IP, DEVICE_ID, "Pixel 8", CLIENT_NONCE)
    assert rig.lockout.check(IP).blocked


def test_begin_returns_a_fresh_server_nonce_per_request() -> None:
    rig = Rig()
    rig.window.open()

    first = start(rig)
    second = start(rig)

    assert len(first.server_nonce) == 22
    assert first.server_nonce != second.server_nonce
    assert first.handle != second.handle


@pytest.mark.parametrize(
    "device_id",
    [
        "",
        "not-a-uuid",
        DEVICE_ID.upper(),
        DEVICE_ID.replace("-", ""),
        "{" + DEVICE_ID + "}",
        "urn:uuid:" + DEVICE_ID,
    ],
)
def test_begin_rejects_device_ids_that_are_not_canonical_uuids(device_id: str) -> None:
    rig = Rig()
    rig.window.open()

    result = rig.window.begin(IP, device_id, "Pixel 8", CLIENT_NONCE)

    assert result == PairingFailure(ErrorCode.PAIR_BAD_PROOF)


@pytest.mark.parametrize(
    "nonce",
    [
        "",
        "AAECAwQFBgcICQoLDA0ODw==",
        "AAECAwQFBgcICQoLDA0O",
        "AAECAwQFBgcICQoLDA0ODwAA",
        "a+b/" * 5,
    ],
)
def test_begin_rejects_nonces_that_are_not_16_unpadded_base64url_bytes(nonce: str) -> None:
    rig = Rig()
    rig.window.open()

    result = rig.window.begin(IP, DEVICE_ID, "Pixel 8", nonce)

    assert result == PairingFailure(ErrorCode.PAIR_BAD_PROOF)


def test_malformed_requests_count_against_the_ip_but_not_the_window() -> None:
    rig = Rig()
    secret = rig.window.open().secret
    for n in range(MAX_FAILED_PROOFS):
        rig.window.begin(ip(n), "garbage", "Pixel 8", CLIENT_NONCE)

    assert rig.window.is_open
    assert rig.lockout.check(ip(0)).blocked is False  # one failure each
    for _ in range(MAX_FAILED_PROOFS):
        rig.window.begin(IP, "garbage", "Pixel 8", CLIENT_NONCE)
    assert rig.lockout.check(IP).blocked
    assert isinstance(pair_ok(rig, secret, ip(99)), PairingSuccess)


def test_only_the_newest_pending_challenges_are_kept() -> None:
    rig = Rig()
    secret = rig.window.open().secret
    challenges = [start(rig) for _ in range(MAX_PENDING_CHALLENGES + 1)]

    evicted = rig.window.submit(IP, challenges[0].handle, good_proof(secret, challenges[0]))
    newest = rig.window.submit(IP, challenges[-1].handle, good_proof(secret, challenges[-1]))

    assert evicted == PairingFailure(ErrorCode.PAIR_BAD_PROOF)
    assert isinstance(newest, PairingSuccess)


# ── submit() ───────────────────────────────────────────────────────────────


def test_a_correct_proof_pairs_the_device_and_closes_the_window() -> None:
    rig = Rig()
    secret = rig.window.open().secret
    challenge = start(rig)

    result = rig.window.submit(IP, challenge.handle, good_proof(secret, challenge))

    assert isinstance(result, PairingSuccess)
    assert result.device_id == DEVICE_ID
    assert result.device_name == "Pixel 8"
    assert re.fullmatch(r"[0-9a-f]{64}", result.device_token)
    assert verify_token(result.device_token, result.token_sha256)
    assert rig.window.state is WindowState.CLOSED
    assert rig.events.calls == [
        ("opened", 120.0),
        ("closed", CloseReason.SUCCESS),
        ("success", DEVICE_ID, IP),
    ]


def test_server_proof_verifies_on_the_phone_side() -> None:
    rig = Rig()
    secret = rig.window.open().secret
    challenge = start(rig)

    result = rig.window.submit(IP, challenge.handle, good_proof(secret, challenge))

    assert isinstance(result, PairingSuccess)
    assert verify_proof(
        secret, "server", FP, CLIENT_NONCE, challenge.server_nonce, DEVICE_ID, result.server_proof
    )
    assert len(result.server_proof) == 43


def test_a_typed_secret_with_lookalikes_and_spaces_pairs() -> None:
    rig = Rig()
    secret = rig.window.open().secret
    typed = secret.lower().replace("-", " ").replace("1", "l").replace("0", "o")
    challenge = start(rig)

    result = rig.window.submit(IP, challenge.handle, good_proof(typed, challenge))

    assert isinstance(result, PairingSuccess)


def test_every_pairing_gets_a_different_token() -> None:
    rig = Rig()
    tokens = []
    for n in range(3):
        secret = rig.window.open().secret
        tokens.append(pair_ok(rig, secret, ip(n)).device_token)

    assert len(set(tokens)) == 3


def test_a_wrong_proof_is_refused_and_the_window_stays_open() -> None:
    rig = Rig()
    rig.window.open()

    result = fail_once(rig, IP)

    assert result == PairingFailure(ErrorCode.PAIR_BAD_PROOF)
    assert rig.window.is_open


def test_each_challenge_allows_one_proof_attempt() -> None:
    rig = Rig()
    secret = rig.window.open().secret
    challenge = start(rig)
    rig.window.submit(IP, challenge.handle, WRONG_PROOF)

    retry = rig.window.submit(IP, challenge.handle, good_proof(secret, challenge))

    assert retry == PairingFailure(ErrorCode.PAIR_BAD_PROOF)


def test_an_unknown_handle_counts_as_a_failed_proof() -> None:
    rig = Rig()
    rig.window.open()

    result = rig.window.submit(IP, "no-such-handle", WRONG_PROOF)

    assert result == PairingFailure(ErrorCode.PAIR_BAD_PROOF)
    for n in range(MAX_FAILED_PROOFS - 1):
        rig.window.submit(ip(n), "no-such-handle", WRONG_PROOF)
    assert rig.window.state is WindowState.COOLDOWN


@pytest.mark.parametrize("proof", ["", "!!!", "AAAA=", "A" * 44, "A" * 42, "é" * 43])
def test_malformed_proofs_fail_cleanly(proof: str) -> None:
    rig = Rig()
    rig.window.open()
    challenge = start(rig)

    result = rig.window.submit(IP, challenge.handle, proof)

    assert result == PairingFailure(ErrorCode.PAIR_BAD_PROOF)


def test_a_proof_for_a_different_challenge_is_refused() -> None:
    rig = Rig()
    secret = rig.window.open().secret
    first = start(rig)
    second = start(rig)

    result = rig.window.submit(IP, second.handle, good_proof(secret, first))

    assert result == PairingFailure(ErrorCode.PAIR_BAD_PROOF)


def test_a_handle_from_an_earlier_window_is_useless_in_a_new_one() -> None:
    rig = Rig()
    old_secret = rig.window.open().secret
    old = start(rig)
    rig.clock.advance(WINDOW_SEC)
    new_secret = rig.window.open().secret

    result = rig.window.submit(IP, old.handle, good_proof(new_secret, old))

    assert result == PairingFailure(ErrorCode.PAIR_BAD_PROOF)
    assert new_secret != old_secret


# ── Failure limits ─────────────────────────────────────────────────────────


def test_the_fifth_failed_proof_closes_the_window_and_starts_the_cooldown() -> None:
    rig = Rig()
    rig.window.open()
    for n in range(MAX_FAILED_PROOFS - 1):
        assert fail_once(rig, ip(n)).code is ErrorCode.PAIR_BAD_PROOF
        assert rig.window.is_open

    assert fail_once(rig, ip(9)).code is ErrorCode.PAIR_BAD_PROOF

    assert rig.window.state is WindowState.COOLDOWN
    assert rig.window.remaining_sec == pytest.approx(30.0)
    assert rig.events.calls[-1] == ("closed", CloseReason.TOO_MANY_FAILURES)


def test_during_the_cooldown_everything_is_locked_out_and_open_is_refused() -> None:
    rig = Rig()
    rig.window.open()
    for n in range(MAX_FAILED_PROOFS):
        fail_once(rig, ip(n))
    rig.clock.advance(10)

    refused = rig.window.begin(ip(50), DEVICE_ID, "Pixel 8", CLIENT_NONCE)
    with pytest.raises(PairingUnavailableError) as caught:
        rig.window.open()

    assert isinstance(refused, PairingFailure)
    assert refused.code is ErrorCode.PAIR_LOCKED_OUT
    assert refused.retry_after_sec == pytest.approx(20.0)
    assert caught.value.retry_after_sec == pytest.approx(20.0)
    assert "cooling down" in str(caught.value)


def test_after_the_cooldown_a_new_window_starts_with_a_clean_count() -> None:
    rig = Rig()
    rig.window.open()
    for n in range(MAX_FAILED_PROOFS):
        fail_once(rig, ip(n))
    rig.clock.advance(COOLDOWN_SEC)
    assert rig.window.state is WindowState.CLOSED

    secret = rig.window.open().secret
    for n in range(MAX_FAILED_PROOFS - 1):
        fail_once(rig, ip(20 + n))

    assert rig.window.is_open
    assert isinstance(pair_ok(rig, secret, ip(40)), PairingSuccess)


def test_five_failures_from_one_ip_also_block_that_ip() -> None:
    rig = Rig()
    rig.window.open()
    for _ in range(MAX_FAILED_PROOFS):
        fail_once(rig, IP)
    rig.clock.advance(COOLDOWN_SEC)

    refused = rig.window.begin(IP, DEVICE_ID, "Pixel 8", CLIENT_NONCE)

    assert isinstance(refused, PairingFailure)
    assert refused.code is ErrorCode.PAIR_LOCKED_OUT
    assert refused.retry_after_sec == pytest.approx(30.0)  # the IP block outlasts the cooldown


def test_a_blocked_ip_cannot_burn_the_windows_attempts() -> None:
    rig = Rig()
    secret = rig.window.open().secret
    for _ in range(MAX_FAILED_PROOFS):
        rig.lockout.record_failure(IP)

    for _ in range(50):
        refused = rig.window.submit(IP, "whatever", WRONG_PROOF)
        assert isinstance(refused, PairingFailure)
        assert refused.code is ErrorCode.PAIR_LOCKED_OUT
        assert refused.retry_after_sec is not None

    assert rig.window.is_open
    assert isinstance(pair_ok(rig, secret, ip(1)), PairingSuccess)


def test_submit_on_a_closed_window_is_refused_even_with_a_valid_looking_proof() -> None:
    rig = Rig()
    secret = rig.window.open().secret
    challenge = start(rig)
    rig.window.cancel()

    result = rig.window.submit(IP, challenge.handle, good_proof(secret, challenge))

    assert result == PairingFailure(ErrorCode.PAIR_WINDOW_CLOSED)


def test_an_invalid_source_address_is_a_programming_error() -> None:
    rig = Rig()
    rig.window.open()

    with pytest.raises(ValueError, match="not a valid IP"):
        rig.window.begin("not-an-ip", DEVICE_ID, "Pixel 8", CLIENT_NONCE)


# ── Secrecy ────────────────────────────────────────────────────────────────


def test_secrets_and_tokens_are_hidden_from_repr_and_str() -> None:
    rig = Rig()
    opened = rig.window.open()
    challenge = start(rig)
    result = rig.window.submit(IP, challenge.handle, good_proof(opened.secret, challenge))
    assert isinstance(result, PairingSuccess)

    shown = " ".join(
        (
            repr(opened),
            str(opened),
            repr(challenge),
            repr(result),
            str(result),
            repr(rig.window),
        )
    )

    assert opened.secret not in shown
    assert normalize_secret(opened.secret) not in shown
    assert result.device_token not in shown
    assert challenge.handle not in shown


def test_cooldown_error_message_carries_no_secret() -> None:
    rig = Rig()
    secret = rig.window.open().secret
    for n in range(MAX_FAILED_PROOFS):
        fail_once(rig, ip(n))

    with pytest.raises(PairingUnavailableError) as caught:
        rig.window.open()

    assert secret not in str(caught.value)
    assert normalize_secret(secret) not in str(caught.value)
    assert secret not in repr(caught.value.details)


# ── Construction and defaults ──────────────────────────────────────────────


@pytest.mark.parametrize("fingerprint", ["", "AB" * 32, "ab" * 31, "zz" * 32, "ab" * 33])
def test_fingerprint_must_be_64_lowercase_hex(fingerprint: str) -> None:
    clock = FakeClock()

    with pytest.raises(ValueError, match="64 lowercase hex"):
        PairingWindow(clock, LockoutTracker(clock), fingerprint)


@pytest.mark.parametrize(
    "kwargs",
    [{"window_sec": 0}, {"cooldown_sec": 0}, {"max_failed_proofs": 0}],
)
def test_limits_must_be_positive(kwargs: dict[str, Any]) -> None:
    clock = FakeClock()

    with pytest.raises(ValueError, match="positive"):
        PairingWindow(clock, LockoutTracker(clock), FP, **kwargs)


def test_default_random_source_and_no_event_observer_work_end_to_end() -> None:
    clock = FakeClock()
    window = PairingWindow(clock, LockoutTracker(clock), FP)
    assert window.begin(IP, DEVICE_ID, "Pixel 8", CLIENT_NONCE) == PairingFailure(
        ErrorCode.PAIR_WINDOW_CLOSED
    )
    first = window.open()
    window.cancel()
    second = window.open()
    challenge = window.begin(IP, DEVICE_ID, "Pixel 8", CLIENT_NONCE)
    assert isinstance(challenge, Challenge)

    result = window.submit(IP, challenge.handle, good_proof(second.secret, challenge))

    assert first.secret != second.secret
    assert isinstance(result, PairingSuccess)
    assert window.state is WindowState.CLOSED
    window.expire_if_due()
