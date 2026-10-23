import 'package:deckhand/data/protocol/proofs.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('normalizePairingSecret', () {
    test('uppercases and strips spaces and hyphens', () {
      expect(normalizePairingSecret(' ab-cd 12 '), 'ABCD12');
    });

    test('maps lookalike characters to digits', () {
      expect(normalizePairingSecret('ILO'), '110');
    });
  });

  group('computePairingProof', () {
    test('matches the reference HMAC vector', () {
      final proof = computePairingProof(
        secret: 'ABC123',
        role: clientRole,
        fingerprint: 'aa11bb22',
        clientNonce: 'nonce-c',
        serverNonce: 'nonce-s',
        deviceId: 'dev-1',
      );
      expect(proof, 'X5y7Os8HuvPluLgQqZE0YmNp3lLb9KSTtm-YKegw2NE');
    });

    test('is base64url without padding', () {
      final proof = computePairingProof(
        secret: 'ABC123',
        role: serverRole,
        fingerprint: 'aa11bb22',
        clientNonce: 'nonce-c',
        serverNonce: 'nonce-s',
        deviceId: 'dev-1',
      );
      expect(proof, isNot(contains('=')));
      expect(proof, isNot(contains('+')));
      expect(proof, isNot(contains('/')));
    });

    test('client and server proofs differ for the same nonces', () {
      String proofFor(String role) => computePairingProof(
        secret: 'ABC123',
        role: role,
        fingerprint: 'aa11bb22',
        clientNonce: 'nonce-c',
        serverNonce: 'nonce-s',
        deviceId: 'dev-1',
      );
      expect(proofFor(clientRole), isNot(proofFor(serverRole)));
    });
  });
}
