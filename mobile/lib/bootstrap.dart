import 'package:deckhand/app/app.dart';
import 'package:deckhand/core/logging/app_logger.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// The composition root of the mobile app.
///
/// Binds the Flutter engine, routes uncaught errors into the logger, and mounts
/// the app inside a `ProviderScope`. Repositories and services are overridden
/// here (Phase 1) so widgets never construct them.
void bootstrap() {
  WidgetsFlutterBinding.ensureInitialized();
  final logger = AppLogger();
  FlutterError.onError = (details) => logger.error(
    'Uncaught Flutter error',
    error: details.exception,
    stackTrace: details.stack,
  );
  runApp(const ProviderScope(child: DeckhandApp()));
}
