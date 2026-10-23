import 'package:deckhand/core/errors/failure.dart';
import 'package:deckhand/core/result.dart';
import 'package:deckhand/domain/entities/host.dart';
import 'package:deckhand/domain/entities/paired_device.dart';
import 'package:deckhand/domain/repositories/device_repository.dart';
import 'package:deckhand/domain/repositories/host_repository.dart';

/// Stores a completed pairing on the phone.
///
/// The pairing handshake itself (QR scan, HMAC proofs, `PAIR_OK`) lives in the
/// network layer. This use case persists the outcome: credentials in secure
/// storage, and the pinned fingerprint on the host record (SRD 4.4 step 6).
final class PairDevice {
  /// Creates the use case.
  const PairDevice({required this.hosts, required this.devices});

  /// Host persistence.
  final HostRepository hosts;

  /// Credential persistence.
  final DeviceRepository devices;

  /// Saves [device] for [host] and pins its fingerprint.
  Future<Result<Host>> call({
    required Host host,
    required PairedDevice device,
  }) async {
    try {
      await devices.save(device);
      final paired = host.copyWith(
        pinnedFingerprint: device.pinnedFingerprint,
      );
      await hosts.saveHost(paired);
      return Ok(paired);
    } on Exception catch (error) {
      return Err(
        StorageFailure('Could not store the pairing.', cause: error),
      );
    }
  }
}
