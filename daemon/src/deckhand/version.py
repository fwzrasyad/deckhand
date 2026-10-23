"""Product identity and version constants.

The working name lives here so a rename touches only this file, the mDNS
service type, and the ``deckhand://`` URI scheme (SRD Section 1).
"""

from typing import Final

PRODUCT_NAME: Final = "deckhand"
PROTOCOL_NAME: Final = "deckhand.v1"
MDNS_SERVICE_TYPE: Final = "_deckhand._tcp.local."
URI_SCHEME: Final = "deckhand"

__version__: Final = "0.1.0"
