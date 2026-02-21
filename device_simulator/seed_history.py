import json
import os
import random

from datetime import datetime, timedelta, UTC

import fleet

HISTORY_FILE = os.path.join(os.path.dirname(__file__), '..', 'reports', 'test_history.json')
random.seed(26)  # fixed seed

# Days where something goes wrong — (fail_probability, scenario_label - used in dashboard)
# All other days are normal with 5% noise
BAD_DAYS = {
     8: (0.80, "high_error_rate"),
    14: (0.95, "critical_regression"),
    22: (0.70, "intermittent_failures"),
    27: (0.60, "integration_failures"),
}


def bump_version(version: str) -> str:
    """Increment the patch number: 1.0.219 → 1.0.220"""
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def seed_history(days=30):
    """
    Simulate n days of staged firmware rollouts. Default is 30 days.

    Flow goes like this for each day:
      1. Bump the candidate version (assuming we get a new build every day).
      2. Try staging  → if fails, rollback. Customers unaffected.
      3. Try canary → if fails, rollback. Customers unaffected.
      4. Try production → if fails, rollback. Customers briefly saw bad fw.
      5. Record what happened as one row in test_history.json

    production_version = what customers are actually running right now.
    It only changes if a full staging → canary → production rollout succeeds.
    """
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

    # Clear events.json before seeding so stale data from previous runs
    # doesn't corrupt the file or make the Streamlit dashboard confusing.
    events_file = os.path.join(os.path.dirname(__file__), '..', 'reports', 'events.json')
    with open(events_file, 'w') as f:
        json.dump([], f)

    history = []
    # start_date and time
    base_date = datetime.now(UTC) - timedelta(days=days)

    production_version = "1.0.219"  # base fw version,  what's on customers devices
    candidate_version = production_version  # tracks independently, always bumps each day

    for day in range(1, days+1):
        date_str = (base_date + timedelta(days=day)).strftime("%Y-%m-%d")
        candidate_version = bump_version(candidate_version)  # new build every day regardless
        fail_prob, scenario = BAD_DAYS.get(day, (0.05, "normal_release"))

        # Stage 1: Staging
        staging_results = fleet.rollout("staging", candidate_version, fail_prob*0.1)
        staging_summary = fleet.health_summary(staging_results)

        if staging_summary["rollback_triggered"]:
            # Staging failed — rollback, customers never get candidate_version
            row = _make_row(day, date_str, scenario, "staging", candidate_version,
                            production_version, staging_summary, blocked_at="staging")
            _print_row(row)
            history.append(row)
            continue  # production_version stays the same

        # Stage 2: Canary
        canary_results  = fleet.rollout("canary", candidate_version, fail_prob)
        canary_summary  = fleet.health_summary(canary_results)

        if canary_summary["rollback_triggered"]:
            # Canary failed — rollback, customers never get candidate_version
            row = _make_row(day, date_str, scenario, "canary", candidate_version,
                            production_version, canary_summary, blocked_at="canary")
            _print_row(row)
            history.append(row)
            continue  # production_version stays the same


        # Stage 3: Production
        prod_results    = fleet.rollout("production", candidate_version, fail_prob*0.2)
        prod_summary    = fleet.health_summary(prod_results)

        if prod_summary["rollback_triggered"]:
            # Production failed — customers briefly got bad fw, rolled back
            row = _make_row(day, date_str, scenario, "production", candidate_version,
                            production_version, prod_summary, blocked_at="production")
        else:
            # Full OTA FWrollout succeeded!! Bump production_version
            production_version = candidate_version
            row = _make_row(day, date_str, scenario, "production", candidate_version,
                            production_version, prod_summary, blocked_at="N/A")

        _print_row(row)
        history.append(row)

    with open(HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=4)
    print(f"\nWrote {len(history)} rows to the {HISTORY_FILE}")
    print(f"Final production version: {production_version}")


def _make_row(day, date, scenario, stage, candidate, production, summary, blocked_at):
    return {
        "day": day,
        "date": date,
        "scenario": scenario,
        "stage_reached": stage,
        "target_version": candidate,
        "production_version": production,
        "blocked_at": blocked_at,          # N/A = success (all stages completed)
        **summary,
    }


def _print_row(row):
    blocked = f"BLOCKED at {row['blocked_at']}" if row["blocked_at"] else "PROMOTED"
    print(f"Day {row['day']:02d} | {row['date']} | {row['scenario']:<25} | "
          f"pass_rate={row['pass_rate']:.2f} | {blocked:<25} | prod={row['production_version']}")


if __name__ == "__main__":
    seed_history()
