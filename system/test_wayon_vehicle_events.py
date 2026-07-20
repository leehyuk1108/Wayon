from openpilot.system.wayon_vehicle_events import (
  DoorLockNotificationDebouncer,
  ParkingUnlockReminder,
  door_lock_event,
  enqueue_vehicle_event,
  parking_unlocked_event,
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


def test_parking_unlocked_event_shape():
  event = parking_unlocked_event(179.6)

  assert event["id"]
  assert event["eventType"] == "parking_unlocked"
  assert event["delaySeconds"] == 180
  assert event["test"] is False
  assert event["occurredAt"].endswith("Z")


def test_door_lock_notification_debouncer_suppresses_quick_unlock_lock_pair():
  debouncer = DoorLockNotificationDebouncer(pair_window_s=8)
  unlocked = {**door_lock_event(False), "id": "unlocked"}
  locked = {**door_lock_event(True), "id": "locked"}

  assert debouncer.on_change(unlocked, 10) == []
  assert debouncer.has_pending_unlock
  assert debouncer.on_change(locked, 15) == []
  assert not debouncer.has_pending_unlock
  assert debouncer.flush(30) == []


def test_door_lock_notification_debouncer_releases_sustained_unlock():
  debouncer = DoorLockNotificationDebouncer(pair_window_s=8)
  unlocked = {**door_lock_event(False), "id": "unlocked"}

  assert debouncer.on_change(unlocked, 10) == []
  assert debouncer.flush(17.9) == []
  assert debouncer.flush(18) == [unlocked]
  assert not debouncer.has_pending_unlock


def test_door_lock_notification_debouncer_keeps_separated_changes():
  debouncer = DoorLockNotificationDebouncer(pair_window_s=8)
  unlocked = {**door_lock_event(False), "id": "unlocked"}
  locked = {**door_lock_event(True), "id": "locked"}

  assert debouncer.on_change(unlocked, 10) == []
  assert debouncer.on_change(locked, 18.1) == [unlocked, locked]


def test_door_lock_notification_debouncer_keeps_standalone_lock():
  debouncer = DoorLockNotificationDebouncer(pair_window_s=8)
  locked = {**door_lock_event(True), "id": "locked"}

  assert debouncer.on_change(locked, 10) == [locked]


def test_door_lock_notification_debouncer_suppresses_back_to_back_wake_pairs():
  debouncer = DoorLockNotificationDebouncer(pair_window_s=8)

  assert debouncer.on_change({**door_lock_event(False), "id": "unlock-1"}, 10) == []
  assert debouncer.on_change({**door_lock_event(True), "id": "lock-1"}, 14.2) == []
  assert debouncer.on_change({**door_lock_event(False), "id": "unlock-2"}, 14.3) == []
  assert debouncer.on_change({**door_lock_event(True), "id": "lock-2"}, 15.1) == []
  assert debouncer.flush(30) == []


def test_parking_unlock_reminder_waits_for_known_unlocked_state():
  reminder = ParkingUnlockReminder(delay_s=180)

  assert not reminder.update(None, 0)
  assert not reminder.update(None, 300)
  assert not reminder.update(False, 300)
  assert not reminder.update(False, 479.9)
  assert reminder.update(False, 480)
  assert not reminder.update(False, 900)


def test_parking_unlock_reminder_is_cancelled_by_lock():
  reminder = ParkingUnlockReminder(delay_s=180)

  assert not reminder.update(False, 10)
  assert not reminder.update(True, 100)
  assert not reminder.update(False, 400)


def test_parking_unlock_reminder_can_be_disabled():
  reminder = ParkingUnlockReminder(delay_s=0, enabled=False)

  assert not reminder.update(False, 0)


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
