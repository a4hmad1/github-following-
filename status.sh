#!/usr/bin/env bash
# ============================================================
# 📊 Check Kurdish Developer Auto-Pilot Status
# ============================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/autopilot.pid"
LOG_FILE="$DIR/autopilot.log"

GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
CYAN='\033[96m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

RUNNING=0
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        RUNNING=1
    fi
fi

if [ "$RUNNING" -eq 1 ]; then
    echo -e "\n${GREEN}● ☀️ Kurdish Auto-Pilot is ACTIVE and RUNNING 24/7 (PID: ${PID})${RESET}"
    echo -e "${DIM}Streaming live output below (Press Ctrl+C to detach):${RESET}\n"
    trap 'echo -e "\n${GREEN}✓ Detached. Bot is still working in background.${RESET}"; exit 0' INT
    tail -n 25 -f "$LOG_FILE"
else
    echo -e "\n${RED}○ Kurdish Auto-Pilot is STOPPED.${RESET}"
    echo -e "To start: ${BOLD}./start.sh${RESET}\n"
    if [ -f "$LOG_FILE" ]; then
        echo -e "${DIM}Last 10 lines of previous log:${RESET}"
        tail -n 10 "$LOG_FILE"
    fi
fi
