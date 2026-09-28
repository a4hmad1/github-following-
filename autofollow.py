#!/usr/bin/env python3
"""
🚀 Developer Auto-Pilot Pro (Global Software Engineers, Developers & Backend Specialists Edition)
Discovers and follows verified Software Engineers, Software Developers, and Backend Developers
globally and regionally with zero duplicate risk.

Features:
- Primary Target Roles: Software Engineers, Software Developers, Backend Developers, Fullstack.
- Global Scope: Worldwide Tech Hubs (USA, Europe, Asia, Americas, Remote) with dedicated Kurdish scope option.
- Intelligent Pacing & Cooldown: Prevents secondary rate limits and safely handles GitHub API limits.
- Cursor Auto-Wrap: Automatically cycles search pages and refreshes developer pools.
- Zero Duplicates: Double in-memory and disk verification guarantees no user is followed twice.
- 24/7 Background Support: Built for non-stop daemon execution with clean logging and status reporting.
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

# Terminal Colors
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

DEFAULT_BATCH_SIZE = 250      # 250 follows per batch
DEFAULT_BREAK_HOURS = 0.5     # 30 minutes break between batches
DEFAULT_DELAY = 1.0           # 1.0s delay between follows

# ==========================================
# Verified Tech Developer Role Keywords
# ==========================================
DEV_KEYWORDS = [
    "software engineer", "software developer", "backend developer", "backend engineer",
    "back-end developer", "back-end engineer", "fullstack", "full stack", "full-stack",
    "software", "developer", "engineer", "programmer", "coder", "laravel", "senior",
    "frontend", "front-end", "web dev", "mobile dev", "devops", "cloud engineer",
    "python", "golang", "node", "java", "rust", "php", "c++", "typescript"
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

# ==========================================
# Categorized Search Vectors
# ==========================================

# 1. Primary Targeted Roles (Software Engineer, Software Developer, Backend Developer)
SOFTWARE_ENGINEER_VECTORS = [
    ('"software engineer" type:user repos:>5 followers:>2', "Global • Software Engineer"),
    ('"software engineer" type:user repos:>10', "Global • Software Engineer (Active)"),
    ('"software engineer" type:user followers:>10', "Global • Software Engineer (Popular)"),
    ('"senior software engineer" type:user repos:>5', "Global • Senior Software Engineer"),
    ('"lead software engineer" type:user repos:>5', "Global • Lead Software Engineer"),
    ('"staff software engineer" type:user repos:>5', "Global • Staff Software Engineer"),
    ('"software engineer" type:user location:"United States" repos:>5', "USA • Software Engineer"),
    ('"software engineer" type:user location:"United Kingdom" repos:>5', "UK • Software Engineer"),
    ('"software engineer" type:user location:"Germany" repos:>5', "Germany • Software Engineer"),
    ('"software engineer" type:user location:"Canada" repos:>5', "Canada • Software Engineer"),
    ('"software engineer" type:user location:"Netherlands" repos:>3', "Netherlands • Software Engineer"),
    ('"software engineer" type:user location:"Sweden" repos:>3', "Sweden • Software Engineer"),
    ('"software engineer" type:user location:"Australia" repos:>3', "Australia • Software Engineer"),
    ('"software engineer" type:user location:"France" repos:>3', "France • Software Engineer"),
    ('"software engineer" type:user location:"Singapore" repos:>3', "Singapore • Software Engineer"),
    ('"software engineer" type:user location:"Japan" repos:>3', "Japan • Software Engineer"),
    ('"software engineer" type:user location:"Switzerland" repos:>3', "Switzerland • Software Engineer"),
    ('"software engineer" type:user location:"remote" repos:>3', "Remote • Software Engineer"),
]

SOFTWARE_DEVELOPER_VECTORS = [
    ('"software developer" type:user repos:>5 followers:>2', "Global • Software Developer"),
    ('"software developer" type:user repos:>10', "Global • Software Developer (Active)"),
    ('"software developer" type:user followers:>10', "Global • Software Developer (Popular)"),
    ('"senior software developer" type:user repos:>5', "Global • Senior Software Developer"),
    ('"fullstack developer" type:user repos:>5 followers:>2', "Global • Fullstack Developer"),
    ('"full-stack developer" type:user repos:>5', "Global • Full-Stack Developer"),
    ('"full stack engineer" type:user repos:>5', "Global • Full Stack Engineer"),
    ('"software developer" type:user location:"United States" repos:>5', "USA • Software Developer"),
    ('"software developer" type:user location:"United Kingdom" repos:>5', "UK • Software Developer"),
    ('"software developer" type:user location:"Germany" repos:>3', "Germany • Software Developer"),
    ('"software developer" type:user location:"Canada" repos:>3', "Canada • Software Developer"),
    ('"software developer" type:user location:"remote" repos:>3', "Remote • Software Developer"),
]

BACKEND_DEVELOPER_VECTORS = [
    ('"backend developer" type:user repos:>5 followers:>2', "Global • Backend Developer"),
    ('"backend engineer" type:user repos:>5 followers:>2', "Global • Backend Engineer"),
    ('"back-end developer" type:user repos:>5', "Global • Back-End Developer"),
    ('"senior backend engineer" type:user repos:>3', "Global • Senior Backend Engineer"),
    ('"backend developer" type:user repos:>10', "Global • Backend Dev (Active)"),
    ('"backend developer" type:user language:python repos:>3', "Backend • Python"),
    ('"backend developer" type:user language:go repos:>3', "Backend • Golang"),
    ('"backend developer" type:user language:nodejs repos:>3', "Backend • Node.js"),
    ('"backend developer" type:user language:java repos:>3', "Backend • Java"),
    ('"backend developer" type:user language:rust repos:>3', "Backend • Rust"),
    ('"backend developer" type:user language:php repos:>3', "Backend • PHP / Laravel"),
    ('"backend developer" type:user language:c# repos:>3', "Backend • C# / .NET"),
    ('"backend developer" type:user location:"United States" repos:>3', "USA • Backend Developer"),
    ('"backend developer" type:user location:"United Kingdom" repos:>3', "UK • Backend Developer"),
    ('"backend developer" type:user location:"Germany" repos:>3', "Germany • Backend Developer"),
    ('"backend developer" type:user location:"Canada" repos:>3', "Canada • Backend Developer"),
    ('"backend developer" type:user location:"remote" repos:>3', "Remote • Backend Developer"),
]

# Kurdish & Regional Developers (Maintained for dedicated regional scope)
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
    ("location:Sulaymaniyah backend", "Sulaymaniyah • Backend"),
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

# Aliases for backwards compatibility
PRIMARY_DEV_VECTORS = SOFTWARE_ENGINEER_VECTORS + SOFTWARE_DEVELOPER_VECTORS
BACKEND_STACK_VECTORS = BACKEND_DEVELOPER_VECTORS
GLOBAL_HUB_VECTORS = [v for v in SOFTWARE_ENGINEER_VECTORS if "location:" in v[0]]


def handle_rate_limit(resp: requests.Response, attempt: int = 0, default_wait: int = 60) -> int:
    """
    Intelligently determines wait seconds from headers.
    Distinguishes primary hourly rate limit (remaining == 0) from secondary abuse detection.
    """
    retry_after = resp.headers.get("Retry-After")
    if retry_after:
        try:
            return max(int(retry_after) + 2, 5)
        except ValueError:
            pass

    remaining = resp.headers.get("x-ratelimit-remaining")
    reset_time = resp.headers.get("x-ratelimit-reset")

    # Only sleep until reset_time if primary quota is genuinely exhausted (0 remaining)
    if remaining == "0" and reset_time:
        try:
            diff = int(reset_time) - int(time.time())
            return max(diff + 2, 5)
        except ValueError:
            pass

    # Secondary rate limits (anti-abuse) only require 30-60s cooldown
    return min(default_wait * (attempt + 1), 120)


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


def identify_developer_role(bio: str | None, name: str | None, company: str | None, default_role: str = "Developer") -> tuple[bool, str]:
    """
    Inspects bio, name, and company to verify developer role,
    prioritizing: Backend Developer, Software Engineer, Software Developer, Fullstack.
    """
    text = f"{bio or ''} {name or ''} {company or ''}".lower()

    # 1. Backend Developer / Backend Engineer
    for kw in [
        "backend developer", "back-end developer", "back end developer",
        "backend engineer", "back-end engineer", "back end engineer",
        "backend lead", "lead backend", "senior backend", "backend"
    ]:
        if kw in text:
            return True, "Backend Developer"

    # 2. Software Engineer
    for kw in [
        "software engineer", "software engineering", "senior software engineer",
        "lead software engineer", "principal software engineer", "staff software engineer",
        "swe", "systems engineer", "platform engineer", "infrastructure engineer"
    ]:
        if kw in text:
            return True, "Software Engineer"

    # 3. Software Developer
    for kw in [
        "software developer", "software development", "senior software developer",
        "lead software developer", "application developer", "software dev"
    ]:
        if kw in text:
            return True, "Software Developer"

    # 4. Fullstack Developer
    for kw in ["fullstack", "full stack", "full-stack"]:
        if kw in text:
            return True, "Fullstack Developer"

    # 5. Laravel & Backend Frameworks
    for kw in ["laravel", "django", "fastapi", "spring boot", "express.js", "nest.js", "ruby on rails"]:
        if kw in text:
            return True, "Backend Developer"

    # 6. Frontend Developer
    for kw in ["frontend developer", "front-end developer", "front end developer", "react developer", "vue developer"]:
        if kw in text:
            return True, "Frontend Developer"

    # 7. Cloud / DevOps
    for kw in ["devops", "cloud engineer", "cloud architect", "site reliability engineer", "sre"]:
        if kw in text:
            return True, "DevOps / Cloud Engineer"

    # 8. General Developer / Engineer
    for kw in ["developer", "engineer", "programmer", "coder", "web dev", "mobile dev", "flutter"]:
        if kw in text:
            return True, default_role if default_role != "Developer" else "Software Developer"

    return False, default_role


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


def update_daily_state(followed_count: int):
    """Tracks daily run counts and follows in daily_state.json."""
    today = datetime.now().strftime("%Y-%m-%d")
    state = {"runs": {}, "last_run": datetime.now().isoformat(), "today_follows": 0}
    if DAILY_STATE_PATH.exists():
        try:
            with open(DAILY_STATE_PATH, "r", encoding="utf-8") as f:
                state = json.load(f)
        except Exception:
            pass

    runs = state.get("runs", {})
    runs[today] = runs.get(today, 0) + 1
    state["runs"] = runs
    state["last_run"] = datetime.now().isoformat()
    state["today_follows"] = state.get("today_follows", 0) + followed_count

    try:
        with open(DAILY_STATE_PATH, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass


class CursorManager:
    """Tracks the last scanned page per search vector to avoid re-scanning with auto-wrap."""
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
        p = self.cursors.get(key, 1)
        if p > 10 or p < 1:
            return 1
        return p

    def set_page(self, key: str, page: int):
        if page > 10:
            page = 1
        self.cursors[key] = page
        self.save()

    def reset_all(self):
        """Resets all cursors to page 1."""
        self.cursors = {}
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
                    self.history = set(u.lower() for u in data.get("followed", []))
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

        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(
                    f"[{now_str}] FOLLOWED: @{username:<22} | URL: https://github.com/{username:<25} | "
                    f"Role: {role_tag:<24} | Gender: {gender_tag:<18} | Location: {loc_tag}\n"
                )
        except Exception:
            pass

    def contains(self, username: str) -> bool:
        return username.lower() in self.history


class AutoFollowerBot:
    """Core AutoFollower engine with multi-target discovery, rate-limit resilience, and safe following."""
    def __init__(
        self,
        token: str,
        dry_run: bool = False,
        delay: float = DEFAULT_DELAY,
        gender_filter: str = "all",
        target_scope: str = "global",
        role_filter: str = "all"
    ):
        self.token = token
        self.dry_run = dry_run
        self.delay = delay
        self.gender_filter = gender_filter.lower()    # "all", "female", "male"
        self.target_scope = target_scope.lower()      # "global", "software-engineer", "software-developer", "backend", "kurdish", "all"
        self.role_filter = role_filter.lower()        # "all", "software-engineer", "software-developer", "backend"
        self.session = requests.Session()

        # Connection pooling
        adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=2)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session.headers.update({
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "GitHub-AutoFollower-Pro/4.1",
        })
        self.current_user = ""
        self.user_stats = {}
        self.history = HistoryManager(HISTORY_PATH)
        self.cursors = CursorManager(CURSOR_PATH)

    def get_search_vectors(self) -> list[tuple[str, str]]:
        """
        Returns search vectors strictly matched to the chosen target scope.
        'global' focuses 100% on worldwide Software Engineers, Software Developers & Backend Devs.
        """
        if self.target_scope in ("kurdish", "kurdistan"):
            return KURDISH_DEV_VECTORS
        elif self.target_scope in ("backend", "back-end"):
            return BACKEND_DEVELOPER_VECTORS
        elif self.target_scope in ("software-engineer", "swe"):
            return SOFTWARE_ENGINEER_VECTORS
        elif self.target_scope in ("software-developer", "dev"):
            return SOFTWARE_DEVELOPER_VECTORS
        elif self.target_scope == "all":
            # Combines all global engineers, developers, backend specialists, and regional hubs
            return SOFTWARE_ENGINEER_VECTORS + SOFTWARE_DEVELOPER_VECTORS + BACKEND_DEVELOPER_VECTORS + KURDISH_DEV_VECTORS
        else:
            # Default "global": International Software Engineers, Software Developers & Backend Developers Worldwide
            return SOFTWARE_ENGINEER_VECTORS + SOFTWARE_DEVELOPER_VECTORS + BACKEND_DEVELOPER_VECTORS

    def verify_account(self) -> dict | None:
        """Verifies token and retrieves account information with retries and clear diagnostics."""
        for attempt in range(3):
            try:
                resp = self.session.get(f"{GITHUB_API_BASE}/user", timeout=15)
                if resp.status_code == 200:
                    self.user_stats = resp.json()
                    self.current_user = self.user_stats.get("login", "")
                    return self.user_stats
                elif resp.status_code == 401:
                    print(f"{RED}[!] Authentication failed (HTTP 401 Unauthorized): Check your token in {ENV_PATH}.{RESET}")
                    return None
                elif resp.status_code in (403, 429):
                    wait_sec = handle_rate_limit(resp, attempt, default_wait=30)
                    print(f"{YELLOW}[!] GitHub API temporarily rate limited (HTTP {resp.status_code}). Pausing {wait_sec}s...{RESET}")
                    time.sleep(wait_sec)
                    continue
                else:
                    print(f"{YELLOW}[!] GitHub returned status {resp.status_code}. Retrying ({attempt+1}/3)...{RESET}")
                    time.sleep(2)
            except requests.RequestException as e:
                print(f"{YELLOW}[!] Connection issue verifying account: {e}. Retrying ({attempt+1}/3)...{RESET}")
                time.sleep(3)
        return None

    def refresh_user_stats(self) -> dict:
        """Refreshes account stats from GitHub."""
        try:
            resp = self.session.get(f"{GITHUB_API_BASE}/user", timeout=15)
            if resp.status_code == 200:
                self.user_stats = resp.json()
        except requests.RequestException:
            pass
        return self.user_stats

    def preload_current_following(self):
        """Preloads all users that current_user already follows into memory in bulk."""
        is_interactive = sys.stdout.isatty()
        if is_interactive:
            print(f" {CYAN}⚡ Syncing current following list...{RESET}", end="", flush=True)
        else:
            print(f" ⚡ Syncing current following list from GitHub...", flush=True)

        page = 1
        count = 0
        while True:
            try:
                resp = self.session.get(f"{GITHUB_API_BASE}/user/following?per_page=100&page={page}", timeout=15)
                if resp.status_code == 200:
                    items = resp.json()
                    if not items or not isinstance(items, list):
                        break
                    for item in items:
                        self.history.add(item["login"], auto_save=False)
                        count += 1
                    if len(items) < 100:
                        break
                    page += 1
                    time.sleep(0.15)
                elif resp.status_code in (403, 429):
                    wait_sec = handle_rate_limit(resp, 0, default_wait=30)
                    time.sleep(wait_sec)
                    continue
                else:
                    break
            except requests.RequestException:
                time.sleep(1)
                break
        self.history.save()
        if is_interactive:
            print(f" {GREEN}Done ({count} accounts cached, {len(self.history.history)} total in memory){RESET}\n", flush=True)
        else:
            print(f" ✓ Following list synced ({count} accounts cached, {len(self.history.history)} total in memory)\n", flush=True)

    def inspect_developer_profile(self, username: str, default_role: str = "Software Developer") -> tuple[bool, str, str]:
        """
        Inspects user profile with polite pacing and safe rate-limit backoff to verify:
        1. Developer role (Software Engineer, Software Developer, Backend Developer, Fullstack, etc.)
        2. Gender filter (female/male/all)
        Returns: (passes: bool, role_tag: str, gender_tag: str)
        """
        # Polite spacing to avoid triggering secondary rate limit bursts
        time.sleep(0.15)

        for attempt in range(3):
            try:
                resp = self.session.get(f"{GITHUB_API_BASE}/users/{username}", timeout=15)
                if resp.status_code == 200:
                    user_data = resp.json()
                    bio = user_data.get("bio")
                    name = user_data.get("name")
                    company = user_data.get("company")
                    public_repos = user_data.get("public_repos", 0)

                    # 1. Developer Role check
                    is_dev, role_tag = identify_developer_role(bio, name, company, default_role=default_role)
                    if not is_dev and public_repos > 0:
                        is_dev = True
                        role_tag = default_role

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

                elif resp.status_code in (403, 429):
                    wait_sec = handle_rate_limit(resp, attempt, default_wait=45)
                    print(f"\n{YELLOW}  ⚠️ GitHub API rate limit pause: waiting {wait_sec}s...{RESET}", flush=True)
                    time.sleep(wait_sec)
                    continue
                elif resp.status_code == 404:
                    return False, "", ""
                else:
                    return False, "", ""
            except requests.RequestException:
                time.sleep(2)
                continue

        return False, "", ""

    def follow(self, username: str, loc_tag: str = "", role_tag: str = "", gender_tag: str = "") -> bool:
        """Sends PUT request to follow a GitHub user directly with auto-backoff and logging."""
        if self.dry_run:
            return True

        if self.history.contains(username):
            return False

        max_retries = 3
        for attempt in range(max_retries):
            try:
                resp = self.session.put(f"{GITHUB_API_BASE}/user/following/{username}", timeout=15)
                if resp.status_code == 204:
                    self.history.add_record(username, loc_tag=loc_tag, role_tag=role_tag, gender_tag=gender_tag)
                    return True

                if resp.status_code in (403, 429):
                    wait_sec = handle_rate_limit(resp, attempt, default_wait=60)
                    print(f"\n{YELLOW}  ⚠️ GitHub follow limit/cooldown. Pausing {wait_sec}s...{RESET}", flush=True)
                    time.sleep(wait_sec)
                    continue

                if resp.status_code in (404, 422):
                    # Account might be an org or inactive
                    return False

                return False
            except requests.RequestException:
                time.sleep(2)
                continue

        return False

    def scan_developers(self, goal: int = DEFAULT_BATCH_SIZE) -> list[tuple[str, str, str, str]]:
        """
        Scans categorized developer queries with rate limit management and auto-wrapping cursors.
        Returns: list of (username, location_label, role_tag, gender_tag)
        """
        candidates: list[tuple[str, str, str, str]] = []
        per_page = 100
        scanned_total = 0
        skipped_total = 0
        is_interactive = sys.stdout.isatty()

        vectors = self.get_search_vectors()

        gender_label = "GIRLS ONLY" if self.gender_filter in ("female", "girl", "girls") else (
            "BOYS ONLY" if self.gender_filter in ("male", "boy", "boys") else "ALL (BOYS & GIRLS)"
        )
        scope_label = self.target_scope.upper()

        print(f"{YELLOW}🚀 Scanning GitHub for {goal} Verified Developers [{scope_label} • {gender_label}]...{RESET}")
        print(f"{DIM}Focus: Software Engineers, Software Developers, Backend Developers Worldwide{RESET}\n", flush=True)

        for query, label in vectors:
            if len(candidates) >= goal:
                break

            cursor_key = f"{query}_{self.gender_filter}_{self.role_filter}"
            page = self.cursors.get_page(cursor_key)
            max_pages_per_vector = 3
            pages_searched = 0

            while len(candidates) < goal and pages_searched < max_pages_per_vector and page <= 10:
                # Pacing to strictly avoid triggering GitHub Search 30 req/min limit
                time.sleep(1.5)

                resp = None
                for attempt in range(3):
                    try:
                        resp = self.session.get(
                            f"{GITHUB_API_BASE}/search/users",
                            params={"q": query, "per_page": per_page, "page": page},
                            timeout=15
                        )
                        if resp.status_code == 200:
                            break
                        elif resp.status_code in (403, 429):
                            wait_sec = handle_rate_limit(resp, attempt, default_wait=30)
                            print(f"\n{YELLOW}  ⚠️ GitHub search rate limit. Pausing {wait_sec}s for reset...{RESET}", flush=True)
                            time.sleep(wait_sec)
                            continue
                        elif resp.status_code == 422:
                            # 1000 items limit reached for this vector, wrap cursor to 1
                            self.cursors.set_page(cursor_key, 1)
                            break
                        else:
                            break
                    except requests.RequestException:
                        time.sleep(2)
                        continue

                if not resp or resp.status_code != 200:
                    break

                try:
                    data = resp.json()
                except Exception:
                    break

                items = data.get("items", [])
                if not items:
                    self.cursors.set_page(cursor_key, 1)
                    break

                # Infer default role from vector label
                default_role = "Software Engineer" if "Software Eng" in label else (
                    "Backend Developer" if "Backend" in label else (
                        "Software Developer" if "Software Dev" in label else "Software Developer"
                    )
                )

                for item in items:
                    username = item.get("login")
                    if not username:
                        continue

                    scanned_total += 1

                    if self.history.contains(username) or username.lower() == self.current_user.lower():
                        skipped_total += 1
                        continue

                    # If filtering by gender or specific role, perform deep profile inspection
                    if self.gender_filter != "all" or self.role_filter != "all":
                        passes, role_tag, gender_tag = self.inspect_developer_profile(username, default_role=default_role)
                        if not passes:
                            skipped_total += 1
                            continue
                        if self.role_filter != "all":
                            rf = self.role_filter.lower().replace("-", " ")
                            if rf not in role_tag.lower():
                                skipped_total += 1
                                continue
                    else:
                        # For global all-gender search, users found by targeted queries directly match!
                        role_tag = default_role
                        gender_tag = "Dev"

                    candidates.append((username, label, role_tag, gender_tag))

                    if is_interactive:
                        sys.stdout.write(
                            f"\r  {CYAN}📍 [{label}]{RESET} Page {page} │ "
                            f"Scanned: {BOLD}{scanned_total}{RESET} │ "
                            f"Skipped/Dup: {YELLOW}{skipped_total}{RESET} │ "
                            f"Matched Devs: {GREEN}{BOLD}{len(candidates)}/{goal}{RESET} "
                        )
                        sys.stdout.flush()
                    else:
                        # Clean log output for background services
                        if len(candidates) % 10 == 0 or len(candidates) == goal:
                            print(
                                f"  📍 [{label}] Page {page} │ Scanned: {scanned_total} │ "
                                f"Skipped: {skipped_total} │ Matched Devs: {len(candidates)}/{goal}",
                                flush=True
                            )

                    if len(candidates) >= goal:
                        break

                pages_searched += 1
                page += 1
                if len(items) < per_page:
                    self.cursors.set_page(cursor_key, 1)
                    break

            if page > 10:
                self.cursors.set_page(cursor_key, 1)
            else:
                self.cursors.set_page(cursor_key, page)

        if is_interactive:
            sys.stdout.write("\n")
            sys.stdout.flush()

        if len(candidates) == 0:
            print(f"\n{YELLOW}[!] Search vectors reached end. Resetting cursors to refresh candidates on next pass...{RESET}", flush=True)
            self.cursors.reset_all()

        print(f"\n{GREEN}✓ Scan completed! Ready with {len(candidates)} verified developers.{RESET}\n", flush=True)
        return candidates

    def print_batch_dashboard(self, goal: int, batch_num: int):
        """Displays formatted header card with target scope, role, and speed info."""
        est_seconds = goal * self.delay
        est_duration = format_duration(est_seconds)
        eta_time = time.strftime("%I:%M:%S %p", time.localtime(time.time() + est_seconds))
        speed_text = f"{int(60 / max(self.delay, 0.1))} follows/min ({self.delay}s delay)"
        cur_following = self.user_stats.get("following", 0)

        gender_badge = "👩 Girls Only" if self.gender_filter in ("female", "girl", "girls") else (
            "👨 Boys Only" if self.gender_filter in ("male", "boy", "boys") else "🌟 All (Boys & Girls)"
        )
        scope_title = "GLOBAL TECH DEVS" if self.target_scope == "global" else (
            "BACKEND SPECIALISTS" if self.target_scope in ("backend", "back-end") else (
                "SOFTWARE ENGINEERS" if self.target_scope in ("software-engineer", "swe") else (
                    "SOFTWARE DEVELOPERS" if self.target_scope in ("software-developer", "dev") else (
                        "KURDISH DEVELOPERS" if self.target_scope == "kurdish" else "ALL DEVELOPERS"
                    )
                )
            )
        )

        box_width = 68
        print(f"{CYAN}╭{'─' * box_width}╮{RESET}")
        title = f"🚀 BATCH #{batch_num} — {goal} {scope_title} 🚀"
        print(f"{CYAN}│{BOLD}{title:^{box_width}}{RESET}{CYAN}│{RESET}")
        print(f"{CYAN}├{'─' * box_width}┤{RESET}")
        print(f"{CYAN}│{RESET}  👤 {BOLD}Operator:{RESET}    @{self.current_user:<18}  👥 {BOLD}Followers:{RESET} {str(self.user_stats.get('followers', 0)):<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  📍 {BOLD}Scope:{RESET}       {self.target_scope.capitalize():<18}  🔄 {BOLD}Following:{RESET} {str(cur_following):<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  💻 {BOLD}Tech Roles:{RESET}  Software Engineers, Software Devs, Backend Devs     {CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  🏷️  {BOLD}Gender:{RESET}      {gender_badge:<18}  ⚡ {BOLD}Speed:{RESET}     {speed_text:<15}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  ⏱️  {BOLD}Est Time:{RESET}    {est_duration:<18}  🏁 {BOLD}Batch ETA:{RESET} {eta_time:<15}{CYAN}│{RESET}")
        print(f"{CYAN}╰{'─' * box_width}╯{RESET}\n", flush=True)

    def run_batch(self, targets: list[tuple[str, str, str, str]], goal: int, batch_num: int = 1) -> tuple[int, float]:
        """Executes following for the target list with real-time progress bar and role tags."""
        if not targets:
            print(f"{YELLOW}[!] No candidate accounts available.{RESET}", flush=True)
            return 0, 0.0

        self.print_batch_dashboard(goal, batch_num)

        success_count = 0
        start_time = time.time()
        is_interactive = sys.stdout.isatty()

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

                print(status_header, flush=True)
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
                        print(f" {YELLOW}[DRY-RUN]{RESET}", flush=True)
                    else:
                        now_time = datetime.now().strftime("%H:%M:%S")
                        print(f" {GREEN}✓ Followed!{RESET} {DIM}(Logged at {now_time}){RESET}", flush=True)
                        print(f"    {DIM}↳ 🔗 https://github.com/{username}  [Saved in follows.log]{RESET}", flush=True)
                else:
                    print(f" {RED}✗ Skipped{RESET}", flush=True)

                print(flush=True)

                if success_count < goal and self.delay > 0:
                    time.sleep(self.delay)

        except KeyboardInterrupt:
            print(f"\n{YELLOW}⚠️  Session paused by user (Ctrl+C).{RESET}", flush=True)

        batch_elapsed = time.time() - start_time
        update_daily_state(success_count)
        return success_count, batch_elapsed


# Alias for backwards compatibility
KurdishBot = AutoFollowerBot


def sleep_with_countdown(seconds: float, next_run_time_str: str):
    """Sleeps for break duration with a live on-screen countdown timer."""
    end_time = time.time() + seconds
    is_interactive = sys.stdout.isatty()
    try:
        while time.time() < end_time:
            rem = max(0, int(end_time - time.time()))
            dur_str = format_duration(rem)
            if is_interactive:
                sys.stdout.write(
                    f"\r  {CYAN}☕ Resting account... Next batch at {BOLD}{WHITE}{next_run_time_str}{RESET}{CYAN} "
                    f"│ Countdown: {YELLOW}{BOLD}{dur_str}{RESET}  "
                )
                sys.stdout.flush()
                time.sleep(1)
            else:
                # Log periodically in background every 5 minutes
                if rem % 300 == 0 or rem == int(seconds):
                    print(f"  ☕ Resting account... Next batch at {next_run_time_str} │ Remaining: {dur_str}", flush=True)
                time.sleep(1)
        print("\n", flush=True)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}⚠️  Break cancelled by user.{RESET}", flush=True)
        raise


def run_autopilot_cycle(bot: AutoFollowerBot, batch_size: int = DEFAULT_BATCH_SIZE, break_hours: float = DEFAULT_BREAK_HOURS):
    """
    Continuous Auto-Pilot Cycle:
    1. Discovers and follows verified Software Engineers, Software Developers, and Backend Developers worldwide.
    2. Rests 30 minutes to clear GitHub hourly rate limits safely.
    3. Repeats automatically 24/7.
    """
    break_seconds = int(break_hours * 3600)
    batch_num = 1
    total_session_followed = 0

    gender_label = "GIRLS ONLY" if bot.gender_filter in ("female", "girl", "girls") else (
        "BOYS ONLY" if bot.gender_filter in ("male", "boy", "boys") else "ALL (BOYS & GIRLS)"
    )

    break_text = f"{int(break_hours * 60)} Minutes" if break_hours < 1 else f"{break_hours:g} Hours"

    box_width = 68
    print(f"\n{GREEN}╭{'─' * box_width}╮{RESET}")
    title = f"🚀 DEVELOPER AUTO-PILOT ACTIVATED ({break_text.upper()} BREAK) 🚀"
    print(f"{GREEN}│{BOLD}{title:^{box_width}}{RESET}{GREEN}│{RESET}")
    print(f"{GREEN}├{'─' * box_width}┤{RESET}")
    print(f"{GREEN}│{RESET}  • Scope:        {bot.target_scope.capitalize()} Tech Devs [{gender_label}]{' ' * max(0, box_width - len(gender_label) - len(bot.target_scope) - 30)}{GREEN}│{RESET}")
    print(f"{GREEN}│{RESET}  • Tech Roles:   Software Engineers, Software Developers, Backend Devs{' ' * max(0, box_width - 72)}{GREEN}│{RESET}")
    print(f"{GREEN}│{RESET}  • Batch Size:   {batch_size} developers per cycle{' ' * max(0, box_width - len(str(batch_size)) - 36)}{GREEN}│{RESET}")
    print(f"{GREEN}│{RESET}  • Rest Break:   {break_text} (Resets GitHub rate limits){' ' * max(0, box_width - len(break_text) - 43)}{GREEN}│{RESET}")
    print(f"{GREEN}│{RESET}  • Stop:         Press {RED}Ctrl+C{RESET} or run ./stop.sh to exit{' ' * max(0, box_width - 49)}{GREEN}│{RESET}")
    print(f"{GREEN}╰{'─' * box_width}╯{RESET}\n", flush=True)

    while True:
        candidates = bot.scan_developers(goal=batch_size)
        if not candidates:
            print(f"{YELLOW}[!] No candidate accounts available right now. Resting {break_text} before next search...{RESET}", flush=True)
        else:
            followed, elapsed = bot.run_batch(candidates, goal=batch_size, batch_num=batch_num)
            total_session_followed += followed

            bot.refresh_user_stats()
            current_following = bot.user_stats.get("following", 0)

            # Batch Summary Card
            box_width = 68
            print(f"\n{GREEN}╭{'─' * box_width}╮{RESET}")
            title = f"🎉 BATCH #{batch_num} COMPLETED ({followed}/{batch_size} FOLLOWED) 🎉"
            print(f"{GREEN}│{BOLD}{title:^{box_width}}{RESET}{GREEN}│{RESET}")
            print(f"{GREEN}├{'─' * box_width}┤{RESET}")
            print(f"{GREEN}│{RESET}  ✓ {BOLD}Followed in This Batch:{RESET}  {followed} developers{' ' * max(0, box_width - len(str(followed)) - 37)}{GREEN}│{RESET}")
            print(f"{GREEN}│{RESET}  🌟 {BOLD}Total in Auto-Pilot:{RESET}     {total_session_followed} developers{' ' * max(0, box_width - len(str(total_session_followed)) - 35)}{GREEN}│{RESET}")
            print(f"{GREEN}│{RESET}  🔄 {BOLD}Current Total Following:{RESET} {current_following} accounts{' ' * max(0, box_width - len(str(current_following)) - 34)}{GREEN}│{RESET}")
            print(f"{GREEN}│{RESET}  ⏱️  {BOLD}Batch Time Elapsed:{RESET}     {format_duration(elapsed)}{' ' * max(0, box_width - len(format_duration(elapsed)) - 32)}{GREEN}│{RESET}")
            print(f"{GREEN}╰{'─' * box_width}╯{RESET}\n", flush=True)

        # Calculate exact wakeup time for break
        next_wake_time = time.time() + break_seconds
        next_wake_str = time.strftime("%I:%M:%S %p", time.localtime(next_wake_time))

        box_width = 68
        print(f"{CYAN}╭{'─' * box_width}╮{RESET}")
        title = f"☕ {break_text.upper()} REST BREAK (GITHUB ANTI-BAN SHIELD)"
        print(f"{CYAN}│{BOLD}{title:^{box_width}}{RESET}{CYAN}│{RESET}")
        print(f"{CYAN}├{'─' * box_width}┤{RESET}")
        print(f"{CYAN}│{RESET}  🛡️  {BOLD}Rest Duration:{RESET}  {break_text} (Resets hourly abuse detection){' ' * max(0, box_width - len(break_text) - 49)}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  ⏰  {BOLD}Next Batch At:{RESET}  {next_wake_str}{' ' * max(0, box_width - len(next_wake_str) - 25)}{CYAN}│{RESET}")
        print(f"{CYAN}│{RESET}  💾  {BOLD}Status:{RESET}         History saved. Zero duplicate risk.{' ' * max(0, box_width - 50)}{CYAN}│{RESET}")
        print(f"{CYAN}╰{'─' * box_width}╯{RESET}\n", flush=True)

        try:
            sleep_with_countdown(break_seconds, next_wake_str)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}[!] Auto-pilot stopped by user. Progress saved!{RESET}", flush=True)
            break

        batch_num += 1


def show_follow_log(bot: AutoFollowerBot, limit: int = 30):
    """Displays a clean formatted table of followed users from history and log file."""
    total_followed = len(bot.history.history)
    records = bot.history.records
    total_records = len(records)

    box_width = 82
    print(f"\n{CYAN}╭{'─' * box_width}╮{RESET}")
    title = "📜 DEVELOPER FOLLOW LOG & HISTORY"
    print(f"{CYAN}│{BOLD}{title:^{box_width}}{RESET}{CYAN}│{RESET}")
    print(f"{CYAN}├{'─' * box_width}┤{RESET}")
    print(f"{CYAN}│{RESET}  • Total Accounts in Database:  {BOLD}{total_followed}{RESET}{' ' * max(0, box_width - len(str(total_followed)) - 35)}{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  • Detailed Follow Log Records: {BOLD}{total_records}{RESET}{' ' * max(0, box_width - len(str(total_records)) - 35)}{CYAN}│{RESET}")
    print(f"{CYAN}│{RESET}  • Activity Log File:           {BOLD}{str(bot.history.log_path.name)}{RESET}{' ' * max(0, box_width - len(str(bot.history.log_path.name)) - 35)}{CYAN}│{RESET}")
    print(f"{CYAN}╰{'─' * box_width}╯{RESET}\n", flush=True)

    if records:
        display_records = list(records[-limit:])
        display_records.reverse()

        print(f"{BOLD}{'#':<4} {'Date & Time':<20} {'Developer':<20} {'Role':<24} {'Gender':<14}{RESET}")
        print(f"{DIM}{'─' * box_width}{RESET}")

        for idx, r in enumerate(display_records, 1):
            ts = r.get("timestamp", "Unknown")
            uname = f"@{r.get('username', '')}"
            role = r.get("role", "Developer")
            gender = r.get("gender", "")
            url = r.get("url", f"https://github.com/{r.get('username', '')}")
            loc = r.get("location", "")

            print(f"{idx:02d}.  {ts:<20} {BOLD}{uname:<20}{RESET} {GREEN}{role:<24}{RESET} {CYAN}{gender:<14}{RESET}")
            print(f"     {DIM}↳ 🔗 {url}  [📍 {loc}]{RESET}")

        print(f"\n{GREEN}✓ Showing {len(display_records)} most recent logged follows (out of {total_records} records).{RESET}\n", flush=True)
    elif total_followed > 0:
        usernames = sorted(list(bot.history.history), reverse=True)[:limit]
        print(f"{YELLOW}Showing last {len(usernames)} followed usernames from database (total: {total_followed}):{RESET}\n")
        for i, u in enumerate(usernames, 1):
            print(f"  {DIM}{i:02d}.{RESET} {BOLD}@{u:<24}{RESET} 🔗 https://github.com/{u}")
    else:
        print(f"{YELLOW}[!] No follow records logged yet. Run Auto-Pilot or a batch to start following!{RESET}\n", flush=True)

    print(f"{DIM}📁 Full live log file is saved to: {bot.history.log_path.resolve()}{RESET}\n", flush=True)

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
    """Lets user select their preferred gender filter."""
    print(f"\n👥 {BOLD}Choose Developer Gender Filter:{RESET}")
    print(f"  1) {CYAN}🌟 All Developers (Boys & Girls){RESET} [Default - Recommended]")
    print(f"  2) {MAGENTA}👩 Girls Only{RESET} (Female Software Engineers, Software Devs, Backend Devs)")
    print(f"  3) {BLUE}👨 Boys Only{RESET}  (Male Software Engineers, Software Devs, Backend Devs)")

    choice = input("\nEnter choice [1-3, default 1]: ").strip()
    if choice == "2":
        return "female"
    elif choice == "3":
        return "male"
    return "all"


def ask_target_scope() -> str:
    """Lets user select target tech community scope."""
    print(f"\n🎯 {BOLD}Choose Target Developer Scope:{RESET}")
    print(f"  1) {GREEN}🌍 Global Tech Developers (Software Engineers, Software Developers & Backend Devs Worldwide){RESET} [Default - Recommended]")
    print(f"  2) {CYAN}💻 Software Engineers Only (Systems, Infrastructure & Senior SWEs Worldwide){RESET}")
    print(f"  3) {WHITE}💻 Software Developers Only (Fullstack, App & Software Developers Worldwide){RESET}")
    print(f"  4) {YELLOW}⚡ Backend Specialists Only (Python, Golang, Node.js, Java, Rust, PHP, APIs){RESET}")
    print(f"  5) {MAGENTA}☀️ Kurdish Developers Only (Kurdistan, Erbil, Sulaymaniyah, Duhok, Kirkuk){RESET}")
    print(f"  6) 🌐 All Combined (Global Software Engineers, Developers, Backend + Regional Hubs){RESET}")

    choice = input("\nEnter choice [1-6, default 1]: ").strip()
    if choice == "2":
        return "software-engineer"
    elif choice == "3":
        return "software-developer"
    elif choice == "4":
        return "backend"
    elif choice == "5":
        return "kurdish"
    elif choice == "6":
        return "all"
    return "global"


def main():
    parser = argparse.ArgumentParser(description="🚀 Developer Auto-Pilot Pro (Software Engineers, Software Developers & Backend Developers)")
    parser.add_argument("--auto", action="store_true", help="Start continuous Auto-Pilot 24/7 (Follow batch -> 30m break -> Repeat)")
    parser.add_argument("--target", "--scope", default="global", choices=["global", "software-engineer", "swe", "software-developer", "dev", "backend", "kurdish", "all"], help="Target developer audience (default: global)")
    parser.add_argument("--role", default="all", choices=["all", "software-engineer", "software-developer", "backend", "fullstack"], help="Filter by specific developer role (default: all)")
    parser.add_argument("--gender", default="all", choices=["all", "female", "girl", "girls", "male", "boy", "boys"], help="Filter by gender (girl/boy/all)")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help=f"Follows per batch (default: {DEFAULT_BATCH_SIZE})")
    parser.add_argument("--break-hours", type=float, default=DEFAULT_BREAK_HOURS, help=f"Break hours between batches (default: {DEFAULT_BREAK_HOURS})")
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY, help=f"Seconds between follows (default: {DEFAULT_DELAY})")
    parser.add_argument("--once", action="store_true", help="Run only one single batch now and exit")
    parser.add_argument("--reset-cursors", action="store_true", help="Reset all search pagination cursors back to page 1")
    parser.add_argument("--log", nargs="?", const=30, type=int, help="Show log of followed users (default: last 30)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without making actual follow requests")

    args = parser.parse_args()

    token = get_token()
    bot = AutoFollowerBot(
        token,
        dry_run=args.dry_run,
        delay=args.delay,
        gender_filter=args.gender,
        target_scope=args.target,
        role_filter=args.role
    )

    if args.reset_cursors:
        bot.cursors.reset_all()
        print(f"{GREEN}✓ Successfully reset all search cursors to page 1.{RESET}")
        return

    user_info = bot.verify_account()
    if not user_info:
        print(f"{RED}[!] Could not verify GitHub account. Please check network connection and GITHUB_TOKEN in {ENV_PATH}.{RESET}")
        sys.exit(1)

    print(f"{GREEN}{BOLD}✓ Authenticated as @{user_info.get('login')}{RESET}")
    print(f"  Followers: {user_info.get('followers')} | Following: {user_info.get('following')}\n", flush=True)

    if args.log is not None:
        show_follow_log(bot, limit=args.log)
        return

    # Sync following list
    bot.preload_current_following()

    if args.auto:
        run_autopilot_cycle(bot, batch_size=args.batch_size, break_hours=args.break_hours)
    elif args.once:
        candidates = bot.scan_developers(goal=args.batch_size)
        bot.run_batch(candidates, goal=args.batch_size, batch_num=1)
    else:
        while True:
            break_menu_text = f"{int(args.break_hours * 60)}-Minute" if args.break_hours < 1 else f"{args.break_hours:g}-Hour"
            print(f"{BOLD}Choose Operation Mode:{RESET}")
            print(f"  {CYAN}1) 🔄 Start 24/7 Auto-Pilot (Software Engineers, Software Developers & Backend Developers Worldwide){RESET} [Default - Press Enter]")
            print(f"  {YELLOW}2) ⚡ Run Single Batch of {args.batch_size} Now & Exit{RESET}")
            print(f"  {GREEN}3) 🎯 Choose Target Scope (Global Tech Devs, Software Engineers, Backend Specialists, Kurdish, All){RESET}")
            print(f"  {MAGENTA}4) 📜 View Follow Log & History (Show users you have followed){RESET}")
            print(f"  5) 🔄 Reset Search Cursors (Start searches fresh from page 1)")
            print(f"  6) 🛑 Exit")

            mode_choice = input("\nEnter choice [1-6, default 1]: ").strip()
            if mode_choice == "6":
                print("Exited.")
                return
            elif mode_choice == "5":
                bot.cursors.reset_all()
                print(f"{GREEN}✓ All search cursors reset to page 1.{RESET}\n")
                continue
            elif mode_choice == "4":
                show_follow_log(bot)
                try:
                    input(f"\n{DIM}Press Enter to return to main menu...{RESET}")
                except (EOFError, KeyboardInterrupt):
                    return
                print()
                continue
            elif mode_choice == "3":
                bot.target_scope = ask_target_scope()
                print(f"{GREEN}✓ Target scope set to: {bot.target_scope.upper()}{RESET}\n")
                continue

            # Choose Gender & Scope
            bot.gender_filter = ask_gender()

            if mode_choice == "2":
                candidates = bot.scan_developers(goal=args.batch_size)
                bot.run_batch(candidates, goal=args.batch_size, batch_num=1)
                break
            else:
                run_autopilot_cycle(bot, batch_size=args.batch_size, break_hours=args.break_hours)
                break


if __name__ == "__main__":
    main()
