import 'package:flutter/material.dart';

/// Design tokens shared by every widget (SRD 10.10).
///
/// Material 3 roles handle colour; these constants cover the spacing and radii
/// the deck grid and terminal chrome need to stay consistent.
abstract final class Tokens {
  /// 4 px, the base unit of the spacing scale.
  static const double spaceXs = 4;

  /// 8 px.
  static const double spaceSm = 8;

  /// 12 px.
  static const double spaceMd = 12;

  /// 16 px.
  static const double spaceLg = 16;

  /// 24 px.
  static const double spaceXl = 24;

  /// Corner radius for action cards.
  static const double radiusCard = 16;

  /// Corner radius for sheets and dialogs.
  static const double radiusSheet = 24;

  /// Minimum tap target, per the accessibility pass (SRD 10.10).
  static const double minTapTarget = 48;

  /// Border width of a card whose status probe is active.
  static const double statusRing = 2;

  /// Seed colour for the Material 3 colour scheme.
  static const Color seed = Color(0xFF3D7EFF);
}
