import base64
from pathlib import Path
from types import SimpleNamespace
import tempfile
import time
import unittest

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, padding, rsa

from comma_rssi_receiver import pair_wayon
from wayon_door_pair import DOMAIN, authorize, enroll


class PairTests(unittest.IsolatedAsyncioTestCase):
  @classmethod
  def setUpClass(cls):
    cls.phone = ec.generate_private_key(ec.SECP256R1())
    cls.receiver = rsa.generate_private_key(public_exponent=65537, key_size=2048)

  def setUp(self):
    temp = tempfile.TemporaryDirectory()
    self.addCleanup(temp.cleanup)
    self.path = Path(temp.name)
    files = {
      "pair-phone.der": self.phone.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo),
      "pair-receiver.pem": self.receiver.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()),
    }
    for name, value in files.items():
      (self.path / name).write_bytes(value)
      (self.path / name).chmod(0o600)

  def envelope(self, key=b"a" * 32, phone=None, at=None):
    at = int(time.time()) if at is None else at
    box = self.receiver.public_key().encrypt(key, padding.OAEP(
      mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None))
    proof = (phone or self.phone).sign(DOMAIN + str(at).encode() + b"\n" + box, ec.ECDSA(hashes.SHA256()))
    return {"at": at, "box": base64.b64encode(box).decode(), "proof": base64.b64encode(proof).decode()}

  async def test_approved_phone_retry_and_existing_key_not_overwritten(self):
    parked = SimpleNamespace(is_parked=lambda: True)
    target = self.path / "proximity.key"
    for key, status in [(b"a" * 32, 200), (b"a" * 32, 200), (b"b" * 32, 409)]:
      self.assertEqual((await pair_wayon(parked, self.envelope(key), self.path))[1], status)
    self.assertEqual(target.read_text().strip(), (b"a" * 32).hex())
    self.assertEqual(target.stat().st_mode & 0o777, 0o600)

  async def test_forged_expired_and_tampered_proofs(self):
    parked = SimpleNamespace(is_parked=lambda: True)
    changed = self.envelope()
    changed["box"] = ("A" if changed["box"][0] != "A" else "B") + changed["box"][1:]
    for invalid in (changed, self.envelope(phone=ec.generate_private_key(ec.SECP256R1())),
                    self.envelope(at=int(time.time()) - 91)):
      self.assertEqual((await pair_wayon(parked, invalid, self.path))[1], 403)
    self.assertFalse((self.path / "proximity.key").exists())

  async def test_checks_ignition_both_before_and_after_authentication(self):
    for answers in ((False,), (True, False)):
      checks = iter(answers)
      receiver = SimpleNamespace(is_parked=lambda: next(checks))
      self.assertEqual((await pair_wayon(receiver, self.envelope(), self.path))[1], 409)
      self.assertFalse((self.path / "proximity.key").exists())

  def test_rejects_untrusted_local_files(self):
    (self.path / "pair-phone.der").chmod(0o644)
    with self.assertRaises(ValueError):
      authorize(self.path, self.envelope())
    target = self.path / "proximity.key"
    target.symlink_to(self.path / "pair-phone.der")
    with self.assertRaises(OSError):
      enroll(self.path, b"a" * 32)
