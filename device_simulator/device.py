import json
import os
import random

from datetime import datetime, UTC
from enum import Enum

DEFAULT_EVENT_FILE = os.path.join(os.path.dirname(__file__), '..', 'reports', 'events.json')


class DeviceState(Enum):
    BOOTING = "booting"
    IDLE = "idle"
    UPDATING = "updating"
    VERIFYING = "verifying"
    UPDATED = "updated"
    ROLLING_BACK = "rolling_back"
    FAILED = "failed"

class Device:

    # Initialize device
    def __init__(self, device_sn: str, current_version="1.0.219", event_file=DEFAULT_EVENT_FILE):
        self.device_id = device_sn
        self.current_version = current_version
        self.previous_version = None          
        self.state = DeviceState.BOOTING      # just keeping it for completeness
        self.event_file = event_file
        if not os.path.exists(self.event_file):
            with open(self.event_file, 'w') as f:
                json.dump([], f)
        self._transition(DeviceState.IDLE)    # boot completes immediately on init

    def _transition(self, new_state: DeviceState):
        """Move device to a new state and append one event record to the events file."""
        self.state = new_state
        event = {
            "device_id": self.device_id,
            "state": new_state.value,
            "firmware_version": self.current_version,
            "timestamp": datetime.now(UTC).isoformat()
        }
        # Read-append-write: safer than read-modify-write on a shared file
        try:
            with open(self.event_file, 'r') as f:
                data = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            data = [] # start fresh if file is empty or missing
        data.append(event)
        with open(self.event_file, 'w') as f:
            json.dump(data, f, indent=4)

    def apply_update(self, update_version: str, fail_probability=0.0) -> bool:
        """
        Simulate applying a firmware update.

        Args:
            update_version: Target firmware version string.
            fail_probability: 0.0 = always succeed. 
        Returns:
            True if rollback was triggered, False if update succeeded.
        """
        self.previous_version = self.current_version  # save before we start — target_version
        self._transition(DeviceState.UPDATING)
        self._transition(DeviceState.VERIFYING)

        if random.random() < fail_probability:
            # using random to simulate failure based on fail_probability
            self._transition(DeviceState.FAILED)
            self._transition(DeviceState.ROLLING_BACK)
            self.current_version = self.previous_version  # restore to pre-update version
            self._transition(DeviceState.IDLE)
            return True  # rollback triggered
        else:
            # Update succeeded
            self.current_version = update_version
            self._transition(DeviceState.UPDATED)
            self._transition(DeviceState.IDLE)
            return False  # no rollback


if __name__ == "__main__":
    # for debugging
    device = Device("device_123")
    rolled_back = device.apply_update("1.0.220", fail_probability=0.0)
    print(f"Version: {device.current_version}, Rolled back: {rolled_back}, State: {device.state}")

    device2 = Device("device_456")
    rolled_back = device2.apply_update("1.0.220", fail_probability=0.9)
    print(f"Version: {device2.current_version}, Rolled back: {rolled_back}, State: {device2.state}")
