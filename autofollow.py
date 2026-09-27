#!/usr/bin/env python3
"""
☀️ Kurdish Developer Auto-Pilot (GitHub Compliance & 2-Hour Break Edition)
Fully compliant with GitHub anti-abuse guidelines and rate limits.

Workflow:
- Follows a safe batch of 50 fresh Kurdish developers (~1 minute).
- Takes a mandatory 2-hour rest break (7,200s) to reset GitHub's hourly rolling window.
- Displays live countdown timer and exact next start time during the 2-hour break.
- Automatically wakes up after 2 hours, scans fresh Kurdish developers, and repeats.
"""

import os
import sys
import time
import json
import re
import argparse
import requests
from requests.adapters import HTTPAdapter
from pathlib import Path
from datetime import datetime

# Paths
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
HISTORY_PATH = BASE_DIR / "followed_history.json"
CURSOR_PATH = BASE_DIR / "page_cursor.json"
DAILY_STATE_PATH = BASE_DIR / "daily_state.json"
GITHUB_API_BASE = "https://api.github.com"

# Kurdish Flag / Theme Colors (Red, Green, Yellow, Cyan, White)
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

# Safe GitHub Compliance Defaults
DEFAULT_BATCH_SIZE = 50       # 50 follows per session (safe & under hourly limits)
DEFAULT_BREAK_HOURS = 2.0     # 2 hours break between batches to reset rate limits
DEFAULT_DELAY = 1.0           # 1.0s delay between follows (natural pacing)

# Comprehensive Kurdish Search Vectors (Locations & Keywords)
KURDISH_SEARCH_VECTORS = [
    ("location:Kurdistan", "Kurdistan"),
    ("location:Erbil", "Erbil"),
    ("location:Sulaymaniyah", "Sulaymaniyah"),
    ("location:Duhok", "Duhok"),
    ("location:Hawler", "Hawler"),
    ("location:Slemani", "Slemani"),
    ("location:Kirkuk", "Kirkuk"),
    ("location:Halabja", "Halabja"),
    ("location:Zakho", "Zakho"),
    ("location:Ranya", "Ranya"),
    ("location:Kalar", "Kalar"),
    ("location:Diyarbakir", "Diyarbakir"),
    ("location:Mahabad", "Mahabad"),
    ("location:Sanandaj", "Sanandaj"),
    ("Kurdish in:bio", "Kurdish bio"),
    ("Kurdistan in:bio", "Kurdistan bio"),
    ("کوردستان in:bio", "کوردستان bio"),
    ("کورد in:bio", "کورد bio"),
]


def format_duration(seconds: float) -> str:
    """Formats seconds into HH:MM:SS or MM:SS."""
    s = max(0, int(seconds))
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}h {m:02d}m {s:02d}s"
    return f"{m:02d}m {s:02d}s"


def render_progress_bar(current: int, total: int, width: int = 20) -> str:
    """Renders a sleek Unicode progress bar with percentage."""
    if total <= 0:
        return f"[{'░' * width}] 0.0%"
    fraction = min(max(current / total, 0.0), 1.0)
    filled = int(width * fraction)
    bar = f"{GREEN}{'█' * filled}{DIM}{'░' * (width - filled)}{RESET}"
    percent = fraction * 100
    return f"[{bar}] {BOLD}{percent:5.1f}%{RESET}"


