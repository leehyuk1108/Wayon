"""
Copyright (c) 2021-, Haibin Wen, sunnypilot, and a number of other contributors.

This file is part of sunnypilot and is licensed under the MIT License.
See the LICENSE.md file in the root directory for more details.
"""

import json
import os
import socket
import time

from opendbc.car import DT_CTRL, structs
from opendbc.car.can_definitions import CanData
from opendbc.car.gm import gmcan
from opendbc.car.gm.values import CanBus, CruiseButtons
from opendbc.sunnypilot.car.intelligent_cruise_button_management_interface_base import IntelligentCruiseButtonManagementInterfaceBase

SendButtonState = structs.IntelligentCruiseButtonManagement.SendButtonState

# Traverse route captures show short physical presses as four 0x1E1 frames at
# about 33 Hz. The following stock UNPRESS frame naturally releases the button.
BUTTON_PRESS_FRAMES = 4
BUTTON_COOLDOWN_FRAMES = max(1, round(0.2 / DT_CTRL))
BUTTON_TEST_COMMAND_MAX_AGE = 1.0
BUTTON_TEST_SOCKET = "/tmp/gm_button_test.sock"
BUTTON_TEST_ACK_SOCKET = "/tmp/gm_button_test_web.sock"

BUTTONS = {
  SendButtonState.increase: CruiseButtons.RES_ACCEL,
  SendButtonState.decrease: CruiseButtons.DECEL_SET,
}

TEST_BUTTONS = {
  "res": CruiseButtons.RES_ACCEL,
  "set": CruiseButtons.DECEL_SET,
  "cancel": CruiseButtons.CANCEL,
  "unpress": CruiseButtons.UNPRESS,
}


class IntelligentCruiseButtonManagementInterface(IntelligentCruiseButtonManagementInterfaceBase):
  def __init__(self, CP, CP_SP):
    super().__init__(CP, CP_SP)
    self.last_stock_counter = None
    self.active_button = CruiseButtons.INIT
    self.press_frames_remaining = 0
    self.cooldown_until = 0
    self.test_button = CruiseButtons.INIT
    self.test_press_frames_remaining = 0
    self.test_command_id = ""
    self.test_socket = None
    test_socket = None
    try:
      test_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
      test_socket.setblocking(False)
      try:
        os.unlink(BUTTON_TEST_SOCKET)
      except FileNotFoundError:
        pass
      test_socket.bind(BUTTON_TEST_SOCKET)
      os.chmod(BUTTON_TEST_SOCKET, 0o600)
      self.test_socket = test_socket
    except OSError:
      if test_socket is not None:
        test_socket.close()

  def close_test_socket(self) -> None:
    if self.test_socket is None:
      return

    self.test_socket.close()
    self.test_socket = None
    try:
      os.unlink(BUTTON_TEST_SOCKET)
    except FileNotFoundError:
      pass

  def reset_button_sequence(self) -> None:
    self.active_button = CruiseButtons.INIT
    self.press_frames_remaining = 0

  def send_test_ack(self, command_id: str, state: str, reason: str = "", **details) -> None:
    if self.test_socket is None or not command_id:
      return

    payload = json.dumps({
      "schema": "gm-button-test-ack-v1",
      "id": command_id,
      "state": state,
      "reason": reason,
      "atMono": time.monotonic(),
      **details,
    }, separators=(",", ":")).encode()
    try:
      self.test_socket.sendto(payload, BUTTON_TEST_ACK_SOCKET)
    except OSError:
      pass

  def reset_test_sequence(self, reason: str = "") -> None:
    if reason:
      self.send_test_ack(self.test_command_id, "rejected", reason)
    self.test_button = CruiseButtons.INIT
    self.test_press_frames_remaining = 0
    self.test_command_id = ""

  def queue_test_button(self, button_name: str, command_id: str = "") -> bool:
    button = TEST_BUTTONS.get(button_name, CruiseButtons.INIT)
    if button == CruiseButtons.INIT:
      return False

    if self.test_command_id:
      self.send_test_ack(self.test_command_id, "rejected", "superseded")
    self.reset_button_sequence()
    self.cooldown_until = 0
    self.test_button = button
    self.test_press_frames_remaining = 1 if button == CruiseButtons.UNPRESS else BUTTON_PRESS_FRAMES
    self.test_command_id = command_id
    return True

  def consume_test_commands(self) -> None:
    if self.test_socket is None:
      return

    for _ in range(8):
      try:
        raw_command = self.test_socket.recv(512)
      except BlockingIOError:
        break

      try:
        command = json.loads(raw_command)
        command_id = str(command["id"])
        button_name = str(command["button"]).lower()
        issued_at = float(command["issuedAtMono"])
        if not command_id or len(command_id) > 64:
          continue

        age = time.monotonic() - issued_at
        if not -0.2 <= age <= BUTTON_TEST_COMMAND_MAX_AGE:
          self.send_test_ack(command_id, "rejected", "stale_command")
        elif button_name == "ping":
          self.send_test_ack(command_id, "pong")
        elif not self.queue_test_button(button_name, command_id):
          self.send_test_ack(command_id, "rejected", "unsupported_button")
      except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        continue

  def update(self, CS, CC_SP, packer, frame) -> list[CanData]:
    self.CC_SP = CC_SP
    self.ICBM = CC_SP.intelligentCruiseButtonManagement
    self.frame = frame

    stock_counter = int(CS.buttons_counter) % 4
    stock_frame_updated = self.last_stock_counter is None or stock_counter != self.last_stock_counter
    if not stock_frame_updated:
      return []
    self.last_stock_counter = stock_counter
    self.consume_test_commands()

    physical_button_pressed = int(CS.cruise_buttons) != CruiseButtons.UNPRESS
    cruise_enabled = bool(CS.out.cruiseState.enabled)

    if physical_button_pressed or not cruise_enabled:
      self.reset_button_sequence()
      self.reset_test_sequence("physical_button_pressed" if physical_button_pressed else "cruise_not_enabled")
      return []

    if self.test_press_frames_remaining > 0:
      can_sends = [gmcan.create_buttons(packer, CanBus.CAMERA, stock_counter, self.test_button)]
      self.send_test_ack(self.test_command_id, "transmitted", buttonCode=int(self.test_button),
                         bus=CanBus.CAMERA, counter=stock_counter)
      self.test_command_id = ""
      self.test_press_frames_remaining -= 1
      if self.test_press_frames_remaining == 0:
        self.test_button = CruiseButtons.INIT
      return can_sends

    send_button = BUTTONS.get(self.ICBM.sendButton, CruiseButtons.INIT)
    if send_button == CruiseButtons.INIT:
      self.reset_button_sequence()
      return []

    if self.active_button not in (CruiseButtons.INIT, send_button):
      self.reset_button_sequence()
      self.cooldown_until = frame + BUTTON_COOLDOWN_FRAMES
      return []

    if self.press_frames_remaining == 0:
      if frame < self.cooldown_until:
        return []
      self.active_button = send_button
      self.press_frames_remaining = BUTTON_PRESS_FRAMES

    can_sends = [gmcan.create_buttons(packer, CanBus.CAMERA, stock_counter, self.active_button)]
    self.press_frames_remaining -= 1

    if self.press_frames_remaining == 0:
      self.active_button = CruiseButtons.INIT
      self.cooldown_until = frame + BUTTON_COOLDOWN_FRAMES

    return can_sends
