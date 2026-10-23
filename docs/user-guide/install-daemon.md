# Install the daemon

Purpose: Guide a user through installing and starting the Deckhand daemon on a
supported desktop OS, including autostart, firewall access, and tray
requirements (SRD Sections 2.1, 13.2; FR-D-803).

Status: outline, to be written in Phase 6.

## Supported platforms
The OS support matrix from Section 2.1.
## Install
`pipx install deckhand-daemon` or `uv tool install`, and the single-folder PyInstaller bundle for each OS (Section 13.2).
## First run
Certificate creation on first start and state-directory locations (Sections 4.5, 8.1).
## Firewall
Windows private-network prompt, Linux `ufw` rule for TCP 47800, macOS prompt on first run; guidance printed by `deckhand doctor` (Section 13.2).
## Autostart
`deckhand autostart enable` and the per-OS mechanism: Windows Run key, Linux systemd user unit with XDG fallback, macOS LaunchAgent (Section 13.2).
## Tray and headless mode
Linux needs AppIndicator libraries; otherwise the daemon runs headless with CLI access (Section 13.2, FR-D-803).
## Verify
`deckhand doctor` and opening a pairing window (Sections 9.9, 13.2).
