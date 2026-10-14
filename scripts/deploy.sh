#!/usr/bin/env bash
# Deploy script for Booking API with mutex lock, digest verification, and auto-rollback.
set -euo pipefail

MANIFEST_FILE="${1:-}"
if [[ -z "$MANIFEST_FILE" ]]; then
    echo "Usage: $0 <path-to-release-manifest.json>" >&2
    exit 1
fi

if [[ ! -f "$MANIFEST_FILE" ]]; then
    echo "Error: Manifest file not found: $MANIFEST_FILE" >&2
    exit 1
fi

# Dispatch to Python deployment orchestrator
PYTHON_CMD="python3"
if ! command -v "$PYTHON_CMD" &>/dev/null; then
    PYTHON_CMD="python"
fi

exec "$PYTHON_CMD" -m scripts.deploy --manifest "$MANIFEST_FILE" "$@"
