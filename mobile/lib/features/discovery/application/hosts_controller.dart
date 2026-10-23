import 'package:deckhand/domain/entities/host.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Holds the hosts the screen can offer: saved hosts plus mDNS discoveries.
///
/// Phase 1 fills this from `HostRepository` and `HostScanner`. The controller
/// is the single place the screen reads hosts from (SRD 10.1).
final class HostsController extends Notifier<List<Host>> {
  @override
  List<Host> build() => const [];

  /// The hosts currently offered by the screen.
  List<Host> get hosts => state;

  /// Replaces the list after saved hosts load or a scan finishes.
  set hosts(List<Host> value) => state = value;

  /// Adds or updates one host, keeping the list stable for the UI.
  void upsert(Host host) => state = [
    ...state.where((existing) => existing.id != host.id),
    host,
  ];
}

/// Host list state for the hosts screen.
final hostsControllerProvider = NotifierProvider<HostsController, List<Host>>(
  HostsController.new,
);
