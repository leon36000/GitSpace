#!/bin/bash
set -eu

# The normalized verifier is offline and uses only the files baked into the image.
# It writes the exact GitSpace JSON reward artifact; the legacy text reward file is forbidden.
[[ "$(pwd)" == "/app" ]]
[[ ! -e /logs/verifier/reward.json ]]
[[ ! -e /logs/verifier/gitspace-result.json ]]
exec /usr/local/bin/python3 /tests/run_test.py
