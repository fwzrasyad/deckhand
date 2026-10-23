import 'package:deckhand/domain/entities/action_meta.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the action whose parameter sheet is open, if any.
///
/// Actions without parameters run straight from the card; only multi-param or
/// confirming actions open the sheet (SRD 10.4).
final class ActionSheetController extends Notifier<ActionMeta?> {
  @override
  ActionMeta? build() => null;

  /// The action whose sheet is open, if any.
  ActionMeta? get action => state;

  /// Opens the sheet for the given action.
  set action(ActionMeta value) => state = value;

  /// Closes the sheet.
  void close() => state = null;
}

/// Sheet state for the action parameter sheet.
final actionSheetControllerProvider =
    NotifierProvider<ActionSheetController, ActionMeta?>(
      ActionSheetController.new,
    );
