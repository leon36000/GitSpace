#!/usr/bin/env python3
from pathlib import Path

from test_outputs import test_regex_matches_dates

reward_path = Path("/logs/verifier/reward.json")
reward_path.parent.mkdir(parents=True, exist_ok=True)

try:
    test_regex_matches_dates()
except AssertionError:
    reward_path.write_text('{"reward":0}\n', encoding="utf-8")
else:
    reward_path.write_text('{"reward":1}\n', encoding="utf-8")
