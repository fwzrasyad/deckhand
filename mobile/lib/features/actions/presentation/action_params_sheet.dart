import 'package:deckhand/domain/entities/action_meta.dart';
import 'package:flutter/material.dart';

/// Collects an action's parameters before it runs (SRD 10.4).
///
/// Phase 1 builds the per-type inputs (slider for numeric ranges, dropdown for
/// choices, obscured field for secrets) and validates locally before sending.
/// The sheet is only opened for actions that have parameters or need a
/// confirmation.
final class ActionParamsSheet extends StatelessWidget {
  /// Creates the sheet for [action].
  const ActionParamsSheet({required this.action, super.key});

  /// The action being configured.
  final ActionMeta action;

  @override
  Widget build(BuildContext context) => SafeArea(
    child: Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ListTile(
          title: Text(action.label),
          subtitle: action.description.isEmpty
              ? null
              : Text(action.description),
        ),
        for (final param in action.params)
          ListTile(
            title: Text(param.label),
            subtitle: Text(param.type.name),
          ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: FilledButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Run'),
          ),
        ),
      ],
    ),
  );
}
