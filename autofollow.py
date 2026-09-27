#!/usr/bin/env python3
"""
GitHub Network Expander Pro
A high-performance, cleanly-styled CLI tool to expand your GitHub network in 250-account batches.
Features:
- Unified terminal design with live percentage progress bar and ETA clock
- Batch workflow: Follows 250 accounts, then prompts to follow the NEXT 250 or stop
- Neutral company/organization examples (Google, Microsoft, Meta, etc.)
- In-memory pre-caching and HTTP connection pooling for turbo speeds
- Full rate-limit auto-cooldown and duplicate prevention
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

# Paths
BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"
HISTORY_PATH = BASE_DIR / "followed_history.json"
GITHUB_API_BASE = "https://api.github.com"

# Unified Styling Theme (Cyan & Emerald Green)
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

BATCH_SIZE = 250
DEFAULT_DELAY = 0.5  # Turbo speed: 0.5s


def format_duration(seconds: float) -> str:
    """Formats seconds into HH:MM:SS or MM:SS."""
    s = max(0, int(seconds))
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}h {m:02d}m {s:02d}s"
    return f"{m:02d}m {s:02d}s"


def render_progress_bar(current: int, total: int, width: int = 20) -> str:
    """Renders a sleek, modern progress bar with accurate percentage."""
    if total <= 0:
        return f"[{'░' * width}] 0.0%"
    fraction = min(max(current / total, 0.0), 1.0)
    filled = int(width * fraction)
    bar = f"{GREEN}{'█' * filled}{DIM}{'░' * (width - filled)}{RESET}"
    percent = fraction * 100
    return f"[{bar}] {BOLD}{percent:5.1f}%{RESET}"


def clean_input(raw: str) -> str:
    """Cleans URLs, @ symbols, and trailing slashes into clean identifiers."""
    val = raw.strip()
    val = re.sub(r"^https?://(www\.)?github\.com/", "", val, flags=re.IGNORECASE)
    val = val.lstrip("@").rstrip("/")
    if val.endswith(".git"):
        val = val[:-4]
    return val.strip()


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


class HistoryManager:
    """Tracks users already processed in-memory and on disk to prevent duplicate API requests."""
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


class GitHubBot:
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
            "User-Agent": "GitHub-Network-Expander/5.0",
        })
        self.current_user = ""
        self.user_stats = {}
        self.history = HistoryManager(HISTORY_PATH)
        self.page_cursor = {}  # Tracks pagination per target to avoid re-fetching pages

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
        print(f" {GREEN}Done ({count} accounts cached){RESET}\n")

    def follow(self, username: str) -> bool:
        """Sends PUT request to follow a GitHub user directly with auto-backoff."""
        if self.dry_run:
            return True

        max_retries = 3
        for attempt in range(max_retries):
            resp = self.session.put(f"{GITHUB_API_BASE}/user/following/{username}")
            if resp.status_code == 204:
                self.history.add(username, auto_save=True)
                return True

            # Handle Secondary Rate Limit / Abuse Detection
            if resp.status_code in (403, 429):
                retry_after = resp.headers.get("Retry-After")
                reset_time = resp.headers.get("x-ratelimit-reset")
                if retry_after:
                    wait_sec = int(retry_after) + 5
                elif reset_time:
                    wait_sec = max(int(reset_time) - int(time.time()), 60)
                else:
                    wait_sec = 45 * (attempt + 1)

                print(f"\n{YELLOW}  ⚠️ Rate limit active. Pausing {wait_sec}s for cooldown...{RESET}")
                time.sleep(wait_sec)
                continue

            if resp.status_code == 404:
                print(f" {YELLOW}(Not Found){RESET}", end="")
                return False

            print(f" {RED}(HTTP {resp.status_code}){RESET}", end="")
            return False

        return False

    def get_followers_of(self, target_user: str, count: int = BATCH_SIZE) -> list[str]:
        """Fetch fresh, unfollowed followers of a given user or organization."""
        clean_user = clean_input(target_user)
        candidates = []
        page = self.page_cursor.get(clean_user, 1)
        per_page = 100

        print(f"{CYAN}🔍 Collecting next {count} new accounts from @{clean_user}...{RESET}", end="", flush=True)
        while len(candidates) < count:
            url = f"{GITHUB_API_BASE}/users/{clean_user}/followers?per_page={per_page}&page={page}"
            resp = self.session.get(url)
            if resp.status_code != 200:
                break
            items = resp.json()
            if not items or not isinstance(items, list):
                break
            for item in items:
                username = item["login"]
                if not self.history.contains(username) and username.lower() != self.current_user.lower():
                    candidates.append(username)
                    if len(candidates) >= count:
                        break
            if len(items) < per_page:
                break
            page += 1

        self.page_cursor[clean_user] = page
        print(f" {GREEN}Ready ({len(candidates)} fresh accounts found).{RESET}")
        return candidates

    def get_contributors_of(self, repo: str, count: int = BATCH_SIZE) -> list[str]:
        """Fetch fresh contributors of an owner/repo."""
        clean_repo = clean_input(repo)
        candidates = []
        page = self.page_cursor.get(clean_repo, 1)
        per_page = 100

        print(f"{CYAN}🔍 Collecting next {count} new contributors from {clean_repo}...{RESET}", end="", flush=True)
        while len(candidates) < count:
            url = f"{GITHUB_API_BASE}/repos/{clean_repo}/contributors?per_page={per_page}&page={page}"
            resp = self.session.get(url)
            if resp.status_code != 200:
                break
            items = resp.json()
            if not items or not isinstance(items, list):
                break
            for item in items:
                if "login" in item:
                    username = item["login"]
                    if not self.history.contains(username) and username.lower() != self.current_user.lower():
                        candidates.append(username)
                        if len(candidates) >= count:
                            break
            if len(items) < per_page:
                break
            page += 1

        self.page_cursor[clean_repo] = page
        print(f" {GREEN}Ready ({len(candidates)} fresh accounts found).{RESET}")
        return candidates

    def search_users(self, query: str, count: int = BATCH_SIZE) -> list[str]:
        """Search fresh GitHub users matching a query."""
        candidates = []
        page = self.page_cursor.get(query, 1)
        per_page = 100

        print(f"{CYAN}🔍 Collecting next {count} new accounts from '{query}'...{RESET}", end="", flush=True)
        while len(candidates) < count:
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
                if not self.history.contains(username) and username.lower() != self.current_user.lower():
                    candidates.append(username)
                    if len(candidates) >= count:
                        break
            if len(items) < per_page:
                break
            page += 1

        self.page_cursor[query] = page
        print(f" {GREEN}Ready ({len(candidates)} fresh accounts found).{RESET}")
        return candidates

    def print_batch_header(self, batch_num: int, target_label: str, goal: int):
        """Displays a clean, styled dashboard card."""
        est_seconds = goal * self.delay
        est_duration = format_duration(est_seconds)
        eta_time = time.strftime("%I:%M:%S %p", time.localtime(time.time() + est_seconds))
        speed_text = f"~{int(60 / max(self.delay, 0.1))} follows/min ({self.delay}s delay)"
        cur_following = self.user_stats.get("following", 0)

        box_width = 62
        print(f"\n{CYAN}╭{'─' * box_width}╮{RESET}")
        title = f"⚡ BATCH #{batch_num} — TARGET: {goal} FOLLOWS ⚡"
        print(f"{CYAN}│{BOLD}{title:^{box_width}}{RESET}{CYAN}│{RESET}")
        print(f"{CYAN}├{'─' * box_width}┤{RESET}")
        print(f"{CYAN}│{RESET}  👤 {BOLD}Operator:{RESET}  @{self.current_user:<16}  👥 {BOLD}Followers:{RESET} {str(self.user_stats.get('followers', 0)):<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  🎯 {BOLD}Source:{RESET}    {target_label:<16}  🔄 {BOLD}Following:{RESET} {str(cur_following):<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  🎯 {BOLD}Batch Goal:{RESET}{str(goal) + ' accounts':<16}  ⚡ {BOLD}Speed:{RESET}     {speed_text:<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  ⏱️  {BOLD}Est Time:{RESET}  {est_duration:<16}  🏁 {BOLD}Batch ETA:{RESET} {eta_time:<15}{CYAN}│{RESET}")
        print(f"{CYAN}╰{'─' * box_width}╯{RESET}\n")

    def run_batch(self, targets: list[str], goal: int, batch_num: int, target_label: str) -> tuple[int, float]:
        """Executes a single batch with real-time percentage progress bar and timers."""
        if not targets:
            print(f"{YELLOW}[!] No candidate accounts available.{RESET}")
            return 0, 0.0

        self.print_batch_header(batch_num, target_label, goal)

        success_count = 0
        start_time = time.time()

        try:
            for idx, username in enumerate(targets, 1):
                if success_count >= goal:
                    break

                if username.lower() == self.current_user.lower():
                    continue

                if self.history.contains(username):
                    continue

                # Live timer calculations
                rem_needed = goal - success_count
                rem_seconds = rem_needed * self.delay
                eta_clock = time.strftime("%I:%M:%S %p", time.localtime(time.time() + rem_seconds))
                bar_str = render_progress_bar(success_count, goal, width=18)
                rem_str = format_duration(rem_seconds)

                # Unified progress line
                status_header = (
                    f"{bar_str} {BOLD}{success_count}/{goal}{RESET} "
                    f"│ ⏱️ Rem: {CYAN}{rem_str}{RESET} "
                    f"│ 🏁 ETA: {MAGENTA}{eta_clock}{RESET}"
                )

                print(status_header)
                print(f"  → Following {BOLD}@{username}{RESET}...", end="", flush=True)

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
            print(f"\n{YELLOW}⚠️  Batch paused by user (Ctrl+C).{RESET}")

        batch_elapsed = time.time() - start_time
        return success_count, batch_elapsed


def ask_speed() -> float:
    """Lets user select speed mode."""
    print(f"\n⚡ {BOLD}Select Speed Mode:{RESET}")
    print(f"  1) {CYAN}🚀 Turbo{RESET} (0.5s delay - ~120 follows/min) [Recommended]")
    print(f"  2) {GREEN}⚡ Fast{RESET}  (1.0s delay - ~60 follows/min)")
    print(f"  3) {YELLOW}🛡️ Safe{RESET}  (2.0s delay - ~30 follows/min)")

    choice = input("   Enter choice [1-3, default 1]: ").strip()
    if choice == "2":
        return 1.0
    elif choice == "3":
        return 2.0
    return 0.5


def run_continuous_session(bot: GitHubBot, mode: str, target_val: str, batch_size: int = BATCH_SIZE):
    """Loops in batches of 250: after each 250, prompts to follow the NEXT 250 or stop."""
    batch_num = 1
    total_session_followed = 0
    total_session_time = 0.0

    target_label = f"@{target_val}" if mode == "user" else target_val

    while True:
        # Fetch fresh candidates for this batch
        if mode == "user":
            candidates = bot.get_followers_of(target_val, count=batch_size)
        elif mode == "search":
            candidates = bot.search_users(target_val, count=batch_size)
        elif mode == "repo":
            candidates = bot.get_contributors_of(target_val, count=batch_size)
        else:
            candidates = [clean_input(u) for u in target_val.split(",") if clean_input(u)]

        if not candidates:
            print(f"\n{YELLOW}[!] No more fresh unfollowed accounts found from {target_label}.{RESET}")
            break

        followed, elapsed = bot.run_batch(candidates, goal=batch_size, batch_num=batch_num, target_label=target_label)
        total_session_followed += followed
        total_session_time += elapsed

        # Refresh stats from GitHub
        bot.refresh_user_stats()
        current_following = bot.user_stats.get("following", 0)

        # Batch Completion Card
        box_width = 62
        print(f"\n{GREEN}╭{'─' * box_width}╮{RESET}")
        title = f"🎉 BATCH #{batch_num} COMPLETED ({followed}/{batch_size}) 🎉"
        print(f"{GREEN}│{BOLD}{title:^{box_width}}{RESET}{GREEN}│{RESET}")
        print(f"{GREEN}├{'─' * box_width}┤{RESET}")
        print(f"{GREEN}│{RESET}  ✓ {BOLD}Followed in Batch #{batch_num}:{RESET}   {followed} accounts{' ' * (box_width - len(str(followed)) - 32)}{GREEN}│{RESET}")
        print(f"{GREEN}│{RESET}  🌟 {BOLD}Total in This Session:{RESET}     {total_session_followed} accounts{' ' * (box_width - len(str(total_session_followed)) - 32)}{GREEN}│{RESET}")
        print(f"{GREEN}│{RESET}  🔄 {BOLD}Current Total Following:{RESET}   {current_following} accounts{' ' * (box_width - len(str(current_following)) - 32)}{GREEN}│{RESET}")
        print(f"{GREEN}│{RESET}  ⏱️  {BOLD}Batch Time Elapsed:{RESET}       {format_duration(elapsed)}{' ' * (box_width - len(format_duration(elapsed)) - 32)}{GREEN}│{RESET}")
        print(f"{GREEN}╰{'─' * box_width}╯{RESET}\n")

        # Prompt user to continue or stop
        print(f"{BOLD}What would you like to do next?{RESET}")
        print(f"  {CYAN}{BOLD}1) 🚀 Start following NEXT {batch_size} accounts{RESET} [Press Enter]")
        print(f"  {YELLOW}2) 🛑 Stop and exit session{RESET}")

        ans = input(f"\nEnter choice [1/2, default 1]: ").strip()
        if ans == "2":
            break

        batch_num += 1

    # Grand Session Summary
    box_width = 62
    avg_speed = (total_session_followed / total_session_time * 60) if total_session_time > 0 else 0
    print(f"\n{CYAN}╭{'─' * box_width}╮{RESET}")
    print(f"{CYAN}│{BOLD}{'🏆 FINAL SESSION SUMMARY':^{box_width}}{RESET}{CYAN}│{RESET}")
    print(f"{CYAN}├{'─' * box_width}┤{RESET}")
    print(f"{CYAN}│{RESET}  ✓ {BOLD}Total Accounts Followed:{RESET} {total_session_followed} accounts{' ' * (box_width - len(str(total_session_followed)) - 33)}{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  ⏱️  {BOLD}Total Time Elapsed:{RESET}      {format_duration(total_session_time)}{' ' * (box_width - len(format_duration(total_session_time)) - 33)}{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  ⚡ {BOLD}Average Speed:{RESET}           {avg_speed:.1f} follows/min{' ' * (box_width - len(f'{avg_speed:.1f}') - 33)}{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  💾 {BOLD}History Stored In:{RESET}       followed_history.json{' ' * (box_width - 43)}{CYAN}│{RESET}")
    print(f"{CYAN}╰{'─' * box_width}╯{RESET}\n")


def run_interactive(bot: GitHubBot):
    print(f"{BOLD}Choose Target Source:{RESET}")
    print("  1) Follow followers of a company or organization (e.g. google, microsoft, meta)")
    print("  2) Search active developers by keywords (e.g. location:Iraq, language:python)")
    print("  3) Follow contributors of a repository (e.g. facebook/react, flutter/flutter)")
    print("  4) Enter specific usernames manually")
    print("  5) Exit")

    choice = input("\nEnter choice [1-5]: ").strip()

    if choice == "1":
        target = input("\nEnter company or user account (e.g. google, microsoft): ").strip()
        cleaned = clean_input(target)
        bot.delay = ask_speed()
        run_continuous_session(bot, mode="user", target_val=cleaned, batch_size=BATCH_SIZE)

    elif choice == "2":
        query = input("\nEnter search keywords (e.g. location:Iraq language:python): ").strip()
        bot.delay = ask_speed()
        run_continuous_session(bot, mode="search", target_val=query, batch_size=BATCH_SIZE)

    elif choice == "3":
        raw_repo = input("\nEnter repository (e.g. facebook/react): ").strip()
        cleaned_repo = clean_input(raw_repo)
        if "/" not in cleaned_repo:
            cleaned_repo = f"{cleaned_repo}/{cleaned_repo}"
        bot.delay = ask_speed()
        run_continuous_session(bot, mode="repo", target_val=cleaned_repo, batch_size=BATCH_SIZE)

    elif choice == "4":
        raw = input("\nEnter usernames (separated by commas): ").strip()
        bot.delay = ask_speed()
        run_continuous_session(bot, mode="list", target_val=raw, batch_size=BATCH_SIZE)

    else:
        print("Exited.")


def main():
    parser = argparse.ArgumentParser(description="GitHub Network Expander Pro")
    parser.add_argument("--user", help="Target company or user account (e.g. 'google', 'microsoft')")
    parser.add_argument("--search", help="Search query (e.g. 'location:Iraq')")
    parser.add_argument("--repo", help="Target repository (e.g. 'facebook/react') to follow contributors")
    parser.add_argument("--list", help="Comma-separated list of usernames")
    parser.add_argument("--limit", type=int, default=BATCH_SIZE, help=f"Batch size (default: {BATCH_SIZE})")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help=f"Seconds between follows (default: {DEFAULT_DELAY})")
    parser.add_argument("--turbo", action="store_true", help="Run at max speed (0.5s delay)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making actual follow requests")

    args = parser.parse_args()

    delay = 0.5 if args.turbo else args.delay

    token = get_token()
    bot = GitHubBot(token, dry_run=args.dry_run, delay=delay)

    user_info = bot.verify_account()
    if not user_info:
        print(f"{RED}[!] Authentication failed. Check your token in {ENV_PATH}.{RESET}")
        sys.exit(1)

    # Sync following list
    bot.preload_current_following()

    if args.user:
        run_continuous_session(bot, mode="user", target_val=clean_input(args.user), batch_size=args.limit)
    elif args.search:
        run_continuous_session(bot, mode="search", target_val=args.search, batch_size=args.limit)
    elif args.repo:
        cleaned_repo = clean_input(args.repo)
        if "/" not in cleaned_repo:
            cleaned_repo = f"{cleaned_repo}/{cleaned_repo}"
        run_continuous_session(bot, mode="repo", target_val=cleaned_repo, batch_size=args.limit)
    elif args.list:
        run_continuous_session(bot, mode="list", target_val=args.list, batch_size=args.limit)
    else:
        run_interactive(bot)


if __name__ == "__main__":
    main()
