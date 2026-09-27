#!/usr/bin/env python3
"""
GitHub Auto-Follow Tool (High Performance Edition)
Optimized with in-memory preloading, connection pooling, and sub-second delay modes.
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

# Terminal Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"

DEFAULT_LIMIT = 100000
DEFAULT_DELAY = 1.0  # Fast default: 1 second between follows


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
        self._dirty = False
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
            self._dirty = False
        except Exception as e:
            print(f"{YELLOW}[!] Failed to save history: {e}{RESET}")

    def add(self, username: str, auto_save: bool = True):
        self.history.add(username.lower())
        if auto_save:
            self.save()
        else:
            self._dirty = True

    def contains(self, username: str) -> bool:
        return username.lower() in self.history


class GitHubBot:
    def __init__(self, token: str, dry_run: bool = False, delay: float = DEFAULT_DELAY):
        self.token = token
        self.dry_run = dry_run
        self.delay = delay
        self.session = requests.Session()

        # High-performance HTTP connection pooling (reuses TLS sessions)
        adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=2)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitHub-AutoFollow-Fast/3.0",
        })
        self.current_user = ""
        self.history = HistoryManager(HISTORY_PATH)

    def verify_account(self) -> dict | None:
        """Verifies token and retrieves account information."""
        resp = self.session.get(f"{GITHUB_API_BASE}/user")
        if resp.status_code == 200:
            data = resp.json()
            self.current_user = data.get("login", "")
            return data
        return None

    def preload_current_following(self):
        """Preloads all users that current_user already follows into memory in bulk."""
        print(f"{CYAN}[*] Fast-syncing your existing following list...{RESET}", end="", flush=True)
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
        print(f" {GREEN}Done ({count} accounts synced to cache).{RESET}")

    def follow(self, username: str) -> bool:
        """Sends PUT request to follow a GitHub user directly with auto-backoff."""
        if self.dry_run:
            print(f"{YELLOW}[DRY-RUN]{RESET} Would follow @{username}")
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

                print(f"\n{YELLOW}[!] Rate limit pause. Waiting {wait_sec}s before continuing...{RESET}")
                time.sleep(wait_sec)
                continue

            if resp.status_code == 404:
                print(f"{YELLOW}[!] User @{username} not found.{RESET}")
                return False

            print(f"{RED}[!] Error following @{username}: HTTP {resp.status_code} - {resp.text}{RESET}")
            return False

        return False

    def get_followers_of(self, target_user: str, limit: int = DEFAULT_LIMIT) -> list[str]:
        """Fetch all followers of a given user or organization using fast pagination."""
        clean_user = clean_input(target_user)
        users = []
        page = 1
        per_page = 100

        print(f"{CYAN}[*] Fetching followers for @{clean_user}...{RESET}")
        while len(users) < limit:
            url = f"{GITHUB_API_BASE}/users/{clean_user}/followers?per_page={per_page}&page={page}"
            resp = self.session.get(url)
            if resp.status_code != 200:
                print(f"\n{RED}[!] Failed to fetch followers for @{clean_user} (HTTP {resp.status_code}): {resp.text}{RESET}")
                break

            items = resp.json()
            if not items or not isinstance(items, list):
                break

            for item in items:
                users.append(item["login"])
                if len(users) >= limit:
                    break

            print(f"\r  → Collected {len(users)} users (Page {page})...", end="", flush=True)

            if len(items) < per_page:
                break

            page += 1

        print(f"\n{GREEN}[✓] Total candidates collected: {len(users)}{RESET}")
        return users

    def get_contributors_of(self, repo: str, limit: int = DEFAULT_LIMIT) -> list[str]:
        """Fetch contributors of an owner/repo."""
        clean_repo = clean_input(repo)
        users = []
        page = 1
        per_page = 100

        print(f"{CYAN}[*] Fetching contributors for {clean_repo}...{RESET}")
        while len(users) < limit:
            url = f"{GITHUB_API_BASE}/repos/{clean_repo}/contributors?per_page={per_page}&page={page}"
            resp = self.session.get(url)
            if resp.status_code != 200:
                print(f"\n{RED}[!] Failed to fetch contributors for {clean_repo} (HTTP {resp.status_code}): {resp.text}{RESET}")
                break

            items = resp.json()
            if not items or not isinstance(items, list):
                break

            for item in items:
                if "login" in item:
                    users.append(item["login"])
                    if len(users) >= limit:
                        break

            print(f"\r  → Collected {len(users)} contributors (Page {page})...", end="", flush=True)

            if len(items) < per_page:
                break

            page += 1

        print(f"\n{GREEN}[✓] Total contributors collected: {len(users)}{RESET}")
        return users

    def search_users(self, query: str, limit: int = DEFAULT_LIMIT) -> list[str]:
        """Search GitHub users matching a query."""
        users = []
        page = 1
        per_page = 100

        print(f"{CYAN}[*] Searching users for '{query}'...{RESET}")
        while len(users) < limit:
            url = f"{GITHUB_API_BASE}/search/users?q={query}&per_page={per_page}&page={page}"
            resp = self.session.get(url)
            if resp.status_code != 200:
                print(f"\n{RED}[!] Search error: HTTP {resp.status_code} - {resp.text}{RESET}")
                break

            data = resp.json()
            items = data.get("items", [])
            if not items:
                break

            for item in items:
                users.append(item["login"])
                if len(users) >= limit:
                    break

            print(f"\r  → Collected {len(users)} users (Page {page})...", end="", flush=True)

            if len(items) < per_page:
                break

            page += 1

        print(f"\n{GREEN}[✓] Total search results collected: {len(users)}{RESET}")
        return users

    def process_targets(self, targets: list[str]):
        """Iterates over candidates at high speed and executes follows."""
        if not targets:
            print(f"{YELLOW}[!] No targets to process.{RESET}")
            return

        total = len(targets)
        est_seconds = int(total * self.delay)
        hours = est_seconds // 3600
        mins = (est_seconds % 3600) // 60

        print(f"\n{CYAN}{BOLD}Starting fast follow process for {total} candidate(s)...{RESET}")
        print(f"{GREEN}⚡ Speed: ~{int(60 / max(self.delay, 0.1))} follows/min (delay: {self.delay}s){RESET}")
        if hours > 0:
            print(f"{YELLOW}Estimated completion: ~{hours}h {mins}m | Stop anytime with Ctrl+C to save!{RESET}\n")

        success_count = 0
        skipped_count = 0
        start_time = time.time()

        try:
            for idx, username in enumerate(targets, 1):
                pct = (idx / total) * 100

                if username.lower() == self.current_user.lower():
                    continue

                # Instant in-memory check (0 HTTP requests!)
                if self.history.contains(username):
                    print(f"[{idx}/{total}] ({pct:.1f}%) {YELLOW}↷ Skipping @{username} (already followed){RESET}")
                    skipped_count += 1
                    continue

                print(f"[{idx}/{total}] ({pct:.1f}%) {CYAN}→ Following @{username}...{RESET}", end=" ", flush=True)
                if self.follow(username):
                    print(f"{GREEN}✓ Followed!{RESET}")
                    success_count += 1
                else:
                    print(f"{RED}✗ Failed{RESET}")

                # Fast delay
                if idx < total and self.delay > 0:
                    time.sleep(self.delay)

        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}[!] Paused by user (Ctrl+C).{RESET}")
            print(f"{GREEN}[✓] Progress saved in followed_history.json! Rerun anytime to continue.{RESET}")

        elapsed = time.time() - start_time
        rate = (success_count / elapsed * 60) if elapsed > 0 else 0
        print(f"\n{BOLD}Session Summary:{RESET} {GREEN}{success_count} followed{RESET}, {YELLOW}{skipped_count} skipped ({rate:.1f} follows/min)")


def ask_limit(default_limit: int = DEFAULT_LIMIT) -> int:
    """Asks for limit, defaulting to 100,000 (all)."""
    lim_str = input(f"Limit (default {default_limit} / all): ").strip()
    if not lim_str:
        return default_limit
    try:
        limit = int(lim_str)
        return limit if limit > 0 else default_limit
    except ValueError:
        return default_limit


def ask_speed() -> float:
    """Lets user select their preferred speed mode."""
    print(f"\n{BOLD}Select Speed Mode:{RESET}")
    print(f"  1) {GREEN}⚡ Fast{RESET} (1.0s delay - ~60 follows/min) [Recommended]")
    print(f"  2) {CYAN}🚀 Turbo{RESET} (0.5s delay - ~120 follows/min - Max Speed)")
    print(f"  3) {YELLOW}🛡️ Safe{RESET} (2.5s delay - ~24 follows/min)")
    print(f"  4) Custom delay in seconds")

    choice = input("Enter choice [1-4, default 1]: ").strip()
    if choice == "2":
        return 0.5
    elif choice == "3":
        return 2.5
    elif choice == "4":
        custom = input("Enter delay in seconds (e.g. 0.8): ").strip()
        try:
            return max(float(custom), 0.1)
        except ValueError:
            return 1.0
    return 1.0


def run_interactive(bot: GitHubBot, default_limit: int):
    print(f"\n{BOLD}Choose target mode:{RESET}")
    print("  1) Follow followers of a user or organization (e.g. laravel, torvalds, octocat)")
    print("  2) Search users by keyword/location/language (e.g. location:Iraq, language:php)")
    print("  3) Follow contributors of a repository (e.g. laravel/laravel, laravel/framework)")
    print("  4) Enter specific usernames manually (comma separated)")
    print("  5) Exit")

    choice = input("\nEnter choice [1-5]: ").strip()

    if choice == "1":
        target = input("Enter target GitHub username or URL (e.g. laravel or https://github.com/laravel): ").strip()
        cleaned = clean_input(target)
        limit = ask_limit(default_limit)
        bot.delay = ask_speed()
        targets = bot.get_followers_of(cleaned, limit=limit)

    elif choice == "2":
        query = input("Enter search query (e.g. location:Iraq language:python): ").strip()
        limit = ask_limit(default_limit)
        bot.delay = ask_speed()
        targets = bot.search_users(query, limit=limit)

    elif choice == "3":
        raw_repo = input("Enter repository owner/repo or URL (e.g. laravel/laravel or https://github.com/laravel/laravel): ").strip()
        cleaned_repo = clean_input(raw_repo)

        if "/" not in cleaned_repo:
            print(f"\n{YELLOW}[!] '{cleaned_repo}' is an organization/user account, not a repository.{RESET}")
            print(f"  Options:")
            print(f"  a) Follow followers of @{cleaned_repo} instead")
            print(f"  b) Follow contributors of {cleaned_repo}/{cleaned_repo}")
            sub_choice = input("Select [a/b]: ").strip().lower()
            if sub_choice == "a":
                limit = ask_limit(default_limit)
                bot.delay = ask_speed()
                targets = bot.get_followers_of(cleaned_repo, limit=limit)
                bot.process_targets(targets)
                return
            else:
                cleaned_repo = f"{cleaned_repo}/{cleaned_repo}"

        limit = ask_limit(default_limit)
        bot.delay = ask_speed()
        targets = bot.get_contributors_of(cleaned_repo, limit=limit)

    elif choice == "4":
        raw = input("Enter usernames (separated by commas): ").strip()
        targets = [clean_input(u) for u in raw.split(",") if clean_input(u)]
        bot.delay = ask_speed()

    else:
        print("Cancelled.")
        return

    bot.process_targets(targets)


def main():
    parser = argparse.ArgumentParser(description="GitHub Auto Follow Tool (High Speed Edition)")
    parser.add_argument("--user", help="Target username or URL to follow their followers")
    parser.add_argument("--search", help="Search query (e.g. 'location:Iraq')")
    parser.add_argument("--repo", help="Target repository (e.g. 'laravel/laravel') to follow contributors")
    parser.add_argument("--list", help="Comma-separated list of usernames")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help=f"Max accounts to process (default: {DEFAULT_LIMIT})")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help=f"Seconds between follows (default: {DEFAULT_DELAY})")
    parser.add_argument("--turbo", action="store_true", help="Turbo mode: 0.5s delay (~120 follows/min)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making actual follow requests")

    args = parser.parse_args()

    delay = 0.5 if args.turbo else args.delay

    token = get_token()
    bot = GitHubBot(token, dry_run=args.dry_run, delay=delay)

    user_info = bot.verify_account()
    if not user_info:
        print(f"{RED}[!] Authentication failed. Check your token in {ENV_PATH}.{RESET}")
        sys.exit(1)

    print(f"{GREEN}{BOLD}✓ Authenticated as @{user_info.get('login')}{RESET}")
    print(f"  Followers: {user_info.get('followers')} | Following: {user_info.get('following')}\n")

    # Fast sync existing following list in bulk (eliminates redundant individual GET calls)
    bot.preload_current_following()

    targets = []
    if args.user:
        targets = bot.get_followers_of(clean_input(args.user), limit=args.limit)
    elif args.search:
        targets = bot.search_users(args.search, limit=args.limit)
    elif args.repo:
        cleaned_repo = clean_input(args.repo)
        if "/" not in cleaned_repo:
            cleaned_repo = f"{cleaned_repo}/{cleaned_repo}"
        targets = bot.get_contributors_of(cleaned_repo, limit=args.limit)
    elif args.list:
        targets = [clean_input(u) for u in args.list.split(",") if clean_input(u)]
    else:
        run_interactive(bot, default_limit=args.limit)
        return

    bot.process_targets(targets)


if __name__ == "__main__":
    main()
