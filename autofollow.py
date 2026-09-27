#!/usr/bin/env python3
"""
☀️ Kurdish Developer Auto-Pilot Pro (Tech Roles & Gender Filter Edition)
Discovers and follows verified Kurdish developers (Fullstack, Backend, Software Engineers, Laravel, Seniors).

Features:
- Tech Role Filter: Verifies profiles are Software Engineers, Developers, Fullstack, Backend, Laravel, or Seniors.
- Gender Filter: Choose Kurdish Girls Only, Kurdish Boys Only, or All Developers.
- Anti-Ban 2-Hour Rest Break: Follows 50 devs, rests 2 hours to clear GitHub hourly limits, and repeats.
- Kurdish Search Vectors: Scans Erbil, Sulaymaniyah, Duhok, Kirkuk, Kurdistan, etc.
- Zero Duplicates ("Not Again"): Multiple in-memory and disk checks guarantee no user is ever followed twice.
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
FOLLOWS_LOG_PATH = BASE_DIR / "follows.log"
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

DEFAULT_BATCH_SIZE = 50       # 50 follows per session (safe under hourly limits)
DEFAULT_BREAK_HOURS = 2.0     # 2 hours break between batches
DEFAULT_DELAY = 1.0           # 1.0s delay between follows

# ==========================================
# Verified Tech Developer Role Keywords
# ==========================================
DEV_KEYWORDS = [
    "developer", "software engineer", "software developer", "fullstack", "full stack",
    "full-stack", "backend", "back-end", "back end", "frontend", "front-end",
    "front end", "laravel", "larval", "senior", "programmer", "coder",
    "engineer", "web dev", "mobile dev", "devops", "cloud engineer",
    "flutter", "react", "vue", "php", "python", "golang", "node"
]

# ==========================================
# Gender Detection Pronouns & Keywords
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
    "mother", "mom", "lady", "sister", "wife"
]

MALE_BIO_KEYWORDS = [
    "father", "dad", "husband", "brother", "guy", "boy developer"
]

# Kurdish & Regional Female First Names
FEMALE_NAMES = {
    # Kurdish Specific
    "banaz", "tara", "choman", "dlan", "payman", "saya", "lanja", "sheno", "zhina",
    "dilar", "kanar", "shler", "chro", "vian", "avesta", "narin", "perwin", "solin",
    "roza", "helin", "rojin", "berivan", "dlvin", "chra", "kazhal", "shadan", "kwestan",
    "sazan", "sozan", "lawen", "runak", "nishtiman", "gashaw", "zhian", "aveen", "avin",
    "jehan", "darya", "shne", "lana", "helena", "khatoon", "naza", "tre", "taza",
    # Arabic / Middle Eastern
    "sarah", "sara", "fatima", "fatimah", "zahra", "maryam", "mariam", "noor", "nour",
    "zainab", "zeinab", "aya", "ayah", "layla", "leila", "yasmin", "yasmine", "reem",
    "rania", "salma", "huda", "mona", "dina", "nada", "maha", "lina", "leena", "amina",
    "khadija", "khadeeja", "asma", "hanan", "rasha", "rola", "samira", "dalal", "bushra",
    "iman", "amal", "duaa", "israa", "marwa", "shaimaa", "heba", "hager", "rawan", "shahad",
    # Western / International
    "emily", "jessica", "ashley", "amanda", "jennifer", "stephanie", "nicole", "elizabeth",
    "megan", "hannah", "rachel", "lauren", "samantha", "victoria", "chloe", "olivia", "emma",
    "ava", "sophia", "isabella", "mia", "charlotte", "amelia", "harper", "evelyn", "abigail",
    "ella", "camila", "luna", "sofia", "avery", "grace", "zoey", "lily", "claire", "anna",
    "julia", "laura", "maria", "alina", "daria", "valeria", "yulia", "anastasia", "eva"
}

# Kurdish & Regional Male First Names
MALE_NAMES = {
    # Kurdish Specific
    "soran", "diyar", "karwan", "rebaz", "zana", "pawan", "sivar", "hekar", "rawand",
    "hardy", "hardi", "heja", "shvan", "alan", "ranj", "danar", "hiwa", "dana", "aso",
    "hawkar", "brwa", "goran", "kani", "dlawar", "sarkawt", "sarkaw", "araz", "harem",
    "bokan", "botan", "bawer", "dlshad", "dilshad", "aram", "kawa", "ari", "peshawa",
    "shero", "rebwar", "arman", "armin", "shaho", "sirwan", "ferhad", "farhad", "kamaran",
    "bakhtiar", "hawre", "hemn", "hemin", "lawan", "yadgar", "shirwan", "chalak", "daban",
    "baryar", "rebin", "sangar", "zhiyar", "kardo", "chia", "rekan", "dastan", "hoshang",
    # Arabic / Middle Eastern
    "ahmad", "ahmed", "ali", "mohammed", "mohammad", "muhammad", "mhamad", "mhammad",
    "mamad", "mehmet", "omar", "hussein", "hassan", "mustafa", "ibrahim", "khalid",
    "youssef", "yousef", "tariq", "bilal", "zayd", "hamza", "karim", "amr", "abdullah",
    "abdul", "saad", "tamer", "mahmoud", "fadi", "rami", "wail", "samer", "ziad", "hisham",
    "yasin", "faisal", "nasser", "adel", "bassem", "osama", "waleed", "saleh", "marwan",
    # Western / International
    "john", "james", "robert", "michael", "william", "david", "richard", "joseph", "thomas",
    "charles", "christopher", "daniel", "matthew", "anthony", "mark", "paul", "andrew",
    "joshua", "kevin", "brian", "george", "edward", "jason", "ryan", "jacob", "eric",
    "alexander", "patrick", "adam", "peter", "noah", "lucas", "leo", "julian"
}

# Targeted Kurdish Developer Search Vectors
KURDISH_DEV_VECTORS = [
    ("location:Kurdistan developer", "Kurdistan • Dev"),
    ("location:Kurdistan fullstack", "Kurdistan • Fullstack"),
    ("location:Kurdistan backend", "Kurdistan • Backend"),
    ("location:Kurdistan software", "Kurdistan • Software"),
    ("location:Kurdistan laravel", "Kurdistan • Laravel"),
    ("location:Erbil developer", "Erbil • Dev"),
    ("location:Erbil fullstack", "Erbil • Fullstack"),
    ("location:Erbil software", "Erbil • Software"),
    ("location:Erbil backend", "Erbil • Backend"),
    ("location:Erbil laravel", "Erbil • Laravel"),
    ("location:Sulaymaniyah developer", "Sulaymaniyah • Dev"),
    ("location:Sulaymaniyah software", "Sulaymaniyah • Software"),
    ("location:Sulaymaniyah fullstack", "Sulaymaniyah • Fullstack"),
    ("location:Duhok developer", "Duhok • Dev"),
    ("location:Duhok software", "Duhok • Software"),
    ("location:Kirkuk developer", "Kirkuk • Dev"),
    ("location:Hawler developer", "Hawler • Dev"),
    ("location:Slemani developer", "Slemani • Dev"),
    ("location:Halabja developer", "Halabja • Dev"),
    ("location:Zakho developer", "Zakho • Dev"),
    ("Kurdish developer in:bio", "Kurdish bio • Dev"),
    ("Kurdistan software in:bio", "Kurdistan bio • Software"),
]


def detect_gender(name: str | None, bio: str | None, username: str) -> tuple[str, str]:
    """
    Detects profile gender based on pronouns, bio keywords, first name, and username.
    Returns: (gender: "female" | "male" | "unknown", reason: str)
    """
    text = f"{name or ''} {bio or ''}".lower()

    # 1. Pronouns
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

    # 3. First Name
    if name:
        first_word = name.strip().replace("-", " ").replace("_", " ").split()[0].lower()
        clean_first = "".join(c for c in first_word if c.isalpha())
        if clean_first in FEMALE_NAMES:
            return "female", f"name '{clean_first.capitalize()}'"
        if clean_first in MALE_NAMES:
            return "male", f"name '{clean_first.capitalize()}'"

    # 4. Username Prefix
    uname_lower = username.lower().replace("-", "").replace("_", "")
    for fn in FEMALE_NAMES:
        if len(fn) >= 4 and uname_lower.startswith(fn):
            return "female", f"username '{fn}'"

    for mn in MALE_NAMES:
        if len(mn) >= 4 and uname_lower.startswith(mn):
            return "male", f"username '{mn}'"

    return "unknown", "none"


def identify_developer_role(bio: str | None, name: str | None, company: str | None) -> tuple[bool, str]:
    """
    Inspects bio, name, and company to verify developer role.
    """
    text = f"{bio or ''} {name or ''} {company or ''}".lower()

    # High-priority specific roles requested by user
    for role, label in [
        ("fullstack", "Fullstack Developer"),
        ("full stack", "Fullstack Developer"),
        ("full-stack", "Fullstack Developer"),
        ("software engineer", "Software Engineer"),
        ("software developer", "Software Developer"),
        ("backend", "Backend Developer"),
        ("back-end", "Backend Developer"),
        ("back end", "Backend Developer"),
        ("laravel", "Laravel Developer"),
        ("larval", "Laravel Developer"),
        ("senior", "Senior Engineer"),
        ("frontend", "Frontend Developer"),
        ("front-end", "Frontend Developer"),
        ("mobile dev", "Mobile Developer"),
        ("flutter", "Flutter Developer"),
        ("web dev", "Web Developer"),
        ("developer", "Developer"),
        ("engineer", "Engineer"),
        ("programmer", "Programmer"),
        ("coder", "Coder"),
    ]:
        if role in text:
            return True, label

    return False, "Developer"


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
    """Tracks users already processed in-memory and on disk to prevent duplicates and logs activity."""
    def __init__(self, path: Path, log_path: Path | None = None):
        self.path = path
        self.log_path = log_path or FOLLOWS_LOG_PATH
        self.history: set[str] = set()
        self.records: list[dict] = []
        self.load()

    def load(self):
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = set(data.get("followed", []))
                    self.records = data.get("records", [])
            except Exception:
                self.history = set()
                self.records = []

    def save(self):
        try:
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump({
                    "followed": sorted(list(self.history)),
                    "records": self.records
                }, f, indent=2)
        except Exception as e:
            print(f"{YELLOW}[!] Failed to save history: {e}{RESET}")

    def add(self, username: str, auto_save: bool = True):
        self.history.add(username.lower())
        if auto_save:
            self.save()

    def add_record(self, username: str, loc_tag: str = "", role_tag: str = "", gender_tag: str = ""):
        """Records followed developer into history list, rich record store, and follows.log text file."""
        self.history.add(username.lower())
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = {
            "timestamp": now_str,
            "username": username,
            "url": f"https://github.com/{username}",
            "location": loc_tag,
            "role": role_tag,
            "gender": gender_tag
        }
        self.records.append(record)
        self.save()

        # Write to human-readable follows.log
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(
                    f"[{now_str}] FOLLOWED: @{username:<20} | URL: https://github.com/{username:<25} | "
                    f"Role: {role_tag:<22} | Gender: {gender_tag:<20} | Location: {loc_tag}\n"
                )
        except Exception:
            pass

    def contains(self, username: str) -> bool:
        return username.lower() in self.history


class KurdishBot:
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
            "User-Agent": "Kurdish-Developer-AutoPilot/3.0",
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

    def inspect_developer_profile(self, username: str) -> tuple[bool, str, str]:
        """
        Inspects user profile to verify:
        1. Developer role (Fullstack, Backend, Software Engineer, Laravel, Senior, etc.)
        2. Gender filter (female/male/all)
        Returns: (passes: bool, role_tag: str, gender_tag: str)
        """
        resp = self.session.get(f"{GITHUB_API_BASE}/users/{username}")
        if resp.status_code != 200:
            return False, "", ""

        user_data = resp.json()
        bio = user_data.get("bio")
        name = user_data.get("name")
        company = user_data.get("company")
        public_repos = user_data.get("public_repos", 0)

        # 1. Developer Role check
        is_dev, role_tag = identify_developer_role(bio, name, company)
        # If user has repositories and was found via developer search, qualify them as developer
        if not is_dev and public_repos > 0:
            is_dev = True
            role_tag = "Software Dev"

        if not is_dev:
            return False, "", ""

        # 2. Gender check
        gender, gender_reason = detect_gender(name, bio, username)

        if self.gender_filter in ("female", "girl", "girls", "f"):
            if gender != "female":
                return False, "", ""
            return True, role_tag, f"👩 Female ({gender_reason})"

        elif self.gender_filter in ("male", "boy", "boys", "m"):
            if gender != "male":
                return False, "", ""
            return True, role_tag, f"👨 Male ({gender_reason})"

        # All genders accepted
        tag = "👩 Female" if gender == "female" else ("👨 Male" if gender == "male" else "Dev")
        return True, role_tag, tag

    def follow(self, username: str, loc_tag: str = "", role_tag: str = "", gender_tag: str = "") -> bool:
        """Sends PUT request to follow a GitHub user directly with auto-backoff and logging."""
        if self.dry_run:
            return True

        if self.history.contains(username):
            return False

        max_retries = 3
        for attempt in range(max_retries):
            resp = self.session.put(f"{GITHUB_API_BASE}/user/following/{username}")
            if resp.status_code == 204:
                self.history.add_record(username, loc_tag=loc_tag, role_tag=role_tag, gender_tag=gender_tag)
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

    def scan_kurdish_developers(self, goal: int = DEFAULT_BATCH_SIZE) -> list[tuple[str, str, str, str]]:
        """
        Scans Kurdish developer queries, inspects profiles for tech roles & gender.
        Returns: list of (username, location_label, role_tag, gender_tag)
        """
        candidates: list[tuple[str, str, str, str]] = []
        per_page = 100
        scanned_total = 0
        skipped_total = 0

        gender_label = "GIRLS ONLY" if self.gender_filter in ("female", "girl", "girls") else (
            "BOYS ONLY" if self.gender_filter in ("male", "boy", "boys") else "ALL (BOYS & GIRLS)"
        )

        print(f"{YELLOW}☀️ Scanning GitHub for {goal} Verified Kurdish Developers [{gender_label}]...{RESET}")
        print(f"{DIM}Target Roles: Fullstack, Backend, Software Engineers, Laravel, Senior Devs{RESET}\n")

        for query, label in KURDISH_DEV_VECTORS:
            if len(candidates) >= goal:
                break

            cursor_key = f"{query}_{self.gender_filter}"
            page = self.cursors.get_page(cursor_key)
            max_pages = 5

            while len(candidates) < goal and max_pages > 0:
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

                    passes, role_tag, gender_tag = self.inspect_developer_profile(username)
                    if passes:
                        candidates.append((username, label, role_tag, gender_tag))
                        if len(candidates) >= goal:
                            break
                    else:
                        skipped_total += 1

                    sys.stdout.write(
                        f"\r  {CYAN}📍 [{label}]{RESET} Page {page} │ "
                        f"Scanned: {BOLD}{scanned_total}{RESET} │ "
                        f"Filtered: {YELLOW}{skipped_total}{RESET} │ "
                        f"Matched Devs: {GREEN}{BOLD}{len(candidates)}/{goal}{RESET} "
                    )
                    sys.stdout.flush()

                page += 1
                max_pages -= 1
                if len(items) < per_page:
                    break

            self.cursors.set_page(cursor_key, page)

        print(f"\n{GREEN}✓ Scan completed! Ready with {len(candidates)} verified Kurdish developers.{RESET}\n")
        return candidates

    def print_batch_dashboard(self, goal: int, batch_num: int):
        """Displays Kurdish themed header card with gender and role info."""
        est_seconds = goal * self.delay
        est_duration = format_duration(est_seconds)
        eta_time = time.strftime("%I:%M:%S %p", time.localtime(time.time() + est_seconds))
        speed_text = f"{int(60 / max(self.delay, 0.1))} follows/min ({self.delay}s delay)"
        cur_following = self.user_stats.get("following", 0)

        gender_badge = "👩 Girls Only" if self.gender_filter in ("female", "girl", "girls") else (
            "👨 Boys Only" if self.gender_filter in ("male", "boy", "boys") else "🌟 All (Boys & Girls)"
        )

        box_width = 62
        print(f"{YELLOW}╭{'─' * box_width}╮{RESET}")
        title = f"☀️ BATCH #{batch_num} — {goal} KURDISH DEVELOPERS ☀️"
        print(f"{YELLOW}│{BOLD}{title:^{box_width}}{RESET}{YELLOW}│{RESET}")
        print(f"{YELLOW}├{'─' * box_width}┤{RESET}")
        print(f"{YELLOW}│{RESET}  👤 {BOLD}Operator:{RESET}    @{self.current_user:<16}  👥 {BOLD}Followers:{RESET} {str(self.user_stats.get('followers', 0)):<13}{YELLOW}│{RESET}")
        print(f"{YELLOW}│{RESET}  📍 {BOLD}Target:{RESET}      Kurdish Devs      🔄 {BOLD}Following:{RESET} {str(cur_following):<13}{YELLOW}│{RESET}")
        print(f"{YELLOW}│{RESET}  💻 {BOLD}Tech Roles:{RESET}  Fullstack, Backend, Laravel, Software Engineers  {YELLOW}│{RESET}")
        print(f"{YELLOW}│{RESET}  🏷️  {BOLD}Gender:{RESET}      {gender_badge:<16}  ⚡ {BOLD}Speed:{RESET}     {speed_text:<13}{YELLOW}│{RESET}")
        print(f"{YELLOW}│{RESET}  ⏱️  {BOLD}Est Time:{RESET}    {est_duration:<16}  🏁 {BOLD}Batch ETA:{RESET} {eta_time:<13}{YELLOW}│{RESET}")
        print(f"{YELLOW}╰{'─' * box_width}╯{RESET}\n")

    def run_batch(self, targets: list[tuple[str, str, str, str]], goal: int, batch_num: int = 1) -> tuple[int, float]:
        """Executes following for the target list with real-time progress bar and role tags."""
        if not targets:
            print(f"{YELLOW}[!] No candidate accounts available.{RESET}")
            return 0, 0.0

        self.print_batch_dashboard(goal, batch_num)

        success_count = 0
        start_time = time.time()

        try:
            for idx, (username, loc_tag, role_tag, gender_tag) in enumerate(targets, 1):
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
                print(
                    f"  → Following {BOLD}@{username}{RESET} "
                    f"{YELLOW}[📍 {loc_tag}]{RESET} "
                    f"{GREEN}[💻 {role_tag}]{RESET} "
                    f"{CYAN}[{gender_tag}]{RESET}...",
                    end="",
                    flush=True
                )

                if self.follow(username, loc_tag=loc_tag, role_tag=role_tag, gender_tag=gender_tag):
                    success_count += 1
                    if self.dry_run:
                        print(f" {YELLOW}[DRY-RUN]{RESET}")
                    else:
                        now_time = datetime.now().strftime("%H:%M:%S")
                        print(f" {GREEN}✓ Followed!{RESET} {DIM}(Logged at {now_time}){RESET}")
                        print(f"    {DIM}↳ 🔗 https://github.com/{username}  [Saved in follows.log]{RESET}")
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
    Continuous Auto-Pilot with 2-Hour Rest Break:
    1. Discovers and follows verified Kurdish developers (Fullstack/Backend/Laravel/Software Engineers).
    2. Rests 2 hours to clear GitHub hourly rate limits.
    3. Repeats automatically.
    """
    break_seconds = int(break_hours * 3600)
    batch_num = 1
    total_session_followed = 0

    gender_label = "GIRLS ONLY" if bot.gender_filter in ("female", "girl", "girls") else (
        "BOYS ONLY" if bot.gender_filter in ("male", "boy", "boys") else "ALL (BOYS & GIRLS)"
    )

    print(f"\n{YELLOW}╭{'─' * 62}╮{RESET}")
    print(f"{YELLOW}│{BOLD}{'☀️ KURDISH AUTO-PILOT ACTIVATED (2-HOUR BREAK CYCLE) ☀️':^62}{RESET}{YELLOW}│{RESET}")
    print(f"{YELLOW}├{'─' * 62}┤{RESET}")
    print(f"{YELLOW}│{RESET}  • Target:       Verified Kurdish Developers [{gender_label}]{' ' * (62 - len(gender_label) - 46)}{YELLOW}│{RESET}")
    print(f"{YELLOW}│{RESET}  • Tech Roles:   Fullstack, Backend, Software Engineers, Laravel{' ' * 14}{YELLOW}│{RESET}")
    print(f"{YELLOW}│{RESET}  • Batch Size:   {batch_size} developers per cycle{' ' * (62 - len(str(batch_size)) - 34)}{YELLOW}│{RESET}")
    print(f"{YELLOW}│{RESET}  • Rest Break:   {break_hours} hours (Completely resets GitHub rate limits){' ' * (62 - len(str(break_hours)) - 53)}{YELLOW}│{RESET}")
    print(f"{YELLOW}│{RESET}  • Stop:         Press {RED}Ctrl+C{RESET} at any time to pause or exit{' ' * 19}{YELLOW}│{RESET}")
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
            print(f"{GREEN}│{RESET}  ✓ {BOLD}Followed in This Batch:{RESET}  {followed} developers{' ' * (box_width - len(str(followed)) - 35)}{GREEN}│{RESET}")
            print(f"{GREEN}│{RESET}  🌟 {BOLD}Total in Auto-Pilot:{RESET}     {total_session_followed} developers{' ' * (box_width - len(str(total_session_followed)) - 33)}{GREEN}│{RESET}")
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


