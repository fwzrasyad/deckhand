/// The value type of an action parameter, as declared in `actions.yaml`.
///
/// The phone may pre-validate against this, but the daemon is authoritative
/// (SRD 7.6, SEC-003).
enum ParamType {
  /// Free-form text.
  string,

  /// Whole number.
  integer,

  /// Decimal number.
  number,

  /// `true` or `false`.
  boolean,

  /// One of [ActionParamSpec.choices].
  choice,
}

/// One parameter of an action (`ParamSpec` in the protocol, SRD 7.6).
final class ActionParamSpec {
  /// Creates a parameter specification.
  const ActionParamSpec({
    required this.name,
    required this.label,
    required this.type,
    this.isRequired = false,
    this.isSecret = false,
    this.allowLeadingDash = false,
    this.defaultValue,
    this.choices = const [],
    this.min,
    this.max,
    this.maxLength,
    this.pattern,
    this.placeholder,
  });

  /// Machine name, safe to use as an identifier.
  final String name;

  /// Label shown in the parameter sheet.
  final String label;

  /// Value type.
  final ParamType type;

  /// Whether the user must supply a value.
  final bool isRequired;

  /// Whether the value is masked in the UI and redacted from logs.
  final bool isSecret;

  /// Whether a value may start with `-` (argument-injection guard, SRD 8.3).
  final bool allowLeadingDash;

  /// Value used when the sheet opens, if any.
  final String? defaultValue;

  /// Allowed values for [ParamType.choice].
  final List<String> choices;

  /// Minimum value for numeric types.
  final num? min;

  /// Maximum value for numeric types.
  final num? max;

  /// Maximum length for string values.
  final int? maxLength;

  /// Full-match regular expression for string values.
  final String? pattern;

  /// Hint text shown in an empty field.
  final String? placeholder;
}
