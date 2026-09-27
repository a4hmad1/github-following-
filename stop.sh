#!/usr/bin/env bash
# ============================================================
# 🛑 Stop Kurdish Developer Auto-Pilot
# ============================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/autopilot.pid"

RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
RESET='\033[0m'

STOPPED=0

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        kill "$PID" 2>/dev/null
        sleep 1
        kill -9 "$PID" 2>/dev/null || true
        echo -e "${GREEN}✓ Successfully stopped Auto-Pilot (PID: ${PID})${RESET}"
        STOPPED=1
    fi
    rm -f "$PID_FILE"
fi

# Fallback check for any stray autofollow.py instances
STRAY=$(pgrep -f "autofollow.py" || true)
if [ -n "$STRAY" ]; then
    kill -9 $STRAY 2>/dev/null || true
    echo -e "${GREEN}✓ Cleaned up running autofollow processes.${RESET}"
    STOPPED=1
fi

if [ "$STOPPED" -eq 0 ]; then
    echo -e "${YELLOW}[!] Auto-Pilot was not currently running.${RESET}"
fi
