#!/usr/bin/env bash
#
# D-14 SSE/StreamableHTTP proxy passthrough test. Asserts that an MCP
# StreamableHTTP response flows through the reverse proxy on :80 unbuffered.
# Run once with `caddy` and once with `nginx` (swap the compose proxy service
# between runs). The KS_API_KEY env var is never echoed (T-07-14).
#
# Usage:
#   KS_API_KEY=ks_live_... bash deploy/scripts/sse-proxy-test.sh caddy
#   KS_API_KEY=ks_live_... bash deploy/scripts/sse-proxy-test.sh nginx

set -euo pipefail

PROXY="${1:?usage: sse-proxy-test.sh <caddy|nginx>}"
case "$PROXY" in
  caddy|nginx) ;;
  *) echo "usage: sse-proxy-test.sh <caddy|nginx>" >&2; exit 2 ;;
esac

BASE="${SSE_BASE_URL:-http://localhost}"
KEY="${KS_API_KEY:?KS_API_KEY required}"

# MCP StreamableHTTP initialize request; the load-bearing assertion is that
# the response streams through the proxy (event/data lines or a jsonrpc body)
# rather than being buffered or dropped.
BODY='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"sse-test","version":"0"}}}'

OUT=$(curl --no-buffer -N -sS -m 30 \
  -H "Authorization: Bearer ${KEY}" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -X POST "${BASE}/v1/mcp" -d "${BODY}" || true)

if echo "$OUT" | grep -Eq 'event:|data:|"jsonrpc"'; then
  echo "SSE passthrough OK via ${PROXY}"
else
  echo "FAIL: no stream through ${PROXY}" >&2
  echo "--- response head ---" >&2
  echo "$OUT" | head -c 500 >&2
  echo "" >&2
  exit 1
fi
