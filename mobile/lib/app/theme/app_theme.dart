import 'package:deckhand/app/theme/tokens.dart';
import 'package:flutter/material.dart';

/// Material 3 light and dark themes (SRD 10.10).
abstract final class AppTheme {
  /// The light theme.
  static ThemeData get light => _themeFor(Brightness.light);

  /// The dark theme.
  static ThemeData get dark => _themeFor(Brightness.dark);

  static ThemeData _themeFor(Brightness brightness) {
    final scheme = ColorScheme.fromSeed(
      seedColor: Tokens.seed,
      brightness: brightness,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: scheme,
      cardTheme: CardThemeData(
        clipBehavior: Clip.antiAlias,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(Tokens.radiusCard),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size.fromHeight(Tokens.minTapTarget),
        ),
      ),
    );
  }
}
