# Pairing test vectors

`pairing.json` is the shared contract for the SRD 4.4 pairing proof. Both the
daemon (`deckhand.security.crypto`) and the Dart app are tested against these
exact values, so a mismatch on either side fails CI.

The expected values were **not** produced by the code under test. They were
computed once, independently, by a throwaway script using only `hmac`,
`hashlib` and `base64` from the Python standard library (plus `json` to write
the file). The script was not committed; the results below are literals on
purpose, so a bug in the implementation cannot silently redefine the contract.

## Fields

| Field | Meaning |
| :-- | :-- |
| `name` | Stable case identifier, also used as the pytest id. |
| `notes` | Why the case exists. |
| `secret_input` | The secret as the user typed it (may be lowercase, spaced, hyphenated, or use I/L/O). |
| `normalized_secret` | Canonical 12-character Crockford Base32 form (SRD 4.4). |
| `cert_der_hex` | Certificate DER bytes as hex. Some cases use uppercase hex on purpose. |
| `fingerprint` | Lowercase hex SHA-256 of those DER bytes. |
| `client_nonce`, `server_nonce` | 16 random bytes as 22-character unpadded base64url. |
| `device_id` | Random UUIDv4 string. |
| `client_transcript`, `server_transcript` | Exact UTF-8 strings covered by the proofs. |
| `client_proof`, `server_proof` | Unpadded base64url HMAC-SHA256, keyed by `normalized_secret` as ASCII. |

The vector set includes a typed lowercase/space case with `I`/`L`/`O`
substitutions, an uppercase-hex DER case proving `fingerprint()` always yields
lowercase hex, and an all-digit secret.

## Rules

1. Do not regenerate this file from the implementation. Recompute independently
   and treat any change as a protocol change.
2. Dart and Python must both pass every case, including the negative cases in
   the test suites (wrong secret, wrong fingerprint/MITM, swapped role, altered
   nonce, altered device id, padded base64url).
