#!/usr/bin/env bash
# ============================================================
# 📊 Check Developer Auto-Pilot Status & Metrics
# Usage:
#   ./status.sh       (Show full dashboard and exit immediately)
#   ./status.sh -f    (Stream live activity logs in real-time)
# ============================================================

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$DIR/autopilot.pid"
LOG_FILE="$DIR/autopilot.log"
HISTORY_FILE="$DIR/followed_history.json"
STATE_FILE="$DIR/daily_state.json"

GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
CYAN='\033[96m'
MAGENTA='\033[95m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

RUNNING=0
PID=""
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
        RUNNING=1
    else
        # Stale PID file
        rm -f "$PID_FILE"
    fi
fi

# Parse history counts
TOTAL_FOLLOWED=0
TOTAL_RECORDS=0
if [ -f "$HISTORY_FILE" ]; then
    COUNTS=$(python3 -c "
import json
try:
    with open('$HISTORY_FILE') as f:
        d = json.load(f)
        print(len(d.get('followed', [])), len(d.get('records', [])))
except Exception:
    print('0 0')
" 2>/dev/null)
    TOTAL_FOLLOWED=$(echo "$COUNTS" | awk '{print $1}')
    TOTAL_RECORDS=$(echo "$COUNTS" | awk '{print $2}')
fi

# Parse today's state
TODAY_RUNS=0
TODAY_FOLLOWS=0
TODAY_DATE=$(date +%Y-%m-%d)
if [ -f "$STATE_FILE" ]; then
    STATE_COUNTS=$(python3 -c "
import json
try:
    with open('$STATE_FILE') as f:
        d = json.load(f)
        runs = d.get('runs', {}).get('$TODAY_DATE', 0)
        follows = d.get('today_follows', 0)
        print(runs, follows)
except Exception:
    print('0 0')
" 2>/dev/null)
    TODAY_RUNS=$(echo "$STATE_COUNTS" | awk '{print $1}')
    TODAY_FOLLOWS=$(echo "$STATE_COUNTS" | awk '{print $2}')
fi

BOX_WIDTH=68
echo -e "\n${CYAN}╭────────────────────────────────────────────────────────────────────╮${RESET}"
echo -e "${CYAN}│${BOLD}             📊 DEVELOPER AUTO-PILOT SYSTEM STATUS                  ${RESET}${CYAN}│${RESET}"
echo -e "${CYAN}├────────────────────────────────────────────────────────────────────┤${RESET}"

if [ "$RUNNING" -eq 1 ]; then
    PROC_INFO=$(ps -p "$PID" -o etime=,%mem=,%cpu= 2>/dev/null | awk '{print "Uptime: "$1" | Memory: "$2"% | CPU: "$3"%"}')
    echo -e "${CYAN}│${RESET}  ● ${BOLD}Process Status:${RESET}   ${GREEN}${BOLD}ACTIVE & RUNNING 24/7 (PID: ${PID})${RESET}              ${CYAN}│${RESET}"
    echo -e "${CYAN}│${RESET}    ${DIM}${PROC_INFO}${RESET}${CYAN}│${RESET}"
else
    echo -e "${CYAN}│${RESET}  ○ ${BOLD}Process Status:${RESET}   ${RED}${BOLD}STOPPED (Not running)${RESET}                              ${CYAN}│${RESET}"
    echo -e "${CYAN}│${RESET}    ${DIM}To start in background: ./start.sh${RESET}                               ${CYAN}│${RESET}"
fi

echo -e "${CYAN}│${RESET}  🎯 ${BOLD}Target Focus:${RESET}     Software Engineers, Software & Backend Devs   ${CYAN}│${RESET}"
echo -e "${CYAN}│${RESET}  👥 ${BOLD}Total Followed:${RESET}   ${BOLD}${TOTAL_FOLLOWED}${RESET} unique accounts in database                  ${CYAN}│${RESET}"
echo -e "${CYAN}│${RESET}  📜 ${BOLD}Logged Follows:${RESET}   ${BOLD}${TOTAL_RECORDS}${RESET} records in follows.log                       ${CYAN}│${RESET}"
echo -e "${CYAN}│${RESET}  📅 ${BOLD}Today's Batches:${RESET}  ${BOLD}${TODAY_RUNS}${RESET} batches completed today                      ${CYAN}│${RESET}"
echo -e "${CYAN}╰────────────────────────────────────────────────────────────────────╯${RESET}\n"

# Recent Follows snippet
if [ -f "$HISTORY_FILE" ] && [ "$TOTAL_RECORDS" -gt 0 ]; then
    echo -e "${BOLD}Last Followed Developers:${RESET}"
    python3 -c "
import json
try:
    with open('$HISTORY_FILE') as f:
        d = json.load(f)
        recs = d.get('records', [])[-5:]
        recs.reverse()
        for r in recs:
            print(f\"  • \033[1m@{r.get('username')}\033[0m \033[92m[{r.get('role', 'Developer')}]\033[0m \033[90m({r.get('timestamp')}) - {r.get('location')}\033[0m\")
except Exception:
    pass
" 2>/dev/null
    echo
fi

# Log snippet
if [ -f "$LOG_FILE" ]; then
    echo -e "${DIM}Recent Log Output (last 12 lines):${RESET}"
    echo -e "${DIM}──────────────────────────────────────────────────────────────────────${RESET}"
    tail -n 12 "$LOG_FILE" 2>/dev/null || true
    echo -e "${DIM}──────────────────────────────────────────────────────────────────────${RESET}"
fi

# Live stream if requested
if [ "$1" = "-f" ] || [ "$1" = "--follow" ] || [ "$1" = "-w" ] || [ "$1" = "--watch" ]; then
    if [ "$RUNNING" -eq 1 ]; then
        echo -e "\n${CYAN}Streaming live activity (Press Ctrl+C to detach)...${RESET}\n"
        TAIL_PID=""
        cleanup_status_tail() {
            if [ -n "$TAIL_PID" ]; then
                kill "$TAIL_PID" 2>/dev/null || true
            fi
            echo -e "\n${GREEN}✓ Detached from live log.${RESET}"
            exit 0
        }
        trap cleanup_status_tail INT TERM
        tail -f "$LOG_FILE" &
        TAIL_PID=$!
        wait "$TAIL_PID"
    else
        echo -e "\n${YELLOW}[!] Bot is stopped. Run ./start.sh to launch.${RESET}\n"
    fi
else
    echo -e "\n${DIM}💡 Tip: Run ${BOLD}./status.sh -f${RESET}${DIM} to stream live activity in real time.${RESET}"
    echo -e "${DIM}💡 Tip: Run ${BOLD}./stop.sh${RESET}${DIM} to stop the background process.${RESET}\n"
fi
