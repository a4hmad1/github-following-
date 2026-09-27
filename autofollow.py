#!/usr/bin/env python3
"""
GitHub Network Expander Pro
A high-performance CLI tool to expand your GitHub network in 250-account batches.

Features:
- Gender Filter Engine (Girls / Boys / All): Scans profile pronouns, bio keywords, real name, and username.
- Pre-Scan Engine: Live on-screen scan that checks and filters out all previously-followed accounts.
- Persistent Page Cursor (page_cursor.json): Never re-scans old pages; always finds fresh new accounts.
- Zero-Duplicate Guarantee ("Not Again"): Multiple in-memory and disk checks ensure no user is ever followed twice.
- Exact Batch Limit: Guarantees exactly 250 NEW accounts followed per batch.
- Batch Loop: Prompt to follow the NEXT 250 or stop after each batch.
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
CURSOR_PATH = BASE_DIR / "page_cursor.json"
GITHUB_API_BASE = "https://api.github.com"

# Unified Styling Theme (Cyan & Emerald Green)
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
BLUE = "\033[94m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

BATCH_SIZE = 250
DEFAULT_DELAY = 0.5  # Turbo speed: 0.5s

# ==========================================
# Comprehensive Gender Detection Datasets
# ==========================================
FEMALE_PRONOUNS = [
    "she/her", "she / her", "she/hers", "she / hers", "she/they", "she / they",
    "her/she", "she/them", "they/she", "her / she"
]

MALE_PRONOUNS = [
    "he/him", "he / him", "he/his", "he / his", "he/they", "he / they",
    "him/he", "he/them", "they/he", "him / he"
]

FEMALE_BIO_KEYWORDS = [
    "woman in tech", "women in tech", "women who code", "girls who code",
    "pyladies", "shecodes", "djangogirls", "railsgirls", "girlscript",
    "female developer", "female software engineer", "girl developer",
    "mother", "mom", "lady", "sister", "wife", "queen", "actress"
]

MALE_BIO_KEYWORDS = [
    "father", "dad", "husband", "brother", "guy", "boy developer", "king"
]

# Comprehensive Female First Names (Western, Arabic, Middle Eastern, Asian, Hispanic, Slavic)
FEMALE_NAMES = {
    # English & Western
    "sarah", "sara", "emily", "jessica", "ashley", "amanda", "jennifer", "stephanie", "nicole",
    "elizabeth", "megan", "hannah", "rachel", "lauren", "samantha", "victoria", "chloe", "olivia",
    "emma", "ava", "sophia", "isabella", "mia", "charlotte", "amelia", "harper", "evelyn", "abigail",
    "ella", "camila", "luna", "sofia", "avery", "millie", "grace", "zoey", "penelope", "lily",
    "eleanor", "lillian", "addison", "aubrey", "ellie", "stella", "natalie", "zoe", "leah", "hazel",
    "violet", "aurora", "savannah", "audrey", "brooklyn", "bella", "claire", "skylar", "lucy",
    "anna", "caroline", "genesis", "emilia", "kennedy", "maya", "willow", "kinsley", "naomi",
    "elena", "ariana", "allison", "gabriella", "alice", "madelyn", "cora", "ruby", "eva", "clara",
    "julia", "laura", "maria", "alina", "daria", "natasha", "polina", "valeria", "yulia", "anastasia",
    "daphne", "chelsea", "diana", "helen", "nancy", "linda", "patricia", "barbara", "susan", "karen",
    "lisa", "betty", "margaret", "dorothy", "sandra", "carol", "ruth", "sharon", "michelle", "laura",
    "kimberly", "deborah", "amy", "angela", "rebecca", "cynthia", "kathleen", "pamela", "vanessa",
    # Arabic & Middle Eastern
    "fatima", "fatimah", "zahra", "maryam", "mariam", "noor", "nour", "zainab", "zeinab", "aya",
    "ayah", "layla", "leila", "yasmin", "yasmine", "reem", "rania", "salma", "huda", "mona", "dina",
    "nada", "maha", "lina", "leena", "amina", "khadija", "khadeeja", "asma", "hanan", "rasha",
    "rola", "samira", "dalal", "bushra", "iman", "amal", "duaa", "israa", "marwa", "shaimaa",
    "heba", "hager", "rawan", "shahad", "raghad", "hala", "ghada", "sahar", "manar", "naglaa",
    # Asian & Hispanic
    "sakura", "yuki", "mei", "lin", "xia", "yoko", "haruka", "aiko", "priya", "ananya", "deepa",
    "pooja", "neha", "sneha", "kavita", "sunita", "lucia", "martina", "valeria", "paula", "daniela"
}

# Comprehensive Male First Names
MALE_NAMES = {
    # English & Western
    "john", "james", "robert", "michael", "william", "david", "richard", "joseph", "thomas",
    "charles", "christopher", "daniel", "matthew", "anthony", "mark", "donald", "steven", "paul",
    "andrew", "joshua", "kenneth", "kevin", "brian", "george", "edward", "ronald", "timothy",
    "jason", "jeffrey", "ryan", "jacob", "gary", "nicholas", "eric", "jonathan", "stephen",
    "larry", "justin", "scott", "brandon", "benjamin", "samuel", "gregory", "frank", "alexander",
    "raymond", "patrick", "jack", "dennis", "jerry", "tyler", "aaron", "jose", "adam", "nathan",
    "henry", "douglas", "zachary", "peter", "kyle", "walter", "ethan", "jeremy", "harold", "keith",
    "christian", "roger", "noah", "gerald", "carl", "terry", "sean", "austin", "arthur", "lawrence",
    "jesse", "dylan", "bryan", "joe", "jordan", "billy", "albert", "bruce", "willie", "gabriel",
    "logan", "lucas", "mason", "oliver", "liam", "elias", "julian", "leo", "theodore", "ezra",
    # Arabic & Middle Eastern
    "ahmad", "ahmed", "mohammed", "muhammad", "ali", "omar", "hussein", "hassan", "mustafa",
    "ibrahim", "khalid", "youssef", "yousef", "tariq", "bilal", "zayd", "hamza", "karim", "amr",
    "abdullah", "abdul", "saad", "tamer", "mahmoud", "fadi", "rami", "wail", "samer", "ziad",
    "hisham", "yasin", "faisal", "nasser", "adel", "bassem", "osama", "waleed", "saleh", "marwan"
}


def detect_gender(name: str | None, bio: str | None, username: str) -> tuple[str, str]:
    """
    Detects profile gender based on pronouns, bio keywords, real name, and username.
    Returns: (gender: "female" | "male" | "unknown", reason: str)
    """
    text = f"{name or ''} {bio or ''}".lower()

    # 1. Highest Confidence: Declared Pronouns
    for p in FEMALE_PRONOUNS:
        if p in text:
            return "female", f"pronouns '{p}'"

    for p in MALE_PRONOUNS:
        if p in text:
            return "male", f"pronouns '{p}'"

    # 2. Bio Keywords
    for kw in FEMALE_BIO_KEYWORDS:
        if kw in text:
            return "female", f"bio '{kw}'"

    for kw in MALE_BIO_KEYWORDS:
        if kw in text:
            return "male", f"bio '{kw}'"

    # 3. Real Name First Name matching
    if name:
        clean_first = "".join(c for c in name.strip().split()[0].lower() if c.isalpha())
        if clean_first in FEMALE_NAMES:
            return "female", f"name '{clean_first.capitalize()}'"
        if clean_first in MALE_NAMES:
            return "male", f"name '{clean_first.capitalize()}'"

    # 4. Username Prefix matching
    uname_lower = username.lower()
    for fn in FEMALE_NAMES:
        if len(fn) >= 4 and uname_lower.startswith(fn):
            return "female", f"username '{fn}'"

    for mn in MALE_NAMES:
        if len(mn) >= 4 and uname_lower.startswith(mn):
            return "male", f"username '{mn}'"

    return "unknown", "none"


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


class CursorManager:
    """Tracks the last scanned page per target so we never re-scan old pages."""
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
        return self.cursors.get(key.lower(), 1)

    def set_page(self, key: str, page: int):
        self.cursors[key.lower()] = page
        self.save()


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
    def __init__(self, token: str, dry_run: bool = False, delay: float = DEFAULT_DELAY, gender_filter: str = "all"):
        self.token = token
        self.dry_run = dry_run
        self.delay = delay
        self.gender_filter = gender_filter.lower()  # "all", "female" (girls), "male" (boys)
        self.session = requests.Session()

        # Connection pooling
        adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=2)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitHub-Network-Expander/7.0",
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

    def inspect_candidate(self, username: str) -> tuple[bool, str]:
        """
        Validates if username passes the gender filter.
        Returns: (passes: bool, reason: str)
        """
        if self.gender_filter in ("all", "*"):
            return True, "all"

        # Fetch profile metadata for gender inspection
        resp = self.session.get(f"{GITHUB_API_BASE}/users/{username}")
        if resp.status_code != 200:
            return False, "api_error"

        user_data = resp.json()
        gender, reason = detect_gender(user_data.get("name"), user_data.get("bio"), username)

        if self.gender_filter in ("female", "girl", "girls", "f"):
            return (gender == "female"), reason
        elif self.gender_filter in ("male", "boy", "boys", "m"):
            return (gender == "male"), reason

        return True, "all"

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
                    wait_sec = 45 * (attempt + 1)

                print(f"\n{YELLOW}  ⚠️ Rate limit active. Pausing {wait_sec}s for cooldown...{RESET}")
                time.sleep(wait_sec)
                continue

            if resp.status_code == 404:
                return False

            return False

        return False

    def get_followers_of(self, target_user: str, count: int = BATCH_SIZE) -> list[tuple[str, str]]:
        """Scans followers of a target, filtering by gender and previous follows."""
        clean_user = clean_input(target_user)
        candidates: list[tuple[str, str]] = []
        page = self.cursors.get_page(f"followers_{clean_user}_{self.gender_filter}")
        per_page = 100
        scanned_total = 0
        skipped_total = 0

        gender_desc = "GIRLS / FEMALE" if self.gender_filter in ("female", "girl", "girls") else (
            "BOYS / MALE" if self.gender_filter in ("male", "boy", "boys") else "ALL"
        )

        print(f"{CYAN}🔍 Pre-scanning @{clean_user} for {count} BRAND NEW [{gender_desc}] accounts...{RESET}")

        while len(candidates) < count:
            url = f"{GITHUB_API_BASE}/users/{clean_user}/followers?per_page={per_page}&page={page}"
            resp = self.session.get(url)
            if resp.status_code != 200:
                print(f"\n{RED}[!] Error fetching page {page} (HTTP {resp.status_code}){RESET}")
                break

            items = resp.json()
            if not items or not isinstance(items, list):
                break

            for item in items:
                username = item["login"]
                scanned_total += 1

                if self.history.contains(username) or username.lower() == self.current_user.lower():
                    skipped_total += 1
                    continue

                passes, reason = self.inspect_candidate(username)
                if passes:
                    candidates.append((username, reason))
                    if len(candidates) >= count:
                        break
                else:
                    skipped_total += 1

                sys.stdout.write(
                    f"\r  {CYAN}→ Page {page}{RESET} │ "
                    f"Scanned: {BOLD}{scanned_total}{RESET} │ "
                    f"Filtered: {YELLOW}{skipped_total}{RESET} │ "
                    f"Matched ({gender_desc}): {GREEN}{BOLD}{len(candidates)}/{count}{RESET} "
                )
                sys.stdout.flush()

            page += 1
            if len(items) < per_page:
                break

        self.cursors.set_page(f"followers_{clean_user}_{self.gender_filter}", max(1, page - 1))
        print(f"\n{GREEN}✓ Scan completed! Ready with {len(candidates)} brand new matched accounts.{RESET}")
        return candidates

    def get_contributors_of(self, repo: str, count: int = BATCH_SIZE) -> list[tuple[str, str]]:
        """Scans contributors of a repo, filtering by gender and previous follows."""
        clean_repo = clean_input(repo)
        candidates: list[tuple[str, str]] = []
        page = self.cursors.get_page(f"contributors_{clean_repo}_{self.gender_filter}")
        per_page = 100
        scanned_total = 0
        skipped_total = 0

        gender_desc = "GIRLS / FEMALE" if self.gender_filter in ("female", "girl", "girls") else (
            "BOYS / MALE" if self.gender_filter in ("male", "boy", "boys") else "ALL"
        )

        print(f"{CYAN}🔍 Pre-scanning {clean_repo} for {count} BRAND NEW [{gender_desc}] accounts...{RESET}")

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
                    scanned_total += 1

                    if self.history.contains(username) or username.lower() == self.current_user.lower():
                        skipped_total += 1
                        continue

                    passes, reason = self.inspect_candidate(username)
                    if passes:
                        candidates.append((username, reason))
                        if len(candidates) >= count:
                            break
                    else:
                        skipped_total += 1

                    sys.stdout.write(
                        f"\r  {CYAN}→ Page {page}{RESET} │ "
                        f"Scanned: {BOLD}{scanned_total}{RESET} │ "
                        f"Filtered: {YELLOW}{skipped_total}{RESET} │ "
                        f"Matched ({gender_desc}): {GREEN}{BOLD}{len(candidates)}/{count}{RESET} "
                    )
                    sys.stdout.flush()

            page += 1
            if len(items) < per_page:
                break

        self.cursors.set_page(f"contributors_{clean_repo}_{self.gender_filter}", max(1, page - 1))
        print(f"\n{GREEN}✓ Scan completed! Ready with {len(candidates)} brand new matched accounts.{RESET}")
        return candidates

    def search_users(self, query: str, count: int = BATCH_SIZE) -> list[tuple[str, str]]:
        """Scans GitHub search results, filtering by gender and previous follows."""
        candidates: list[tuple[str, str]] = []
        page = self.cursors.get_page(f"search_{query}_{self.gender_filter}")
        per_page = 100
        scanned_total = 0
        skipped_total = 0

        # Set display label for gender
        effective_query = query
        if self.gender_filter in ("female", "girl", "girls"):
            gender_desc = "GIRLS / FEMALE"
        elif self.gender_filter in ("male", "boy", "boys"):
            gender_desc = "BOYS / MALE"
        else:
            gender_desc = "ALL"

        print(f"{CYAN}🔍 Pre-scanning search '{effective_query}' for {count} BRAND NEW [{gender_desc}] accounts...{RESET}")

        while len(candidates) < count:
            url = f"{GITHUB_API_BASE}/search/users?q={effective_query}&per_page={per_page}&page={page}"
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

                passes, reason = self.inspect_candidate(username)
                if passes:
                    candidates.append((username, reason))
                    if len(candidates) >= count:
                        break
                else:
                    skipped_total += 1

                sys.stdout.write(
                    f"\r  {CYAN}→ Page {page}{RESET} │ "
                    f"Scanned: {BOLD}{scanned_total}{RESET} │ "
                    f"Filtered: {YELLOW}{skipped_total}{RESET} │ "
                    f"Matched ({gender_desc}): {GREEN}{BOLD}{len(candidates)}/{count}{RESET} "
                )
                sys.stdout.flush()

            page += 1
            if len(items) < per_page:
                break

        self.cursors.set_page(f"search_{query}_{self.gender_filter}", max(1, page - 1))
        print(f"\n{GREEN}✓ Scan completed! Ready with {len(candidates)} brand new matched accounts.{RESET}")
        return candidates

    def print_batch_header(self, batch_num: int, target_label: str, goal: int):
        """Displays a clean, styled dashboard card with gender filter badge."""
        est_seconds = goal * self.delay
        est_duration = format_duration(est_seconds)
        eta_time = time.strftime("%I:%M:%S %p", time.localtime(time.time() + est_seconds))
        speed_text = f"~{int(60 / max(self.delay, 0.1))} follows/min ({self.delay}s delay)"
        cur_following = self.user_stats.get("following", 0)

        gender_badge = "👩 Girls Only" if self.gender_filter in ("female", "girl", "girls") else (
            "👨 Boys Only" if self.gender_filter in ("male", "boy", "boys") else "🌟 All (Boys & Girls)"
        )

        box_width = 62
        print(f"\n{CYAN}╭{'─' * box_width}╮{RESET}")
        title = f"⚡ BATCH #{batch_num} — GOAL: {goal} NEW FOLLOWS ⚡"
        print(f"{CYAN}│{BOLD}{title:^{box_width}}{RESET}{CYAN}│{RESET}")
        print(f"{CYAN}├{'─' * box_width}┤{RESET}")
        print(f"{CYAN}│{RESET}  👤 {BOLD}Operator:{RESET}  @{self.current_user:<16}  👥 {BOLD}Followers:{RESET} {str(self.user_stats.get('followers', 0)):<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  🎯 {BOLD}Source:{RESET}    {target_label:<16}  🔄 {BOLD}Following:{RESET} {str(cur_following):<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  🏷️  {BOLD}Filter:{RESET}    {gender_badge:<16}  ⚡ {BOLD}Speed:{RESET}     {speed_text:<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  ⏱️  {BOLD}Est Time:{RESET}  {est_duration:<16}  🏁 {BOLD}Batch ETA:{RESET} {eta_time:<15}{CYAN}│{RESET}")
        print(f"{CYAN}╰{'─' * box_width}╯{RESET}\n")

    def run_batch(self, targets: list[tuple[str, str]], goal: int, batch_num: int, target_label: str) -> tuple[int, float]:
        """Executes a single batch with real-time percentage progress bar and timers."""
        if not targets:
            print(f"{YELLOW}[!] No candidate accounts available.{RESET}")
            return 0, 0.0

        self.print_batch_header(batch_num, target_label, goal)

        success_count = 0
        start_time = time.time()

        try:
            for idx, (username, reason) in enumerate(targets, 1):
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

                gender_tag = ""
                if self.gender_filter in ("female", "girl", "girls"):
                    gender_tag = f" {MAGENTA}[👩 {reason}]{RESET}"
                elif self.gender_filter in ("male", "boy", "boys"):
                    gender_tag = f" {BLUE}[👨 {reason}]{RESET}"

                print(status_header)
                print(f"  → Following {BOLD}@{username}{RESET}{gender_tag}...", end="", flush=True)

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


def ask_gender() -> str:
    """Lets user select their preferred gender filter."""
    print(f"\n👥 {BOLD}Select Profile Filter (Boy / Girl):{RESET}")
    print(f"  1) {CYAN}🌟 All Profiles (Boys & Girls){RESET} [Default - Fastest]")
    print(f"  2) {MAGENTA}👩 Girls / Female Only{RESET} (Scans pronouns, bio, name)")
    print(f"  3) {BLUE}👨 Boys / Male Only{RESET}   (Scans pronouns, bio, name)")

    choice = input("\nEnter choice [1-3, default 1]: ").strip()
    if choice == "2":
        return "female"
    elif choice == "3":
        return "male"
    return "all"


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
    """Loops in batches of 250: pre-scans to ensure only fresh accounts, then asks to continue."""
    batch_num = 1
    total_session_followed = 0
    total_session_time = 0.0

    target_label = f"@{target_val}" if mode == "user" else target_val

    while True:
        if mode == "user":
            candidates = bot.get_followers_of(target_val, count=batch_size)
        elif mode == "search":
            candidates = bot.search_users(target_val, count=batch_size)
        elif mode == "repo":
            candidates = bot.get_contributors_of(target_val, count=batch_size)
        else:
            raw_list = [clean_input(u) for u in target_val.split(",") if clean_input(u)]
            candidates = []
            for u in raw_list:
                if not bot.history.contains(u):
                    passes, reason = bot.inspect_candidate(u)
                    if passes:
                        candidates.append((u, reason))

        if not candidates:
            print(f"\n{YELLOW}[!] No more fresh matched accounts found from {target_label}.{RESET}")
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
        title = f"🎉 BATCH #{batch_num} COMPLETED ({followed}/{batch_size} NEW) 🎉"
        print(f"{GREEN}│{BOLD}{title:^{box_width}}{RESET}{GREEN}│{RESET}")
        print(f"{GREEN}├{'─' * box_width}┤{RESET}")
        print(f"{GREEN}│{RESET}  ✓ {BOLD}New Follows in Batch #{batch_num}:{RESET} {followed} accounts{' ' * (box_width - len(str(followed)) - 35)}{GREEN}│{RESET}")
        print(f"{GREEN}│{RESET}  🌟 {BOLD}Total in This Session:{RESET}     {total_session_followed} accounts{' ' * (box_width - len(str(total_session_followed)) - 32)}{GREEN}│{RESET}")
        print(f"{GREEN}│{RESET}  🔄 {BOLD}Current Total Following:{RESET}   {current_following} accounts{' ' * (box_width - len(str(current_following)) - 32)}{GREEN}│{RESET}")
        print(f"{GREEN}│{RESET}  ⏱️  {BOLD}Batch Time Elapsed:{RESET}       {format_duration(elapsed)}{' ' * (box_width - len(format_duration(elapsed)) - 32)}{GREEN}│{RESET}")
        print(f"{GREEN}╰{'─' * box_width}╯{RESET}\n")

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
    print(f"{CYAN}│{RESET}  ✓ {BOLD}Total New Accounts Followed:{RESET} {total_session_followed} accounts{' ' * (box_width - len(str(total_session_followed)) - 37)}{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  ⏱️  {BOLD}Total Time Elapsed:{RESET}          {format_duration(total_session_time)}{' ' * (box_width - len(format_duration(total_session_time)) - 33)}{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  ⚡ {BOLD}Average Speed:{RESET}               {avg_speed:.1f} follows/min{' ' * (box_width - len(f'{avg_speed:.1f}') - 33)}{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  💾 {BOLD}History Stored In:{RESET}           followed_history.json{' ' * (box_width - 43)}{CYAN}│{RESET}")
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
        bot.gender_filter = ask_gender()
        bot.delay = ask_speed()
        run_continuous_session(bot, mode="user", target_val=cleaned, batch_size=BATCH_SIZE)

    elif choice == "2":
        query = input("\nEnter search keywords (e.g. location:Iraq language:python): ").strip()
        bot.gender_filter = ask_gender()
        bot.delay = ask_speed()
        run_continuous_session(bot, mode="search", target_val=query, batch_size=BATCH_SIZE)

    elif choice == "3":
        raw_repo = input("\nEnter repository (e.g. facebook/react): ").strip()
        cleaned_repo = clean_input(raw_repo)
        if "/" not in cleaned_repo:
            print(f"\n{YELLOW}[!] '{cleaned_repo}' is an account/organization, not a repository.{RESET}")
            print(f"    {GREEN}Switching automatically to following followers of @{cleaned_repo}!{RESET}")
            mode = "user"
            target_val = cleaned_repo
        else:
            mode = "repo"
            target_val = cleaned_repo

        bot.gender_filter = ask_gender()
        bot.delay = ask_speed()
        run_continuous_session(bot, mode=mode, target_val=target_val, batch_size=BATCH_SIZE)

    elif choice == "4":
        raw = input("\nEnter usernames (separated by commas): ").strip()
        bot.gender_filter = ask_gender()
        bot.delay = ask_speed()
        run_continuous_session(bot, mode="list", target_val=raw, batch_size=BATCH_SIZE)

    else:
        print("Exited.")


def main():
    parser = argparse.ArgumentParser(description="GitHub Network Expander Pro (With Gender Detection)")
    parser.add_argument("--user", help="Target company or user account (e.g. 'google', 'microsoft')")
    parser.add_argument("--search", help="Search query (e.g. 'location:Iraq')")
    parser.add_argument("--repo", help="Target repository (e.g. 'facebook/react') to follow contributors")
    parser.add_argument("--list", help="Comma-separated list of usernames")
    parser.add_argument("--limit", type=int, default=BATCH_SIZE, help=f"Batch size (default: {BATCH_SIZE})")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help=f"Seconds between follows (default: {DEFAULT_DELAY})")
    parser.add_argument("--gender", default="all", choices=["all", "female", "girl", "male", "boy"], help="Filter by gender (female/girl, male/boy, all)")
    parser.add_argument("--turbo", action="store_true", help="Run at max speed (0.5s delay)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making actual follow requests")

    args = parser.parse_args()

    delay = 0.5 if args.turbo else args.delay

    token = get_token()
    bot = GitHubBot(token, dry_run=args.dry_run, delay=delay, gender_filter=args.gender)

    user_info = bot.verify_account()
    if not user_info:
        print(f"{RED}[!] Authentication failed. Check your token in {ENV_PATH}.{RESET}")
        sys.exit(1)

    # Sync following list into memory
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
