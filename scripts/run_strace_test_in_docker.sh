#!/usr/bin/env bash
set -euo pipefail

docker build -f deploy/Dockerfile.test-linux -t keenyspace-strace-test .
docker run --rm --cap-add=SYS_PTRACE keenyspace-strace-test \
    uv run pytest packages/server/tests/integration/test_atomic_write_strace.py -x -v
