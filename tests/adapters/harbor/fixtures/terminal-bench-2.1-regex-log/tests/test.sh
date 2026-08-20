#!/bin/bash
set -euo pipefail

# The normalized verifier is offline and uses only the files baked into the image.
# It writes the exact GitSpace JSON reward artifact; the legacy text reward file is forbidden.
python3 /tests/run_test.py
