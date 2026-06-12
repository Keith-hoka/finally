#!/usr/bin/env bash
# Stop FinAlly. The finally-data volume is kept, so the portfolio persists.
set -euo pipefail

docker rm -f finally > /dev/null 2>&1 || true
echo "FinAlly stopped. Data persists in the 'finally-data' volume."
