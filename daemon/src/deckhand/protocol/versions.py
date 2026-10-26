"""Protocol version negotiation helpers (SRD 7.3).

Layer 1. The daemon advertises :data:`SUPPORTED_VERSIONS` in HELLO and the
client selects one in AUTH. Negotiation picks the highest version both sides
support; no overlap is reported as ``PROTO_VERSION_UNSUPPORTED``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from .errors import ErrorCode, ProtocolError

SUPPORTED_VERSIONS: Final[tuple[int, ...]] = (1,)
CURRENT_VERSION: Final[int] = SUPPORTED_VERSIONS[-1]


def is_supported(version: object) -> bool:
    """Return whether ``version`` is one of :data:`SUPPORTED_VERSIONS`."""
    return (
        isinstance(version, int) and not isinstance(version, bool) and version in SUPPORTED_VERSIONS
    )


def negotiate_version(
    client_versions: Iterable[int],
    server_versions: Iterable[int] = SUPPORTED_VERSIONS,
) -> int:
    """Return the highest version supported by both sides.

    ``client_versions`` is the list received in HELLO or the single version in
    AUTH; ``server_versions`` defaults to this daemon's list. Non-integer
    entries are ignored. Raises :class:`ProtocolError` with
    ``PROTO_VERSION_UNSUPPORTED`` when there is no overlap or when the input
    is not a usable list of versions.
    """
    try:
        client = {
            version
            for version in client_versions
            if isinstance(version, int) and not isinstance(version, bool)
        }
        server = {
            version
            for version in server_versions
            if isinstance(version, int) and not isinstance(version, bool)
        }
    except Exception as exc:
        raise ProtocolError(
            ErrorCode.PROTO_VERSION_UNSUPPORTED,
            "No compatible protocol version",
        ) from exc

    common = client & server
    if not common:
        raise ProtocolError(
            ErrorCode.PROTO_VERSION_UNSUPPORTED,
            "No compatible protocol version",
        )
    return max(common)


__all__ = [
    "CURRENT_VERSION",
    "SUPPORTED_VERSIONS",
    "is_supported",
    "negotiate_version",
]
