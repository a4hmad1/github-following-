#!/usr/bin/env bash
# ============================================================
# 🛑 Stop Developer Auto-Pilot Background Service
# ============================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/autopilot.pid"

RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
BOLD='\033[1m'
RESET='\033[0m'

STOPPED=0

# Clean up any log stream viewers first
pkill -f "tail -f.*autopilot.log" 2>/dev/null || true

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Sending graceful stop signal to Auto-Pilot (PID: ${PID})...${RESET}"
        kill -INT "$PID" 2>/dev/null
        
        # Wait up to 3 seconds for graceful cleanup
        for i in {1..3}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done

        # Force kill if still lingering
        if ps -p "$PID" > /dev/null 2>&1; then
            kill -9 "$PID" 2>/dev/null || true
        fi

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
