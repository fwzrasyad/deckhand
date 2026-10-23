import 'dart:async';

import 'package:deckhand/domain/entities/host.dart';

/// Finds Deckhand daemons on the local network (SRD 9.7).
///
/// mDNS is only a hint: a discovered host is shown with its advertised address,
/// and the connection still has to satisfy certificate pinning (SEC-019, T8).
/// Manual entry is always available because mDNS fails on many networks.
abstract interface class HostScanner {
  /// Hosts found while scanning. The stream closes after [timeout].
  Stream<Host> scan({Duration timeout});

  /// Stops an in-flight scan and releases the platform resources.
  Future<void> stop();
}