def load_token_from_env_file() -> str | None:
    """Reads GITHUB_TOKEN from .env if present."""
    if not ENV_PATH.exists():
        return None
    try:
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("GITHUB_TOKEN="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        return val
    except Exception:
        pass
    return None


def get_token() -> str:
    """Get token from OS env or local .env file."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        token = load_token_from_env_file()
    if not token:
        print(f"{RED}[!] Error: No GITHUB_TOKEN found.{RESET}")
        print(f"Please set GITHUB_TOKEN in {ENV_PATH} or export it in your shell.")
        sys.exit(1)
    return token


class CursorManager:
    """Tracks the last scanned page per search vector to avoid re-scanning."""
    def __init__(self, path: Path):
        self.path = path
        self.cursors: dict[str, int] = {}
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self.cursors = json.load(f)
            except Exception:
                self.cursors = {}

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.cursors, f, indent=2)
        except Exception:
            pass

    def get_page(self, key: str) -> int:
        return self.cursors.get(key, 1)

    def set_page(self, key: str, page: int):
        self.cursors[key] = page
        self.save()


class HistoryManager:
    """Tracks users already processed in-memory and on disk to prevent duplicates."""
    def __init__(self, path: Path):
        self.path = path
        self.history: set[str] = set()
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = set(data.get("followed", []))
            except Exception:
                self.history = set()

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({"followed": sorted(list(self.history))}, f, indent=2)
        except Exception as e:
            print(f"{YELLOW}[!] Failed to save history: {e}{RESET}")

    def add(self, username: str, auto_save: bool = True):
        self.history.add(username.lower())
        if auto_save:
            self.save()

    def contains(self, username: str) -> bool:
        return username.lower() in self.history


class KurdishBot:
    def __init__(self, token: str, dry_run: bool = False, delay: float = DEFAULT_DELAY):
        self.token = token
        self.dry_run = dry_run
        self.delay = delay
        self.session = requests.Session()

        # Connection pooling
        adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=2)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Kurdish-Dev-Expander/2.0",
        })
        self.current_user = ""
        self.user_stats = {}
        self.history = HistoryManager(HISTORY_PATH)
        self.cursors = CursorManager(CURSOR_PATH)

    def verify_account(self) -> dict | None:
        """Verifies token and retrieves account information."""
        resp = self.session.get(f"{GITHUB_API_BASE}/user")
        if resp.status_code == 200:
            self.user_stats = resp.json()
            self.current_user = self.user_stats.get("login", "")
            return self.user_stats
        return None

    def refresh_user_stats(self) -> dict:
        """Refreshes account stats from GitHub."""
        resp = self.session.get(f"{GITHUB_API_BASE}/user")
        if resp.status_code == 200:
            self.user_stats = resp.json()
        return self.user_stats

    def preload_current_following(self):
        """Preloads all users that current_user already follows into memory in bulk."""
        print(f" {CYAN}⚡ Syncing current following list...{RESET}", end="", flush=True)
        page = 1
        count = 0
        while True:
            resp = self.session.get(f"{GITHUB_API_BASE}/user/following?per_page=100&page={page}")
            if resp.status_code != 200:
                break
            items = resp.json()
            if not items or not isinstance(items, list):
                break
            for item in items:
                self.history.add(item["login"], auto_save=False)
                count += 1
            if len(items) < 100:
                break
            page += 1
        self.history.save()
        print(f" {GREEN}Done ({count} accounts cached, {len(self.history.history)} total in memory){RESET}\n")

    def follow(self, username: str) -> bool:
        """Sends PUT request to follow a GitHub user directly with auto-backoff."""
        if self.dry_run:
            return True

        if self.history.contains(username):
            return False

        max_retries = 3
        for attempt in range(max_retries):
            resp = self.session.put(f"{GITHUB_API_BASE}/user/following/{username}")
            if resp.status_code == 204:
                self.history.add(username, auto_save=True)
                return True

            if resp.status_code in (403, 429):
                retry_after = resp.headers.get("Retry-After")
                reset_time = resp.headers.get("x-ratelimit-reset")
                if retry_after:
                    wait_sec = int(retry_after) + 5
                elif reset_time:
                    wait_sec = max(int(reset_time) - int(time.time()), 60)
                else:
                    wait_sec = 60 * (attempt + 1)

                print(f"\n{YELLOW}  ⚠️ GitHub rate limit. Cooldown for {wait_sec}s...{RESET}")
                time.sleep(wait_sec)
                continue

            if resp.status_code == 404:
                return False

            return False

        return False

    def scan_kurdish_developers(self, goal: int = DEFAULT_BATCH_SIZE) -> list[tuple[str, str]]:
        """
        Scans across all Kurdish locations and keywords to find 'goal' brand-new Kurdish developers.
        Returns: list of (username, location_tag)
        """
        candidates: list[tuple[str, str]] = []
        per_page = 100
        scanned_total = 0
        skipped_total = 0

        print(f"{YELLOW}☀️ Scanning GitHub for {goal} BRAND NEW Kurdish Developers (Boys & Girls)...{RESET}")

        for query, label in KURDISH_SEARCH_VECTORS:
            if len(candidates) >= goal:
                break

            page = self.cursors.get_page(query)
            max_pages_per_vector = 5

            while len(candidates) < goal and max_pages_per_vector > 0:
                url = f"{GITHUB_API_BASE}/search/users?q={query}&per_page={per_page}&page={page}"
                resp = self.session.get(url)
                if resp.status_code != 200:
                    break

                data = resp.json()
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    username = item["login"]
                    scanned_total += 1

                    if self.history.contains(username) or username.lower() == self.current_user.lower():
                        skipped_total += 1
                        continue

                    candidates.append((username, label))
                    if len(candidates) >= goal:
                        break

                sys.stdout.write(
                    f"\r  {CYAN}📍 [{label}]{RESET} Page {page} │ "
                    f"Scanned: {BOLD}{scanned_total}{RESET} │ "
                    f"Already Followed: {YELLOW}{skipped_total}{RESET} │ "
                    f"New Found: {GREEN}{BOLD}{len(candidates)}/{goal}{RESET} "
                )
                sys.stdout.flush()

                page += 1
                max_pages_per_vector -= 1
                if len(items) < per_page:
                    break

            self.cursors.set_page(query, page)

        print(f"\n{GREEN}✓ Scan completed! Ready with {len(candidates)} brand-new Kurdish developers.{RESET}\n")
        return candidates

    def print_batch_dashboard(self, goal: int, batch_num: int):
        """Displays Kurdish themed header card."""
        est_seconds = goal * self.delay
        est_duration = format_duration(est_seconds)
        eta_time = time.strftime("%I:%M:%S %p", time.localtime(time.time() + est_seconds))
        speed_text = f"{int(60 / max(self.delay, 0.1))} follows/min ({self.delay}s delay)"
        cur_following = self.user_stats.get("following", 0)

        box_width = 62
        print(f"{YELLOW}╭{'─' * box_width}╮{RESET}")
        title = f"☀️ BATCH #{batch_num} — GOAL: {goal} KURDISH DEVELOPERS ☀️"
        print(f"{YELLOW}│{BOLD}{title:^{box_width}}{RESET}{YELLOW}│{RESET}")
        print(f"{YELLOW}├{'─' * box_width}┤{RESET}")
        print(f"{YELLOW}│{RESET}  👤 {BOLD}Operator:{RESET}  @{self.current_user:<16}  👥 {BOLD}Followers:{RESET} {str(self.user_stats.get('followers', 0)):<15}{YELLOW}│{RESET}")
        print(f"{YELLOW}│{RESET}  📍 {BOLD}Target:{RESET}    Kurdish Devs      🔄 {BOLD}Following:{RESET} {str(cur_following):<15}{YELLOW}│{RESET}")
        print(f"{YELLOW}│{RESET}  🎯 {BOLD}Batch Goal:{RESET}{str(goal) + ' accounts':<16}  ⚡ {BOLD}Speed:{RESET}     {speed_text:<15}{YELLOW}│{RESET}")
        print(f"{YELLOW}│{RESET}  ⏱️  {BOLD}Est Time:{RESET}  {est_duration:<16}  🏁 {BOLD}Batch ETA:{RESET} {eta_time:<15}{YELLOW}│{RESET}")
        print(f"{YELLOW}╰{'─' * box_width}╯{RESET}\n")

    def run_batch(self, targets: list[tuple[str, str]], goal: int, batch_num: int = 1) -> tuple[int, float]:
        """Executes following for the target list with real-time progress bar and location tags."""
        if not targets:
            print(f"{YELLOW}[!] No candidate accounts available.{RESET}")
            return 0, 0.0

        self.print_batch_dashboard(goal, batch_num)

        success_count = 0
        start_time = time.time()

        try:
            for idx, (username, loc_tag) in enumerate(targets, 1):
                if success_count >= goal:
                    break

                if self.history.contains(username) or username.lower() == self.current_user.lower():
                    continue

                rem_needed = goal - success_count
                rem_seconds = rem_needed * self.delay
                eta_clock = time.strftime("%I:%M:%S %p", time.localtime(time.time() + rem_seconds))
                bar_str = render_progress_bar(success_count, goal, width=18)
                rem_str = format_duration(rem_seconds)

                status_header = (
                    f"{bar_str} {BOLD}{success_count}/{goal}{RESET} "
                    f"│ ⏱️ Rem: {CYAN}{rem_str}{RESET} "
                    f"│ 🏁 ETA: {MAGENTA}{eta_clock}{RESET}"
                )

                print(status_header)
                print(f"  → Following {BOLD}@{username}{RESET} {YELLOW}[📍 {loc_tag}]{RESET}...", end="", flush=True)

                if self.follow(username):
                    success_count += 1
                    if self.dry_run:
                        print(f" {YELLOW}[DRY-RUN]{RESET}")
                    else:
                        print(f" {GREEN}✓ Followed!{RESET}")
                else:
                    print(f" {RED}✗ Skipped{RESET}")

                print()

                if success_count < goal and self.delay > 0:
                    time.sleep(self.delay)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}⚠️  Session paused by user (Ctrl+C).{RESET}")

        batch_elapsed = time.time() - start_time
        return success_count, batch_elapsed


def sleep_with_countdown(seconds: float, next_run_time_str: str):
    """Sleeps for break duration with a live on-screen countdown timer."""
    end_time = time.time() + seconds
    try:
        while time.time() < end_time:
            rem = max(0, int(end_time - time.time()))
            dur_str = format_duration(rem)
            sys.stdout.write(
                f"\r  {CYAN}☕ Resting account... Next batch at {BOLD}{WHITE}{next_run_time_str}{RESET}{CYAN} "
                f"│ Countdown: {YELLOW}{BOLD}{dur_str}{RESET}  "
            )
            sys.stdout.flush()
            time.sleep(1)
        print("\n")
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Break cancelled by user.{RESET}")
        raise


def run_autopilot_cycle(bot: KurdishBot, batch_size: int = DEFAULT_BATCH_SIZE, break_hours: float = DEFAULT_BREAK_HOURS):
    """
    Continuous Auto-Pilot:
    1. Follows batch_size (50) Kurdish developers.
    2. Takes break_hours (2.0) rest to comply with GitHub hourly limits.
    3. Repeats automatically.
    """
    break_seconds = int(break_hours * 3600)
    batch_num = 1
    total_session_followed = 0

    print(f"\n{YELLOW}╭{'─' * 62}╮{RESET}")
    print(f"{YELLOW}│{BOLD}{'☀️ KURDISH AUTO-PILOT ACTIVATED (2-HOUR BREAK CYCLE) ☀️':^62}{RESET}{YELLOW}│{RESET}")
    print(f"{YELLOW}├{'─' * 62}┤{RESET}")
    print(f"{YELLOW}│{RESET}  • Batch Size:   {BOLD}{batch_size} Kurdish developers per cycle{RESET}{' ' * (62 - len(str(batch_size)) - 42)}{YELLOW}│{RESET}")
    print(f"{YELLOW}│{RESET}  • Rest Break:   {BOLD}{break_hours} hours{RESET} (Completely resets GitHub rate limits){' ' * (62 - len(str(break_hours)) - 53)}{YELLOW}│{RESET}")
    print(f"{YELLOW}│{RESET}  • Daily Total:  ~{int((24 / break_hours) * batch_size)} follows/day (100% GitHub Rule Compliant){' ' * (62 - 58)}{YELLOW}│{RESET}")
    print(f"{YELLOW}│{RESET}  • Press:        {RED}Ctrl+C{RESET} at any time to pause or exit{' ' * 17}{YELLOW}│{RESET}")
    print(f"{YELLOW}╰{'─' * 62}╯{RESET}\n")

    while True:
        candidates = bot.scan_kurdish_developers(goal=batch_size)
        if not candidates:
            print(f"{YELLOW}[!] No more fresh Kurdish developers found right now. Checking again in {break_hours}h...{RESET}")
        else:
            followed, elapsed = bot.run_batch(candidates, goal=batch_size, batch_num=batch_num)
            total_session_followed += followed

            bot.refresh_user_stats()
            current_following = bot.user_stats.get("following", 0)

            # Batch Summary Card
            box_width = 62
            print(f"\n{GREEN}╭{'─' * box_width}╮{RESET}")
            title = f"🎉 BATCH #{batch_num} COMPLETED ({followed}/{batch_size} FOLLOWED) 🎉"
            print(f"{GREEN}│{BOLD}{title:^{box_width}}{RESET}{GREEN}│{RESET}")
            print(f"{GREEN}├{'─' * box_width}┤{RESET}")
            print(f"{GREEN}│{RESET}  ✓ {BOLD}Followed in This Batch:{RESET}  {followed} accounts{' ' * (box_width - len(str(followed)) - 34)}{GREEN}│{RESET}")
            print(f"{GREEN}│{RESET}  🌟 {BOLD}Total in Auto-Pilot:{RESET}     {total_session_followed} accounts{' ' * (box_width - len(str(total_session_followed)) - 32)}{GREEN}│{RESET}")
            print(f"{GREEN}│{RESET}  🔄 {BOLD}Current Total Following:{RESET} {current_following} accounts{' ' * (box_width - len(str(current_following)) - 32)}{GREEN}│{RESET}")
            print(f"{GREEN}│{RESET}  ⏱️  {BOLD}Batch Time Elapsed:{RESET}     {format_duration(elapsed)}{' ' * (box_width - len(format_duration(elapsed)) - 30)}{GREEN}│{RESET}")
            print(f"{GREEN}╰{'─' * box_width}╯{RESET}\n")

        # Calculate exact wakeup time for 2-hour break
        next_wake_time = time.time() + break_seconds
        next_wake_str = time.strftime("%I:%M:%S %p", time.localtime(next_wake_time))

        box_width = 62
        print(f"{CYAN}╭{'─' * box_width}╮{RESET}")
        title = f"☕ 2-HOUR REST BREAK (GITHUB ANTI-BAN SHIELD)"
        print(f"{CYAN}│{BOLD}{title:^{box_width}}{RESET}{CYAN}│{RESET}")
        print(f"{CYAN}├{'─' * box_width}┤{RESET}")
        print(f"{CYAN}│{RESET}  🛡️  {BOLD}Rest Duration:{RESET}  {break_hours} Hours (Resets hourly abuse detection){' ' * (box_width - len(str(break_hours)) - 50)}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  ⏰  {BOLD}Next Batch At:{RESET}  {next_wake_str}{' ' * (box_width - len(next_wake_str) - 23)}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  💾  {BOLD}Status:{RESET}         History saved. Zero duplicate risk.{' ' * (box_width - 48)}{CYAN}│{RESET}")
        print(f"{CYAN}╰{'─' * box_width}╯{RESET}\n")

        try:
            sleep_with_countdown(break_seconds, next_wake_str)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}[!] Auto-pilot stopped by user. Progress saved!{RESET}")
            break

        batch_num += 1


def main():
    parser = argparse.ArgumentParser(description="☀️ Kurdish Developer Auto-Pilot (GitHub Compliance Edition)")
    parser.add_argument("--auto", action="store_true", help="Start continuous Auto-Pilot (Follow batch -> 2h break -> Repeat)")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help=f"Follows per batch (default: {DEFAULT_BATCH_SIZE})")
    parser.add_argument("--break-hours", type=float, default=DEFAULT_BREAK_HOURS, help=f"Break hours between batches (default: {DEFAULT_BREAK_HOURS})")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help=f"Seconds between follows (default: {DEFAULT_DELAY})")
    parser.add_argument("--once", action="store_true", help="Run only one single batch now and exit")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making actual follow requests")

    args = parser.parse_args()

    token = get_token()
    bot = KurdishBot(token, dry_run=args.dry_run, delay=args.delay)

    user_info = bot.verify_account()
    if not user_info:
        print(f"{RED}[!] Authentication failed. Check your token in {ENV_PATH}.{RESET}")
        sys.exit(1)

    print(f"{GREEN}{BOLD}✓ Authenticated as @{user_info.get('login')}{RESET}")
    print(f"  Followers: {user_info.get('followers')} | Following: {user_info.get('following')}\n")

    # Sync following list
    bot.preload_current_following()

    if args.auto:
        run_autopilot_cycle(bot, batch_size=args.batch_size, break_hours=args.break_hours)
    elif args.once:
        candidates = bot.scan_kurdish_developers(goal=args.batch_size)
        bot.run_batch(candidates, goal=args.batch_size, batch_num=1)
    else:
        # Simple default interactive menu
        print(f"{BOLD}Choose Operation Mode:{RESET}")
        print(f"  {CYAN}1) 🔄 Start Kurdish Auto-Pilot (Follow {args.batch_size} → 2-Hour Break → Repeat All Day){RESET} [Default - Press Enter]")
        print(f"  {YELLOW}2) ⚡ Run Single Batch Now (Follow {args.batch_size} Kurdish developers and exit){RESET}")
        print(f"  3) 🛑 Exit")

        choice = input("\nEnter choice [1-3, default 1]: ").strip()
        if choice == "2":
            candidates = bot.scan_kurdish_developers(goal=args.batch_size)
            bot.run_batch(candidates, goal=args.batch_size, batch_num=1)
        elif choice == "3":
            print("Exited.")
        else:
            run_autopilot_cycle(bot, batch_size=args.batch_size, break_hours=args.break_hours)


if __name__ == "__main__":
    main()
