"""Pytest configuration ensuring sys.path contains repository root and backend."""

import sys
from pathlib import Path

# Guarantee that both repository root and backend directory are first in sys.path
TESTS_DIR = Path(__file__).resolve().parent
BACKEND_DIR = TESTS_DIR.parent
REPO_ROOT = BACKEND_DIR.parent

for path in (str(REPO_ROOT), str(BACKEND_DIR)):
    if path in sys.path:
        sys.path.remove(path)
    sys.path.insert(0, path)
