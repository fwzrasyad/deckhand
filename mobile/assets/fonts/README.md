# Fonts

Monospace fonts for the terminal and for numeric telemetry readouts belong
here.

Nothing is checked in yet. The terminal uses a platform monospace family in
Phase 0; Phase 4 bundles one font so line wrapping and column widths are
identical on Android and iOS:

- `DeckhandMono-Regular.ttf` — terminal output.
- `DeckhandMono-Bold.ttf` — prompt and emphasised lines.

Declare the family in `pubspec.yaml` and reference it from `AppTheme` when the
files land. Bundling a font means it must be licensed for redistribution; the
licence file goes in this directory.
