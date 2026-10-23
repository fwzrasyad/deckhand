import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Where the pairing flow currently is (SRD 10.3).
enum PairingStage {
  /// Nothing started yet.
  idle,

  /// The camera is scanning for a pairing QR code.
  scanningQr,

  /// The user is typing the code printed by the daemon.
  enteringCode,

  /// Both sides are exchanging HMAC proofs.
  verifyingProofs,

  /// `PAIR_OK` received and credentials stored.
  paired,

  /// Pairing failed; the screen shows the reason and offers a retry.
  failed,
}

/// Drives the pairing screen's state machine.
///
/// The handshake itself lives in the network layer in Phase 1; this controller
/// only tracks which step the UI is showing.
final class PairingController extends Notifier<PairingStage> {
  @override
  PairingStage build() => PairingStage.idle;

  /// The stage the flow is showing.
  PairingStage get stage => state;

  /// Moves to the given stage.
  set stage(PairingStage value) => state = value;

  /// Returns to the start after a failure or a cancel.
  void reset() => state = PairingStage.idle;
}

/// Pairing state for the pairing screen.
final pairingControllerProvider =
    NotifierProvider<PairingController, PairingStage>(PairingController.new);
