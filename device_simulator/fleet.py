import os
import yaml

from device import Device

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'configs', 'fleet_config.yaml')
#EVENTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'reports', 'events.json')


def load(device_config=CONFIG_PATH, group=None):
    """Load device configuration from YAML and return Device instances for a group."""
    with open(device_config, 'r') as f:
        config = yaml.safe_load(f)
    device_groups = config.get('device_groups', {})
    entries = device_groups.get(group, [])
    return [Device(d['device_id'], d['fw_version']) for d in entries]


def rollout(group, version, fail_probability=0.0):
    """
    Simulate a firmware rollout to all devices in a group.
    Returns a list of result dicts.
    """
    devices = load(group=group)
    results = []
    for device in devices:
        rolled_back = device.apply_update(version, fail_probability)
        results.append({
            "device_id": device.device_id,
            "group": group,
            "target_version": version,
            "final_version": device.current_version,
            "rolled_back": rolled_back,
            "final_state": device.state.value,
        })
    return results


def health_summary(results: list) -> dict:
    """
    Summarize the results returned by rollout().

    Returns counts and pass rate. This is what feeds test_history.json
    and eventually to the Streamlit dashboard.
    """
    total = len(results)
    failed = sum(1 for r in results if r["rolled_back"])
    succeeded = total - failed
    return {
        "total": total,
        "succeeded": succeeded,
        "failed": failed,
        "pass_rate": round(succeeded / total, 3) if total > 0 else 0.0,
        "rollback_triggered": failed > 0,
    }


if __name__ == "__main__":
    results = rollout("staging", "1.0.220", fail_probability=0.5)
    summary = health_summary(results)
    print("Results:", results)
    print("Summary:", summary) 