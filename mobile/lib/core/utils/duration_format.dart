/// Formats durations the way the runs list and terminal header show them.
///
/// Examples: `0.4s`, `12s`, `3m 05s`, `1h 02m`.
String formatDuration(Duration duration) {
  if (duration.inSeconds < 1) {
    final tenths = (duration.inMilliseconds / 100).round();
    return '${(tenths / 10).toStringAsFixed(1)}s';
  }

  final totalSeconds = duration.inSeconds;
  if (totalSeconds < 60) {
    return '${totalSeconds}s';
  }

  final minutes = totalSeconds ~/ 60;
  final seconds = totalSeconds % 60;
  if (minutes < 60) {
    return '${minutes}m ${_pad(seconds)}s';
  }

  final hours = minutes ~/ 60;
  return '${hours}h ${_pad(minutes % 60)}m';
}

String _pad(int value) => value.toString().padLeft(2, '0');