def show_follow_log(bot: KurdishBot, limit: int = 30):
    """Displays a clean formatted table of followed users from history and log file."""
    total_followed = len(bot.history.history)
    records = bot.history.records
    total_records = len(records)

    box_width = 78
    print(f"\n{CYAN}╭{'─' * box_width}╮{RESET}")
    title = "📜 KURDISH DEVELOPER FOLLOW LOG & HISTORY"
    print(f"{CYAN}│{BOLD}{title:^{box_width}}{RESET}{CYAN}│{RESET}")
    print(f"{CYAN}├{'─' * box_width}┤{RESET}")
    print(f"{CYAN}│{RESET}  • Total Accounts in Database:  {BOLD}{total_followed}{RESET}{' ' * (box_width - len(str(total_followed)) - 35)}{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  • Detailed Follow Log Records: {BOLD}{total_records}{RESET}{' ' * (box_width - len(str(total_records)) - 35)}{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  • Activity Log File:           {BOLD}{str(bot.history.log_path.name)}{RESET}{' ' * (box_width - len(str(bot.history.log_path.name)) - 35)}{CYAN}│{RESET}")
    print(f"{CYAN}╰{'─' * box_width}╯{RESET}\n")

    if records:
        display_records = list(records[-limit:])
        display_records.reverse()

        print(f"{BOLD}{'#':<4} {'Date & Time':<20} {'Developer':<20} {'Role':<22} {'Gender':<12}{RESET}")
        print(f"{DIM}{'─' * box_width}{RESET}")

        for idx, r in enumerate(display_records, 1):
            ts = r.get("timestamp", "Unknown")
            uname = f"@{r.get('username', '')}"
            role = r.get("role", "Developer")
            gender = r.get("gender", "")
            url = r.get("url", f"https://github.com/{r.get('username', '')}")
            loc = r.get("location", "")

            print(f"{idx:02d}.  {ts:<20} {BOLD}{uname:<20}{RESET} {GREEN}{role:<22}{RESET} {CYAN}{gender:<12}{RESET}")
            print(f"     {DIM}↳ 🔗 {url}  [📍 {loc}]{RESET}")

        print(f"\n{GREEN}✓ Showing {len(display_records)} most recent logged follows (out of {total_records} records).{RESET}")
    elif total_followed > 0:
        usernames = sorted(list(bot.history.history), reverse=True)[:limit]
        print(f"{YELLOW}Showing last {len(usernames)} followed usernames from database (total: {total_followed}):{RESET}\n")
        for i, u in enumerate(usernames, 1):
            print(f"  {DIM}{i:02d}.{RESET} {BOLD}@{u:<24}{RESET} 🔗 https://github.com/{u}")
        print(f"\n{DIM}Note: New follows with this version will record timestamp, tech role, and gender in follows.log.{RESET}")
    else:
        print(f"{YELLOW}[!] No follow records logged yet. Run Auto-Pilot or a batch to start following!{RESET}")

    print(f"\n{DIM}📁 Full live log file is saved to: {bot.history.log_path.resolve()}{RESET}\n")

    # Quick search prompt if interactive
    if sys.stdin.isatty():
        try:
            query = input(f"{CYAN}🔍 Enter a username to check if already followed (or press Enter to return): {RESET}").strip().lstrip("@")
            if query:
                if bot.history.contains(query):
                    matching = [r for r in records if r.get("username", "").lower() == query.lower()]
                    print(f"\n{GREEN}✓ YES! You have already followed @{query}.{RESET}")
                    if matching:
                        m = matching[-1]
                        print(f"  • Date/Time: {m.get('timestamp')}")
                        print(f"  • Role:      {m.get('role')}")
                        print(f"  • Gender:    {m.get('gender')}")
                        print(f"  • Location:  {m.get('location')}")
                    print(f"  • Profile:   https://github.com/{query}\n")
                else:
                    print(f"\n{YELLOW}✗ @{query} has NOT been followed yet.{RESET}\n")
        except (EOFError, KeyboardInterrupt):
            pass


