#!/usr/bin/env bash
# ============================================================
# 🚀 Developer Auto-Pilot 24/7 Launcher
# Target: Software Engineers, Software Developers & Backend Developers Worldwide
# Works 24/7 continuously in the background
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
    if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚡ Auto-Pilot is ALREADY RUNNING in the background (PID: ${PID})${RESET}"
        if [ "$1" != "-d" ] && [ "$1" != "--detach" ]; then
            echo -e "${DIM}Streaming live output below (Press Ctrl+C to detach — bot will keep running!):${RESET}\n"
            TAIL_PID=""
            cleanup_tail() {
                if [ -n "$TAIL_PID" ]; then
                    kill "$TAIL_PID" 2>/dev/null || true
                fi
                echo -e "\n${GREEN}✓ Detached. Auto-Pilot continues running in background.${RESET}"
                exit 0
            }
            trap cleanup_tail INT TERM
            tail -n 25 -f "$LOG_FILE" &
            TAIL_PID=$!
            wait "$TAIL_PID"
        else
            echo -e "${DIM}To view logs: ./status.sh -f or tail -f autopilot.log${RESET}"
        fi
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

# Check for detach flag and filter arguments
DETACH=0
FILTERED_ARGS=()
for arg in "$@"; do
    if [ "$arg" = "-d" ] || [ "$arg" = "--detach" ]; then
        DETACH=1
    else
        FILTERED_ARGS+=("$arg")
    fi
done

# Parse extra arguments
EXTRA_ARGS=()
if [ "${#FILTERED_ARGS[@]}" -eq 0 ]; then
    # Default is global software engineers, software developers, and backend developers worldwide
    EXTRA_ARGS=("--target" "global" "--gender" "all")
elif [ "${#FILTERED_ARGS[@]}" -eq 1 ] && [[ "${FILTERED_ARGS[0]}" =~ ^(all|female|girl|girls|male|boy|boys)$ ]]; then
    EXTRA_ARGS=("--target" "global" "--gender" "${FILTERED_ARGS[0]}")
else
    EXTRA_ARGS=("${FILTERED_ARGS[@]}")
fi

# Clean up any leftover stray tail or autofollow processes
pkill -f "tail -f.*autopilot.log" 2>/dev/null || true

# Launch background process completely unbuffered and detached
setsid env PYTHONUNBUFFERED=1 python3 -u "$DIR/autofollow.py" --auto "${EXTRA_ARGS[@]}" </dev/null >> "$LOG_FILE" 2>&1 &
PID=$!
sleep 1
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${RED}[!] Error: Auto-Pilot failed to stay running. Check $LOG_FILE for details:${RESET}"
    tail -n 10 "$LOG_FILE"
    exit 1
fi
echo "$PID" > "$PID_FILE"

# Setup automatic resume on reboot & 10-minute watchdog to keep working 24/7 all the time
CRON_REBOOT="@reboot cd $DIR && /bin/bash start.sh -d > /dev/null 2>&1"
CRON_WATCHDOG="*/10 * * * * cd $DIR && /bin/bash start.sh -d > /dev/null 2>&1"
CURRENT_CRON=$(crontab -l 2>/dev/null || true)
CLEANED_CRON=$(echo "$CURRENT_CRON" | grep -v -F "start.sh" || true)
(echo "$CLEANED_CRON"; echo "$CRON_REBOOT"; echo "$CRON_WATCHDOG") | grep -v '^$' | crontab - 2>/dev/null || true

echo -e "\n${GREEN}╭──────────────────────────────────────────────────────────────╮${RESET}"
echo -e "${GREEN}│${BOLD}      🚀 DEVELOPER AUTO-PILOT IS NOW WORKING 24/7!             ${RESET}${GREEN}│${RESET}"
echo -e "${GREEN}├──────────────────────────────────────────────────────────────┤${RESET}"
echo -e "${GREEN}│${RESET}  🚀 ${BOLD}Status:${RESET}       RUNNING in background (PID: ${PID})          ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}  💻 ${BOLD}Target Roles:${RESET} Software Engineers, Software & Backend Devs   ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}  👥 ${BOLD}Batch Size:${RESET}   250 developers per cycle                     ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}  ⏱️  ${BOLD}Break Rest:${RESET}   30 Minutes countdown between batches         ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}  🔄 ${BOLD}Auto-Boot:${RESET}    Enabled (Resumes automatically after reboot) ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}  🛑 ${BOLD}To Stop:${RESET}      Run: ./stop.sh                               ${GREEN}│${RESET}"
echo -e "${GREEN}│${RESET}  📊 ${BOLD}To Check:${RESET}     Run: ./status.sh                             ${GREEN}│${RESET}"
echo -e "${GREEN}╰──────────────────────────────────────────────────────────────╯${RESET}\n"

# Stream live log if not detached
if [ "$DETACH" -eq 1 ]; then
    echo -e "${DIM}Auto-Pilot started in detached mode. Run ./status.sh to check status.${RESET}"
    exit 0
fi

echo -e "${CYAN}Streaming live activity below...${RESET}"
echo -e "${DIM}(Press ${RED}Ctrl+C${RESET}${DIM} anytime to detach and close terminal — the bot KEEPS WORKING!)${RESET}\n"
sleep 1

TAIL_PID=""
cleanup_stream() {
    if [ -n "$TAIL_PID" ]; then
        kill "$TAIL_PID" 2>/dev/null || true
    fi
    echo -e "\n\n${GREEN}✓ Detached from log viewer!${RESET}\n${YELLOW}⚡ Auto-Pilot continues working 24/7 in the background.${RESET}\n${DIM}To check status: ./status.sh${RESET}\n${DIM}To stop:         ./stop.sh${RESET}"
    exit 0
}
trap cleanup_stream INT TERM
tail -f "$LOG_FILE" &
TAIL_PID=$!
wait "$TAIL_PID"
