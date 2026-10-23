import 'package:deckhand/app/router.dart';
import 'package:deckhand/app/theme/app_theme.dart';
import 'package:deckhand/core/constants/app_constants.dart';
import 'package:deckhand/l10n/app_localizations.dart';
import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// The root widget: theme, localization, and the router.
final class DeckhandApp extends StatefulWidget {
  /// Creates the app.
  const DeckhandApp({super.key});

  @override
  State<DeckhandApp> createState() => _DeckhandAppState();
}

final class _DeckhandAppState extends State<DeckhandApp> {
  late final GoRouter _router = AppRouter.create();

  @override
  void dispose() {
    _router.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => MaterialApp.router(
    title: AppConstants.productName,
    debugShowCheckedModeBanner: false,
    theme: AppTheme.light,
    darkTheme: AppTheme.dark,
    routerConfig: _router,
    localizationsDelegates: AppLocalizations.localizationsDelegates,
    supportedLocales: AppLocalizations.supportedLocales,
  );
}
