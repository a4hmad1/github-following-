<div align="center">

# ⚡ GitHub Network Expander Pro

**A blazing-fast, intelligent, and resilient CLI automation tool for GitHub networking in 250-account batches.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub license](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/a4hmad1/github-following-?style=for-the-badge&logo=github)](https://github.com/a4hmad1/github-following-/stargazers)
[![GitHub Followers](https://img.shields.io/github/followers/a4hmad1?style=for-the-badge&logo=github&label=Follow%20%40a4hmad1)](https://github.com/a4hmad1)

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-batch-workflow">Batch Workflow</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-token-setup">Token Setup</a> •
  <a href="#-usage-guide">Usage Guide</a> •
  <a href="#-rate-limit--safety-shield">Safety Shield</a>
</p>

</div>

---

## 🚀 Overview

**GitHub Network Expander Pro** is a high-performance Python utility engineered to help developers grow their open-source network efficiently. Designed with a **250-account batch workflow**, unified styling, live percentage progress, in-memory pre-caching, and intelligent rate-limit backoff, it provides maximum speed with total reliability.

---

## ✨ Key Features

- **⚡ Turbo Engine (~150 Follows/min)**: Reuses HTTP keep-alive connection pooling (`requests.adapters.HTTPAdapter`) to eliminate TLS handshake overhead.
- **👩/👨 Intelligent Gender Filter**: Filter profiles to target **Girls / Female** or **Boys / Male** by scanning profile pronouns (`she/her`, `he/him`), bio keywords, real names, and usernames.
- **🔄 Smart 250 Batch Workflow**: Automatically follows 250 fresh accounts, displays completion stats, and prompts you to continue with the next 250 or stop.
- **🔍 Live Pre-Scan Engine**: Actively scans and filters candidate lists before following to guarantee 100% brand-new accounts.
- **📊 Unified Progress Dashboard**: Sleek Cyan & Emerald Green theme with live percentage progress bar, remaining countdown timer, and exact finishing ETA.
- **🧠 In-Memory Smart Cache**: Bulk pre-syncs your current following list into memory at launch. Eliminates redundant check requests, doubling execution speed.
- **🛡️ Adaptive Rate-Limit Shield**: Actively inspects response headers (`x-ratelimit-reset`, `Retry-After`). Pauses automatically during rate limit cooldowns and resumes without dying.
- **💾 Safe Pause & Auto-Resume**: Tracks every processed user in `followed_history.json`. Stop at any time with `Ctrl+C` and restart without duplicate follows.
- **🔗 Smart URL Cleaning**: Paste raw input like `https://github.com/google`, `@microsoft`, or `owner/repo`—the tool automatically extracts clean identifiers.

---

## 🔄 Batch Workflow

```text
╭──────────────────────────────────────────────────────────────╮
│               ⚡ BATCH #1 — TARGET: 250 FOLLOWS ⚡            │
├──────────────────────────────────────────────────────────────┤
│  👤 Operator:  @a4hmad1          👥 Followers: 26             │
│  🎯 Source:    @google           🔄 Following: 537            │
│  🎯 Batch Goal:250 accounts      ⚡ Speed:     ~120/min       │
│  ⏱️  Est Time:  02m 05s          🏁 Batch ETA: 08:55 PM       │
╰──────────────────────────────────────────────────────────────╯

[████████████████░░░░]  78.4% (196/250) │ ⏱️ Rem: 00m 27s │ 🏁 ETA: 08:55 PM
  → Following @johndoe... ✓ Followed!

╭──────────────────────────────────────────────────────────────╮
│                 🎉 BATCH #1 COMPLETED (250/250) 🎉           │
├──────────────────────────────────────────────────────────────┤
│  ✓ Followed in Batch #1:   250 accounts                       │
│  🌟 Total in This Session: 250 accounts                       │
│  🔄 Current Total Following: 787 accounts                     │
│  ⏱️  Batch Time Elapsed:   02m 04s                            │
╰──────────────────────────────────────────────────────────────╯

What would you like to do next?
  1) 🚀 Start following NEXT 250 accounts [Press Enter]
  2) 🛑 Stop and exit session
```

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/a4hmad1/github-following-.git
cd github-following-
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Token Setup

1. Go to **[GitHub Token Settings (Classic)](https://github.com/settings/tokens)**.
2. Click **Generate new token (classic)**.
3. Select **ONLY** the scope:
   - `[x] user:follow` (Allows following and unfollowing users).
4. Create `.env` from template:
```bash
cp .env.example .env
```
5. Put your token in `.env`:
```env
GITHUB_TOKEN=ghp_yourTokenHere
```

---

## 💻 Usage Guide

### 1. Interactive Menu Mode
Run without flags to open the interactive command console:
```bash
python3 autofollow.py
```
```text
Choose Target Source:
  1) Follow followers of a company or organization (e.g. google, microsoft, meta)
  2) Search active developers by keywords (e.g. location:Iraq, language:python)
  3) Follow contributors of a repository (e.g. facebook/react, flutter/flutter)
  4) Enter specific usernames manually
  5) Exit
```

---

### 2. Command-Line Direct Modes

#### A. Target Company / Organization Followers
```bash
# Follow followers of Google in 250 batches
python3 autofollow.py --user google

# Follow followers of Microsoft at turbo speed
python3 autofollow.py --user microsoft --turbo
```

#### B. Search Active Developers by Tech Stack or Location
```bash
# Target Python developers in a specific country
python3 autofollow.py --search "location:Iraq language:python"

# Target developers in follow-back communities
python3 autofollow.py --search "follow-back"
```

#### C. Follow Active Contributors of a Repository
```bash
python3 autofollow.py --repo facebook/react
python3 autofollow.py --repo flutter/flutter
```

#### D. Filter by Gender (Girls or Boys)
```bash
# Follow ONLY girls/female developers from Google
python3 autofollow.py --user google --gender girl

# Follow ONLY girls/female developers from a search query
python3 autofollow.py --search "location:Iraq" --gender girl

# Follow ONLY boys/male developers
python3 autofollow.py --user microsoft --gender boy
```

#### E. Dry-Run Mode (Simulation)
Preview targets without sending real follow requests:
```bash
python3 autofollow.py --user google --dry-run
```

---

## 🛡️ Rate Limit & Safety Shield

> [!IMPORTANT]
> **GitHub Anti-Abuse Compliance**
> - Standard personal access tokens allow up to **5,000 requests per hour**.
> - The **250-account batch workflow** provides natural checkpoints to monitor your network growth responsibly.
> - Automatic backoff on HTTP `403` / `429` secondary rate limits ensures your account stays safe.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<div align="center">

Developed with ❤️ by [**@a4hmad1**](https://github.com/a4hmad1)

⭐ **Star this repository if you find it helpful!**

</div>
