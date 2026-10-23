# deckhand-app

Flutter app for Deckhand: the phone-side control surface. It connects to the
daemon over an authenticated, certificate-pinned WebSocket, renders the deck of
owner-defined actions, shows live telemetry, and streams process output into a
terminal.

The phone never decides what may run. It sends an `action_id` plus parameters,
and the daemon validates everything against its local `actions.yaml` (SRD
SEC-001, SEC-003).

## Layout

| Path | Responsibility |
| :-- | :-- |
| `lib/main.dart` | Entry point; delegates to `bootstrap.dart`. |
| `lib/bootstrap.dart` | Composition root: bindings, error handling, `ProviderScope`. |
| `lib/app/` | Root widget, router, Material 3 themes, design tokens. |
| `lib/core/` | Constants, failures, result type, logger, haptics, platform facts, formatters. |
| `lib/domain/entities/` | Immutable models mirroring protocol concepts. No JSON, no Flutter. |
| `lib/domain/repositories/` | Interfaces the UI depends on; implementations live in `data/`. |
| `lib/domain/usecases/` | Operations that combine repositories and enforce client-side rules. |
| `lib/data/protocol/` | Envelope model and codec, pairing proofs; `dto/` holds generated payload models. |
| `lib/data/network/` | Client interface, pinned HTTP client, request tracking, reconnect policy. |
| `lib/data/discovery/` | mDNS host discovery interface. |
| `lib/data/storage/` | Secure storage and preferences wrappers. |
| `lib/data/repositories/` | Implementations of the domain repository interfaces. |
| `lib/features/<name>/application/` | Riverpod controllers holding feature state. |
| `lib/features/<name>/presentation/` | Screens and sheets for that feature. |
| `lib/shared/widgets/` | Widgets used by more than one feature. |
| `lib/l10n/` | `app_en.arb` plus the generated `AppLocalizations`. |

Generated localization files (`lib/l10n/app_localizations*.dart`) are rebuilt by
`flutter pub get` because `generate: true` is set in `pubspec.yaml`; they are not
edited by hand.

## Requirements

- Flutter stable (currently 3.41.x, Dart 3.11).
- Android SDK for the Android target; Xcode on macOS for the iOS target.

## Commands

```bash
flutter pub get
dart format lib/ test/
dart analyze --fatal-infos lib/ test/
flutter test
flutter run
flutter build apk --debug
```

Widget tests live in `test/widget/`, pure logic tests in `test/unit/`, and
on-device flows in `integration_test/` (run with `flutter test integration_test`
on a connected device or emulator).

## Status

Phase 0: skeleton only. Screens render real state containers but no network
traffic, storage, or pairing is wired up yet. The vertical slice (pair, connect,
run an action, watch telemetry) is Phase 1.
