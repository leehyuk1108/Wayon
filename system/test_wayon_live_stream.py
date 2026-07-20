import json
from types import SimpleNamespace

from openpilot.system.wayon_live_stream import (
  FRAME_FLAG_KEY,
  FRAME_HEADER,
  FRAME_MAGIC,
  FRAME_TYPE_METADATA,
  bounded_number,
  encoded_payload,
  is_offroad,
  json_frame,
  pack_frame,
)


def unpack_frame(frame):
  header = FRAME_HEADER.unpack(frame[:FRAME_HEADER.size])
  magic, frame_type, flags, _, sequence, timestamp_us, payload_size = header
  return magic, frame_type, flags, sequence, timestamp_us, frame[FRAME_HEADER.size:FRAME_HEADER.size + payload_size]


def test_pack_frame_preserves_header_and_payload():
  frame = pack_frame(2, b"video", sequence=42, timestamp_us=123_456, key_frame=True)
  magic, frame_type, flags, sequence, timestamp_us, payload = unpack_frame(frame)

  assert magic == FRAME_MAGIC
  assert frame_type == 2
  assert flags & FRAME_FLAG_KEY
  assert sequence == 42
  assert timestamp_us == 123_456
  assert payload == b"video"


def test_json_frame_uses_compact_utf8_payload():
  frame = json_frame(FRAME_TYPE_METADATA, {"state": "live", "fps": 20})
  *_, payload = unpack_frame(frame)
  assert json.loads(payload) == {"state": "live", "fps": 20}


def test_encoded_payload_prepends_codec_header_on_key_frame():
  payload, key_frame = encoded_payload(SimpleNamespace(header=b"sps-pps", data=b"frame"))
  assert payload == b"sps-ppsframe"
  assert key_frame is True

  payload, key_frame = encoded_payload(SimpleNamespace(header=b"", data=b"delta"))
  assert payload == b"delta"
  assert key_frame is False


def test_bounded_number_clamps_and_falls_back():
  assert bounded_number("800", 10, 100, 1000) == 800
  assert bounded_number(10, 50, 20, 100) == 20
  assert bounded_number("bad", 50, 20, 100) == 50


def test_is_offroad_requires_matching_manager_params():
  class FakeParams:
    def __init__(self, values):
      self.values = values

    def get_bool(self, key):
      return self.values.get(key, False)

  assert is_offroad(FakeParams({"IsOffroad": True, "IsOnroad": False}))
  assert not is_offroad(FakeParams({"IsOffroad": False, "IsOnroad": False}))
  assert not is_offroad(FakeParams({"IsOffroad": True, "IsOnroad": True}))
