#!/usr/bin/env bash
# Regenerate hashed requirement locks. See docs/REPRODUCIBILITY.md.
set -euo pipefail
cd "$(dirname "$0")/.."

uv pip compile pyproject.toml \
  --extra dev --extra api \
  --generate-hashes \
  --universal \
  --python-version 3.10 \
  --no-emit-package rageval \
  --custom-compile-command "bash scripts/compile_locks.sh" \
  -o requirements-lock-fast.txt

uv pip compile pyproject.toml \
  --extra all \
  --generate-hashes \
  --python-platform x86_64-manylinux_2_28 \
  --python-version 3.12 \
  --torch-backend cpu \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  --index-strategy first-index \
  --emit-index-url \
  --no-emit-package rageval \
  --custom-compile-command "bash scripts/compile_locks.sh" \
  -o requirements-lock-all.txt
