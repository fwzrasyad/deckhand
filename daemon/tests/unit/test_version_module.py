"""The identity constants the rest of the codebase reads (SRD Section 1)."""

from deckhand import version


def test_product_identity_is_centralised() -> None:
    assert version.PRODUCT_NAME == "deckhand"
    assert version.URI_SCHEME == "deckhand"
    assert version.MDNS_SERVICE_TYPE == "_deckhand._tcp.local."
    assert version.PROTOCOL_NAME == "deckhand.v1"


def test_version_is_semver() -> None:
    parts = version.__version__.split(".")

    assert len(parts) == 3
    assert all(part.isdigit() for part in parts)
