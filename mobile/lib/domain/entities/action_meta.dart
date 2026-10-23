import 'package:deckhand/domain/entities/action_param_spec.dart';

/// How a run's output is attached to the phone (SRD 7.6).
enum RunMode {
  /// Line-oriented output delivered as `PROCESS_LOG` batches.
  pipe,

  /// Raw terminal output delivered as `PTY_DATA`.
  pty,
}

/// The public description of an action, as sent in `SNAPSHOT`.
///
/// This is `ActionMeta` in the protocol: the `run` block (argv, cwd, env) is
/// never sent to the phone (SRD SEC-001, SEC-002).
final class ActionMeta {
  /// Creates an action description.
  const ActionMeta({
    required this.id,
    required this.label,
    this.icon = 'bolt',
    this.category = '',
    this.description = '',
    this.mode = RunMode.pipe,
    this.interactive = false,
    this.confirm = false,
    this.parallel = false,
    this.hasStatus = false,
    this.params = const [],
  });

  /// Owner-defined identifier, for example `docker-up`.
  final String id;

  /// Button label, at most 32 characters.
  final String label;

  /// Built-in icon key or `material:<name>`.
  final String icon;

  /// Optional grouping label shown in the deck.
  final String category;

  /// Optional description shown in the action sheet.
  final String description;

  /// Whether output arrives as lines or as a raw terminal stream.
  final RunMode mode;

  /// Whether the run accepts stdin. Pty runs are always interactive.
  final bool interactive;

  /// Whether the phone must ask for confirmation before running.
  final bool confirm;

  /// Whether the daemon allows this action to run concurrently with itself.
  final bool parallel;

  /// Whether the action has a status probe, so the card can show a colour.
  final bool hasStatus;

  /// Parameter declarations, in display order.
  final List<ActionParamSpec> params;
}
