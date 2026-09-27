#!/usr/bin/env bash
# ============================================================
# ☀️ Kurdish Developer Auto-Pilot 24/7 Launcher
# One command to run and work all the time!
# ============================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

PID_FILE="$DIR/autopilot.pid"
LOG_FILE="$DIR/autopilot.log"

RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# Check if already running
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚡ Auto-Pilot is ALREADY RUNNING in the background (PID: ${PID})${RESET}"
        echo -e "${DIM}Streaming live output below (Press Ctrl+C to detach — bot will keep running!):${RESET}\n"
        trap 'echo -e "\n${GREEN}✓ Detached. Auto-Pilot is still running in background.${RESET}"; exit 0' INT
        tail -n 25 -f "$LOG_FILE"
        exit 0
    else
        rm -f "$PID_FILE"
    fi
fi

# Ensure .env exists
if [ ! -f "$DIR/.env" ]; then
    echo -e "${RED}[!] Error: .env file not found in $DIR${RESET}"
    echo "Please configure GITHUB_TOKEN in .env"
    exit 1
fi

# Optional gender argument (all, female, male)
GENDER_ARG="all"
if [ -n "$1" ]; then
    GENDER_ARG="$1"
fi

# Launch background process
nohup python3 "$DIR/autofollow.py" --auto --gender "$GENDER_ARG" > "$LOG_FILE" 2>&1 &
PID=$!
disown $PID 2>/dev/null || true
echo "$PID" > "$PID_FILE"

# Setup automatic resume on reboot if not already present
CRON_JOB="@reboot cd $DIR && /bin/bash start.sh > /dev/null 2>&1"
(crontab -l 2>/dev/null | grep -F "start.sh") >/dev/null 2>&1 || (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab - >/dev/null 2>&1

echo -e "\n${YELLOW}╭──────────────────────────────────────────────────────────────╮${RESET}"
echo -e "${YELLOW}│${BOLD}     ☀️ KURDISH DEVELOPER AUTO-PILOT IS NOW WORKING 24/7!      ${RESET}${YELLOW}│${RESET}"
echo -e "${YELLOW}├──────────────────────────────────────────────────────────────┤${RESET}"
echo -e "${YELLOW}│${RESET}  🚀 ${BOLD}Status:${RESET}       RUNNING in background (PID: ${PID})          ${YELLOW}│${RESET}"
echo -e "${YELLOW}│${RESET}  👥 ${BOLD}Batch Size:${RESET}   250 Kurdish developers per cycle             ${YELLOW}│${RESET}"
echo -e "${YELLOW}│${RESET}  ⏱️  ${BOLD}Break Rest:${RESET}   30 Minutes countdown between batches         ${YELLOW}│${RESET}"
echo -e "${YELLOW}│${RESET}  🔄 ${BOLD}Auto-Boot:${RESET}    Enabled (Resumes automatically after reboot) ${YELLOW}│${RESET}"
echo -e "${YELLOW}│${RESET}  🛑 ${BOLD}To Stop:${RESET}      Run: ./stop.sh                               ${YELLOW}│${RESET}"
echo -e "${YELLOW}│${RESET}  📊 ${BOLD}To Check:${RESET}     Run: ./status.sh                             ${YELLOW}│${RESET}"
echo -e "${YELLOW}╰──────────────────────────────────────────────────────────────╯${RESET}\n"

echo -e "${CYAN}Streaming live activity below...${RESET}"
echo -e "${DIM}(Press ${RED}Ctrl+C${RESET}${DIM} anytime to detach and close terminal — the bot KEEPS WORKING!)${RESET}\n"

sleep 1
trap 'echo -e "\n\n${GREEN}✓ Detached from log viewer!${RESET}\n${YELLOW}⚡ Auto-Pilot continues working 24/7 in the background.${RESET}\n${DIM}To re-attach: ./status.sh or tail -f autopilot.log${RESET}\n${DIM}To stop:      ./stop.sh${RESET}"; exit 0' INT
tail -f "$LOG_FILE"
