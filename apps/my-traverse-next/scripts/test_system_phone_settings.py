import base64
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

import system_phone_settings as settings


class LinkSettingsTest(unittest.TestCase):
  def setUp(self):
    self.tmp = tempfile.TemporaryDirectory()
    self.addCleanup(self.tmp.cleanup)
    self.directory = Path(self.tmp.name)
    self.runtime = self.directory / "runtime"
    self.key = ec.generate_private_key(ec.SECP256R1())
    pub = self.directory / "pair-phone.der"
    pub.write_bytes(self.key.public_key().public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo))
    pub.chmod(0o600)
    target = self.directory / settings.PROFILE
    target.write_text(json.dumps({"near": -80, "far": -93, "scope": "preserve"}))
    target.chmod(0o600)

  def command(self, near=-25, far=-45, revision=0):
    payload = f"wayon-link-thresholds-v1\n{revision}\n{near}\n{far}\n".encode()
    proof = base64.b64encode(self.key.sign(payload, ec.ECDSA(hashes.SHA256()))).decode()
    return {"near": near, "far": far, "revision": revision, "proof": proof}

  def test_reads_exact_sample_only_while_fresh_and_parked(self):
    with patch.object(settings.time, "monotonic_ns", return_value=1_000_000_000):
      settings.publish(0, -25, "received", self.runtime)
      view = settings.snapshot(self.directory, self.runtime, parked=True)
      self.assertEqual((view["linkRssi"], view["sampleId"], view["ageMs"], view["applied"]), (-25, 1000, 0, True))
      self.assertIsNone(settings.snapshot(self.directory, self.runtime, parked=False)["linkRssi"])
      settings.publish(0, None, "not_seen", self.runtime)
      view = settings.snapshot(self.directory, self.runtime, parked=True)
      self.assertIsNone(view["linkRssi"])
      self.assertEqual(view["status"], "not_seen")
      settings.publish(0, 0, "received", self.runtime)
    with patch.object(settings.time, "monotonic_ns", return_value=4_000_000_000):
      self.assertIsNone(settings.snapshot(self.directory, self.runtime, parked=True)["linkRssi"])

  def test_threshold_update_requires_signature_current_revision_and_park(self):
    cmd = self.command()
    for wrong, parked, code in (({**cmd, "far": -48}, lambda: True, 403),
                                (cmd, lambda: False, 409),
                                ({**cmd, "far": -26}, lambda: True, 400)):
      self.assertEqual(settings.update(wrong, parked, self.directory)[1], code)
      self.assertEqual(settings.profile(self.directory)[1], 0)
    self.assertEqual(settings.update(cmd, lambda: True, self.directory)[1], 200)
    self.assertEqual(settings.profile(self.directory), ({"near": -25, "far": -45, "scope": "preserve", "thresholdRevision": 1}, 1))
    self.assertEqual(settings.update(cmd, lambda: True, self.directory)[0]["error"], "threshold_conflict")

  def test_saved_and_effective_revision_are_distinct(self):
    settings.publish(0, -27, "received", self.runtime)
    self.assertEqual(settings.update(self.command(), lambda: True, self.directory)[1], 200)
    view = settings.snapshot(self.directory, self.runtime, parked=True)
    self.assertFalse(view["applied"])
    self.assertIsNone(view["linkRssi"])
    settings.publish(1, -30, "received", self.runtime)
    view = settings.snapshot(self.directory, self.runtime, parked=True)
    self.assertEqual((view["applied"], view["near"], view["far"], view["linkRssi"]), (True, -25, -45, -30))

  def test_signed_three_db_gap_is_accepted_and_two_db_gap_is_rejected(self):
    self.assertEqual(settings.update(self.command(near=-12, far=-14), lambda: True, self.directory)[1], 400)
    self.assertEqual(settings.profile(self.directory)[1], 0)
    self.assertEqual(settings.update(self.command(near=-11, far=-14), lambda: True, self.directory)[1], 200)
    self.assertEqual(settings.profile(self.directory),
                     ({"near": -11, "far": -14, "scope": "preserve", "thresholdRevision": 1}, 1))
