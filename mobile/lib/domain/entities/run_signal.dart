/// The signals the phone may send to a running process (SRD 7.5).
///
/// The daemon maps these to `SIGINT`/`CTRL_BREAK`, `SIGTERM`, and a force kill
/// per platform (SRD 9.2).
enum RunSignal {
  /// Ask the process to stop gracefully; the user's Ctrl+C.
  interrupt,

  /// Request termination.
  terminate,

  /// Force the process to die.
  kill,
}