def ask_gender() -> str:
    """Lets user select their preferred gender filter at daily start."""
    print(f"\n👥 {BOLD}Choose Kurdish Developer Gender Filter:{RESET}")
    print(f"  1) {CYAN}🌟 All Kurdish Developers (Boys & Girls){RESET} [Default - Recommended]")
    print(f"  2) {MAGENTA}👩 Kurdish Girls Only{RESET} (Female Fullstack / Backend / Software Engineers)")
    print(f"  3) {BLUE}👨 Kurdish Boys Only{RESET}  (Male Fullstack / Backend / Software Engineers)")

    choice = input("\nEnter choice [1-3, default 1]: ").strip()
    if choice == "2":
        return "female"
    elif choice == "3":
        return "male"
    return "all"


def main():
    parser = argparse.ArgumentParser(description="☀️ Kurdish Developer Auto-Pilot Pro")
    parser.add_argument("--auto", action="store_true", help="Start continuous Auto-Pilot (Follow batch -> 2h break -> Repeat)")
    parser.add_argument("--gender", default="all", choices=["all", "female", "girl", "girls", "male", "boy", "boys"], help="Filter by gender (girl/boy/all)")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help=f"Follows per batch (default: {DEFAULT_BATCH_SIZE})")
    parser.add_argument("--break-hours", type=float, default=DEFAULT_BREAK_HOURS, help=f"Break hours between batches (default: {DEFAULT_BREAK_HOURS})")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help=f"Seconds between follows (default: {DEFAULT_DELAY})")
    parser.add_argument("--once", action="store_true", help="Run only one single batch now and exit")
    parser.add_argument("--log", nargs="?", const=30, type=int, help="Show log of followed users (default: last 30)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making actual follow requests")

    args = parser.parse_args()

    token = get_token()
    bot = KurdishBot(token, dry_run=args.dry_run, delay=args.delay, gender_filter=args.gender)

    user_info = bot.verify_account()
    if not user_info:
        print(f"{RED}[!] Authentication failed. Check your token in {ENV_PATH}.{RESET}")
        sys.exit(1)

    print(f"{GREEN}{BOLD}✓ Authenticated as @{user_info.get('login')}{RESET}")
    print(f"  Followers: {user_info.get('followers')} | Following: {user_info.get('following')}\n")

    if args.log is not None:
        show_follow_log(bot, limit=args.log)
        return

    # Sync following list
    bot.preload_current_following()

    if args.auto:
        run_autopilot_cycle(bot, batch_size=args.batch_size, break_hours=args.break_hours)
    elif args.once:
        candidates = bot.scan_kurdish_developers(goal=args.batch_size)
        bot.run_batch(candidates, goal=args.batch_size, batch_num=1)
    else:
        while True:
            # Interactive Daily Start
            print(f"{BOLD}Choose Operation Mode:{RESET}")
            print(f"  {CYAN}1) 🔄 Start Kurdish Auto-Pilot (Follow {args.batch_size} → 2-Hour Break → Repeat){RESET} [Default - Press Enter]")
            print(f"  {YELLOW}2) ⚡ Run Single Batch of {args.batch_size} Now & Exit{RESET}")
            print(f"  {MAGENTA}3) 📜 View Follow Log & History (Show users you have followed){RESET}")
            print(f"  4) 🛑 Exit")

            mode_choice = input("\nEnter choice [1-4, default 1]: ").strip()
            if mode_choice == "4":
                print("Exited.")
                return
            elif mode_choice == "3":
                show_follow_log(bot)
                try:
                    input(f"\n{DIM}Press Enter to return to main menu...{RESET}")
                except (EOFError, KeyboardInterrupt):
                    return
                print()
                continue

            # Choose Gender at Start
            bot.gender_filter = ask_gender()

            if mode_choice == "2":
                candidates = bot.scan_kurdish_developers(goal=args.batch_size)
                bot.run_batch(candidates, goal=args.batch_size, batch_num=1)
                break
            else:
                run_autopilot_cycle(bot, batch_size=args.batch_size, break_hours=args.break_hours)
                break


if __name__ == "__main__":
    main()
