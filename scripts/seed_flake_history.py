import json
import os
import random

# Simulate a history of test runs with some flaky tests for testing the flake detector.
random.seed(42)

OUTPUT = os.path.join(os.path.dirname(__file__), '..', 'reports', 'test_run_history.json')

TESTS = {
    "test_device_starts_idle":             "stable",
    "test_normal_update_succeeds":         "stable",
    "test_rollback_restores_version":      "stable",
    "test_ota_delivery_timing":            "flaky",  
}

runs = []
for run_number in range(1, 21):   # simulate 20 CI runs
    for test_id, behaviour in TESTS.items():
        if behaviour == "stable":
            passed = True
        else:
            # Flaky: passes most of the time but randomly fails ~40% of runs
            passed = random.random() > 0.4
        runs.append({"test_id": test_id, "run": run_number, "passed": passed})

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, 'w') as f:
    json.dump(runs, f, indent=4)

print(f"Written {len(runs)} test run entries to {OUTPUT}")
