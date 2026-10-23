/// How urgent an alert is (SRD 7.6).
enum AlertSeverity {
  /// Informational; no haptic.
  info,

  /// Warning; light haptic.
  warning,

  /// Critical; strong haptic and a banner.
  critical,
}

/// The comparison an alert rule applies to a metric.
enum AlertOp {
  /// Greater than.
  greaterThan,

  /// Greater than or equal.
  greaterOrEqual,

  /// Less than.
  lessThan,

  /// Less than or equal.
  lessOrEqual,
}

/// A rule the daemon evaluates against telemetry (SRD 7.6, 8.5).
///
/// The phone may edit rules when `security.remote_alert_edit` is on; the daemon
/// persists them.
final class AlertRule {
  /// Creates a rule.
  const AlertRule({
    required this.id,
    required this.metric,
    required this.op,
    required this.threshold,
    this.forSeconds = 0,
    this.clearMargin = 0,
    this.cooldownSeconds = 0,
    this.severity = AlertSeverity.warning,
    this.isEnabled = true,
  });

  /// Rule identifier, unique within the rule set.
  final String id;

  /// Metric path, for example `cpu.usage_percent` or `gpu.0.temp_celsius`.
  final String metric;

  /// Comparison applied to the latest sample.
  final AlertOp op;

  /// Value the metric is compared against.
  final double threshold;

  /// How long the condition must hold before the alert is raised.
  final int forSeconds;

  /// Hysteresis: the metric must clear the threshold by this much to clear.
  final double clearMargin;

  /// Minimum time between two alerts for this rule.
  final int cooldownSeconds;

  /// How urgent the alert is.
  final AlertSeverity severity;

  /// Whether the daemon evaluates this rule.
  final bool isEnabled;
}

/// A rule that is currently firing (`ALERT_RAISED`, SRD 7.5).
final class ActiveAlert {
  /// Creates an active alert.
  const ActiveAlert({
    required this.alertId,
    required this.ruleId,
    required this.metric,
    required this.value,
    required this.threshold,
    required this.severity,
    required this.since,
  });

  /// Identifier of this alert instance.
  final String alertId;

  /// The rule that raised it.
  final String ruleId;

  /// Metric path that crossed the threshold.
  final String metric;

  /// Observed value at raise time.
  final double value;

  /// The rule's threshold.
  final double threshold;

  /// How urgent the alert is.
  final AlertSeverity severity;

  /// When the alert was raised.
  final DateTime since;
}
