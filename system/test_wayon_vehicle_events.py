from openpilot.system.wayon_vehicle_events import (
  door_lock_event,
  enqueue_vehicle_event,
  peek_vehicle_event,
  remove_vehicle_event,
)


def test_door_lock_event_shape():
  event = door_lock_event(True)

  assert event["id"]
  assert event["eventType"] == "door_lock"
  assert event["locked"] is True
  assert event["test"] is False
  assert event["occurredAt"].endswith("Z")


def test_vehicle_event_queue_round_trip(tmp_path):
  queue = tmp_path / "vehicle_events.jsonl"
  unlocked = {**door_lock_event(False), "id": "unlocked"}
  locked = {**door_lock_event(True), "id": "locked"}

  enqueue_vehicle_event(unlocked, queue)
  enqueue_vehicle_event(locked, queue)
  assert peek_vehicle_event(queue) == unlocked
  assert remove_vehicle_event("unlocked", queue)
  assert peek_vehicle_event(queue) == locked
  assert remove_vehicle_event("locked", queue)
  assert peek_vehicle_event(queue) is None
