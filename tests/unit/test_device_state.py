from device_simulator.device import Device, DeviceState

# Using pytest's tmp_path so it creates test files under sys temp dir
def test_device_starts_idle(tmp_path):
    """Device should BOOT and transition to IDLE state on init."""
    device = Device("test_001", event_file=str(tmp_path / "events.json"))
    assert device.state == DeviceState.IDLE


def test_normal_update_succeeds(tmp_path):
    """fail_probability=0.0 should always update successfully."""
    device = Device("test_002", current_version="1.0.219", event_file=str(tmp_path / "events.json"))
    rolled_back = device.apply_update("1.0.220", fail_probability=0.0)
    assert rolled_back is False
    assert device.current_version == "1.0.220"
    assert device.previous_version == "1.0.219"
    assert device.state == DeviceState.IDLE


def test_forced_failure_triggers_rollback(tmp_path):
    """fail_probability=1.0 should always rollback."""
    device = Device("test_003", current_version="1.0.219", event_file=str(tmp_path / "events.json"))
    rolled_back = device.apply_update("1.0.220", fail_probability=1.0)
    assert rolled_back is True
    assert device.current_version == "1.0.219"
    assert device.state == DeviceState.IDLE


def test_rollback_restores_previous_version(tmp_path):
    """After two updates, rollback should restore the most recent successful version."""
    device = Device("test_004", current_version="1.0.219", event_file=str(tmp_path / "events.json"))
    device.apply_update("1.0.220", fail_probability=0.0)
    device.apply_update("1.0.221", fail_probability=1.0)
    assert device.current_version == "1.0.220"
