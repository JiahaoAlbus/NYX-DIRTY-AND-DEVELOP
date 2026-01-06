#!/usr/bin/env bash
set -euo pipefail

bash conformance/frozen-verify.sh
bash tooling/scripts/conformance.sh