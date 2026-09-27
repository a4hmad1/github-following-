#!/usr/bin/env python3
"""
GitHub Auto-Follow Tool (High Performance Edition)
Features:
- Beautiful UI dashboard with live progress bar and ETA clock
- Default limit of 250 following
- Accurate time remaining and elapsed time tracking
- In-memory pre-caching and HTTP connection pooling
- Auto-resume and secondary rate-limit protection
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

# Terminal Colors & Styling
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

DEFAULT_LIMIT = 250
DEFAULT_DELAY = 0.5  # Turbo speed: 0.5s


def format_duration(seconds: float) -> str:
    """Formats seconds into HH:MM:SS or MM:SS."""
    s = max(0, int(seconds))
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}h {m:02d}m {s:02d}s"
    return f"{m:02d}m {s:02d}s"


def render_progress_bar(current: int, total: int, width: int = 24) -> str:
    """Renders a modern Unicode progress bar."""
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
            "User-Agent": "GitHub-AutoFollow-Design/4.0",
        })
        self.current_user = ""
        self.user_stats = {}
        self.history = HistoryManager(HISTORY_PATH)

    def verify_account(self) -> dict | None:
        """Verifies token and retrieves account information."""
        resp = self.session.get(f"{GITHUB_API_BASE}/user")
        if resp.status_code == 200:
            self.user_stats = resp.json()
            self.current_user = self.user_stats.get("login", "")
            return self.user_stats
        return None

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

    def get_followers_of(self, target_user: str, limit: int = DEFAULT_LIMIT) -> list[str]:
        """Fetch fresh, unfollowed followers of a given user or organization."""
        clean_user = clean_input(target_user)
        candidates = []
        page = 1
        per_page = 100

        print(f"{CYAN}🔍 Collecting followers of @{clean_user}...{RESET}", end="", flush=True)
        while len(candidates) < limit:
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
                    if len(candidates) >= limit:
                        break
            if len(items) < per_page:
                break
            page += 1

        print(f" {GREEN}Found {len(candidates)} new accounts to follow.{RESET}")
        return candidates

    def get_contributors_of(self, repo: str, limit: int = DEFAULT_LIMIT) -> list[str]:
        """Fetch fresh contributors of an owner/repo."""
        clean_repo = clean_input(repo)
        candidates = []
        page = 1
        per_page = 100

        print(f"{CYAN}🔍 Collecting contributors of {clean_repo}...{RESET}", end="", flush=True)
        while len(candidates) < limit:
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
                        if len(candidates) >= limit:
                            break
            if len(items) < per_page:
                break
            page += 1

        print(f" {GREEN}Found {len(candidates)} new accounts to follow.{RESET}")
        return candidates

    def search_users(self, query: str, limit: int = DEFAULT_LIMIT) -> list[str]:
        """Search fresh GitHub users matching a query."""
        candidates = []
        page = 1
        per_page = 100

        print(f"{CYAN}🔍 Searching users for '{query}'...{RESET}", end="", flush=True)
        while len(candidates) < limit:
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
                    if len(candidates) >= limit:
                        break
            if len(items) < per_page:
                break
            page += 1

        print(f" {GREEN}Found {len(candidates)} new accounts to follow.{RESET}")
        return candidates

    def print_dashboard(self, target_label: str, target_limit: int):
        """Prints a beautiful dashboard card with ETA and time calculations."""
        est_seconds = target_limit * self.delay
        est_duration = format_duration(est_seconds)
        eta_time = time.strftime("%I:%M:%S %p", time.localtime(time.time() + est_seconds))
        speed_text = f"~{int(60 / max(self.delay, 0.1))} follows/min ({self.delay}s delay)"

        box_width = 62
        print(f"{CYAN}╭{'─' * box_width}╮{RESET}")
        print(f"{CYAN}│{BOLD}{'⚡ GITHUB AUTO-FOLLOWER PRO ⚡':^{box_width}}{RESET}{CYAN}│{RESET}")
        print(f"{CYAN}├{'─' * box_width}┤{RESET}")
        print(f"{CYAN}│{RESET}  👤 {BOLD}Account:{RESET} @{self.current_user:<16}  👥 {BOLD}Followers:{RESET} {str(self.user_stats.get('followers', 0)):<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  🎯 {BOLD}Target:{RESET}  {target_label:<16}  🔄 {BOLD}Following:{RESET} {str(self.user_stats.get('following', 0)):<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  🎯 {BOLD}Goal:{RESET}    {str(target_limit) + ' follows':<16}  ⚡ {BOLD}Speed:{RESET}     {speed_text:<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  ⏱️  {BOLD}Est Time:{RESET}{est_duration:<16}  🏁 {BOLD}ETA Time:{RESET}  {eta_time:<15}{CYAN}│{RESET}")
        print(f"{CYAN}╰{'─' * box_width}╯{RESET}\n")

    def process_targets(self, targets: list[str], target_limit: int = DEFAULT_LIMIT, target_label: str = "custom"):
        """Executes follows up to target_limit with real-time UI, progress bar, and timers."""
        if not targets:
            print(f"{YELLOW}[!] No candidates available to process.{RESET}")
            return

        self.print_dashboard(target_label, target_limit)

        success_count = 0
        skipped_count = 0
        start_time = time.time()

        try:
            for idx, username in enumerate(targets, 1):
                if success_count >= target_limit:
                    break

                if username.lower() == self.current_user.lower():
                    continue

                # Instant in-memory check (0 HTTP requests!)
                if self.history.contains(username):
                    skipped_count += 1
                    continue

                # Time calculations
                elapsed_sec = time.time() - start_time
                remaining_needed = target_limit - success_count
                rem_seconds = remaining_needed * self.delay
                eta_clock = time.strftime("%I:%M:%S %p", time.localtime(time.time() + rem_seconds))

                progress_bar = render_progress_bar(success_count, target_limit, width=18)
                elapsed_str = format_duration(elapsed_sec)
                rem_str = format_duration(rem_seconds)

                # Status Line: Progress bar + Counts + Remaining Time
                status_header = (
                    f"{progress_bar} {BOLD}{success_count}/{target_limit}{RESET} "
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

                print()  # Empty line for clean spacing

                # Delay between follows
                if success_count < target_limit and self.delay > 0:
                    time.sleep(self.delay)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}⚠️  Session paused by user (Ctrl+C).{RESET}")

        total_elapsed = time.time() - start_time
        avg_speed = (success_count / total_elapsed * 60) if total_elapsed > 0 else 0

        # Beautiful Session Summary Card
        box_width = 62
        print(f"\n{GREEN}╭{'─' * box_width}╮{RESET}")
        print(f"{GREEN}│{BOLD}{'🎉 SESSION SUMMARY':^{box_width}}{RESET}{GREEN}│{RESET}")
        print(f"{GREEN}├{'─' * box_width}┤{RESET}")
        print(f"{GREEN}│{RESET}  ✓ {BOLD}Successfully Followed:{RESET} {success_count} accounts{' ' * (box_width - len(str(success_count)) - 32)}{GREEN}│{RESET}")
        print(f"{GREEN}│{RESET}  ↷ {BOLD}Skipped (Already Followed):{RESET} {skipped_count} accounts{' ' * (box_width - len(str(skipped_count)) - 36)}{GREEN}│{RESET}")
        print(f"{GREEN}│{RESET}  ⏱️  {BOLD}Total Time Elapsed:{RESET} {format_duration(total_elapsed)}{' ' * (box_width - len(format_duration(total_elapsed)) - 29)}{GREEN}│{RESET}")
        print(f"{GREEN}│{RESET}  ⚡ {BOLD}Average Speed:{RESET} {avg_speed:.1f} follows/min{' ' * (box_width - len(f'{avg_speed:.1f}') - 31)}{GREEN}│{RESET}")
        print(f"{GREEN}│{RESET}  💾 {BOLD}Progress Saved To:{RESET} followed_history.json{' ' * (box_width - 48)}{GREEN}│{RESET}")
        print(f"{GREEN}╰{'─' * box_width}╯{RESET}\n")


def ask_limit(default_limit: int = DEFAULT_LIMIT) -> int:
    """Asks for limit, defaulting to 250."""
    print(f"\n🎯 {BOLD}Follow Target Limit:{RESET}")
    print(f"   Default is {GREEN}{BOLD}250{RESET} accounts.")
    lim_str = input(f"   Enter limit [Press Enter for {default_limit}]: ").strip()
    if not lim_str:
        return default_limit
    try:
        limit = int(lim_str)
        return limit if limit > 0 else default_limit
    except ValueError:
        return default_limit


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


def run_interactive(bot: GitHubBot, default_limit: int = DEFAULT_LIMIT):
    print(f"{BOLD}Choose Target Mode:{RESET}")
    print("  1) Follow followers of a user/organization (e.g. laravel, octocat)")
    print("  2) Search active developers (e.g. location:Iraq, language:php)")
    print("  3) Follow contributors of a repository (e.g. laravel/framework)")
    print("  4) Enter specific usernames manually")
    print("  5) Exit")

    choice = input("\nEnter choice [1-5]: ").strip()

    if choice == "1":
        target = input("\nEnter target GitHub username or URL (e.g. laravel): ").strip()
        cleaned = clean_input(target)
        limit = ask_limit(default_limit)
        bot.delay = ask_speed()
        targets = bot.get_followers_of(cleaned, limit=limit)
        bot.process_targets(targets, target_limit=limit, target_label=f"@{cleaned}")

    elif choice == "2":
        query = input("\nEnter search query (e.g. location:Iraq language:python): ").strip()
        limit = ask_limit(default_limit)
        bot.delay = ask_speed()
        targets = bot.search_users(query, limit=limit)
        bot.process_targets(targets, target_limit=limit, target_label=f"query:{query}")

    elif choice == "3":
        raw_repo = input("\nEnter repository (e.g. laravel/framework): ").strip()
        cleaned_repo = clean_input(raw_repo)
        if "/" not in cleaned_repo:
            cleaned_repo = f"{cleaned_repo}/{cleaned_repo}"
        limit = ask_limit(default_limit)
        bot.delay = ask_speed()
        targets = bot.get_contributors_of(cleaned_repo, limit=limit)
        bot.process_targets(targets, target_limit=limit, target_label=cleaned_repo)

    elif choice == "4":
        raw = input("\nEnter usernames (separated by commas): ").strip()
        targets = [clean_input(u) for u in raw.split(",") if clean_input(u)]
        bot.delay = ask_speed()
        bot.process_targets(targets, target_limit=len(targets), target_label="custom-list")

    else:
        print("Exited.")


def main():
    parser = argparse.ArgumentParser(description="GitHub Auto Follow Tool (Pro Design Edition)")
    parser.add_argument("--user", help="Target username or URL to follow their followers")
    parser.add_argument("--search", help="Search query (e.g. 'location:Iraq')")
    parser.add_argument("--repo", help="Target repository (e.g. 'laravel/laravel') to follow contributors")
    parser.add_argument("--list", help="Comma-separated list of usernames")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Max accounts to follow (default: {DEFAULT_LIMIT})")
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

    targets = []
    target_label = "targets"
    if args.user:
        target_label = f"@{clean_input(args.user)}"
        targets = bot.get_followers_of(clean_input(args.user), limit=args.limit)
    elif args.search:
        target_label = f"search:{args.search}"
        targets = bot.search_users(args.search, limit=args.limit)
    elif args.repo:
        cleaned_repo = clean_input(args.repo)
        if "/" not in cleaned_repo:
            cleaned_repo = f"{cleaned_repo}/{cleaned_repo}"
        target_label = cleaned_repo
        targets = bot.get_contributors_of(cleaned_repo, limit=args.limit)
    elif args.list:
        target_label = "custom-list"
        targets = [clean_input(u) for u in args.list.split(",") if clean_input(u)]
    else:
        run_interactive(bot, default_limit=args.limit)
        return

    bot.process_targets(targets, target_limit=args.limit, target_label=target_label)


if __name__ == "__main__":
    main()
