# Windows packaging notes

The PyInstaller bundle is a single folder (`daemon/dist/deckhand/`) containing
`deckhand.exe`. There is no installer yet; this file records what the Phase 6
installer must do.

## Install

1. Copy `dist/deckhand/` to `%LOCALAPPDATA%\Programs\Deckhand\`.
2. Add that directory to the user `PATH` so `deckhand` resolves in a terminal.
3. Run `deckhand doctor` once. It prints the exact Defender Firewall rule.

## Firewall

The first bind triggers the Windows Defender Firewall prompt. Allow **private
networks only** (SRD 13.2). To add the rule from an elevated shell instead:

```powershell
New-NetFirewallRule -DisplayName "Deckhand" -Direction Inbound `
  -Protocol TCP -LocalPort 47800 -Profile Private -Action Allow
```

## Autostart

`deckhand autostart enable` writes
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run\Deckhand` pointing at
`deckhand.exe serve`. The daemon runs as a normal user process; there is no
Windows service mode in v1 (SRD 1.3).

## Not yet done (Phase 6)

- Installer (Inno Setup or MSIX) with an uninstaller that removes the Run key,
  the firewall rule, and `%APPDATA%\Deckhand` / `%LOCALAPPDATA%\Deckhand`.
- Code signing of `deckhand.exe` and the installer.
- Icon and version resources on the executable.
