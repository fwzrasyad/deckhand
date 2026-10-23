# Tray assets

Icon files for the tray application live here. `tray/icons.py` maps each tray
state to one of these files:

| State | File | Meaning |
| :-- | :-- | :-- |
| `idle` | `idle.png` | Running, no sessions |
| `connected` | `connected.png` | At least one authenticated session |
| `pairing` | `pairing.png` | Pairing window open |
| `error` | `error.png` | A service failed; see the log |

Icons are 32x32 PNG with an alpha channel, plus `@2x` variants at 64x64.
Binary assets are added in Phase 3 alongside the tray implementation.
