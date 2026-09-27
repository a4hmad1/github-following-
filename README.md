<div align="center">

# ☀️ Kurdish Developer Auto-Pilot Pro (Tech Roles & Gender Filter)

**An intelligent, GitHub rule-compliant automation tool that discovers and follows verified Kurdish developers (Fullstack, Backend, Software Engineers, Laravel, Seniors) in safe 50-account batches separated by 2-hour rest breaks, with interactive Gender Selection (Girls / Boys / All).**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub license](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/a4hmad1/github-following-?style=for-the-badge&logo=github)](https://github.com/a4hmad1/github-following-/stargazers)
[![GitHub Followers](https://img.shields.io/github/followers/a4hmad1?style=for-the-badge&logo=github&label=Follow%20%40a4hmad1)](https://github.com/a4hmad1)

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-core-features">Features</a> •
  <a href="#-why-the-2-hour-break-matters">GitHub Rules & 2h Break</a> •
  <a href="#-how-auto-pilot-works">Auto-Pilot Workflow</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage-guide">Usage Guide</a>
</p>

</div>

---

## 🚀 Overview

**Kurdish Developer Auto-Pilot Pro** is designed specifically to expand your developer network across Kurdistan while strictly adhering to **GitHub's Rate Limits & Anti-Abuse Policies**.

Instead of aggressively following accounts all at once (which triggers GitHub spam alarms and secondary rate limits), the tool operates on an intelligent **Duty-Cycle Auto-Pilot**:
- **Verified Tech Roles**: Inspects candidate profiles to verify they are **Fullstack, Backend, Software Engineers, Laravel, or Senior Developers**.
- **Gender Selection**: Choose **Girls Only**, **Boys Only**, or **All Developers** (scans pronouns, bio signals, Kurdish first names, and usernames).
- **Safe Batch Size**: Follows **250 verified Kurdish developers** per cycle (~4 minutes).
- **30-Minute Anti-Ban Break**: Automatically takes a **30-minute rest break** with a live countdown timer to completely clear GitHub's rolling window.
- **Continuous 24/7 Cycle**: Automatically wakes up after 30 minutes, discovers the next batch of 250, and repeats safely.
- **Run in Cloud (Computer Off)**: Includes a **GitHub Actions 24/7 workflow** that runs in GitHub's cloud even when your personal computer is shut down!
- **Zero Duplicate Risk ("Not Again")**: Pre-caches your existing following list and maintains a local database to guarantee no account is ever followed twice.

---

## 🛡️ Why the 2-Hour Break Matters (GitHub Rules Protection)

| Risk on GitHub | Without 2-Hour Break | With Kurdish Auto-Pilot (2h Break) |
| :--- | :--- | :--- |
| **Secondary Abuse Limit** | ⚠️ Triggers `403 Secondary Rate Limit` within minutes | ✅ **100% avoided** — 2-hour rest clears the write buffer |
| **Hourly Rolling Window** | ⚠️ Exceeds max write actions per 60-minute window | ✅ **Fully resets** the hourly API quota every single cycle |
| **Account Shadowban Risk** | ⚠️ High risk of automated bot detection | ✅ **Zero risk** — looks like natural developer networking |
| **Duplicate Follows** | ⚠️ Wastes requests on already-followed users | ✅ **Zero duplicates** — in-memory cache pre-filters everyone |

---

## 🔄 Auto-Pilot Workflow

```text
╭──────────────────────────────────────────────────────────────╮
│         ☀️ BATCH #1 — GOAL: 50 KURDISH DEVELOPERS ☀️         │
├──────────────────────────────────────────────────────────────┤
│  👤 Operator:  @a4hmad1           👥 Followers: 27             │
│  📍 Target:    Kurdish Devs      🔄 Following: 538            │
│  🎯 Batch Goal:50 accounts       ⚡ Speed:     60 follows/min │
│  ⏱️  Est Time:  00m 50s           🏁 Batch ETA: 09:20 PM       │
╰──────────────────────────────────────────────────────────────╯

[████████████████░░░░]  78.4% (39/50) │ ⏱️ Rem: 00m 11s │ 🏁 ETA: 09:20 PM
  → Following @PawanOsman [📍 Sulaymaniyah]... ✓ Followed!
  → Following @HekarNizarki [📍 Duhok]... ✓ Followed!
  → Following @ShahramShakiba [📍 Erbil]... ✓ Followed!

╭──────────────────────────────────────────────────────────────╮
│         ☕ 2-HOUR REST BREAK (GITHUB ANTI-BAN SHIELD)         │
├──────────────────────────────────────────────────────────────┤
│  🛡️  Rest Duration:  2.0 Hours (Resets hourly abuse detection) │
│  ⏰  Next Batch At:  11:20:00 PM                             │
│  💾  Status:         History saved. Zero duplicate risk.     │
╰──────────────────────────────────────────────────────────────╯

  ☕ Resting account... Next batch at 11:20:00 PM │ Countdown: 01h 59m 45s
```

---

## 📦 Installation

```bash
git clone https://github.com/a4hmad1/github-following-.git
cd github-following-
pip install -r requirements.txt
```

### Configure Your Token:
```bash
cp .env.example .env
```
Add your token inside `.env`:
```env
GITHUB_TOKEN=ghp_yourTokenHere
```

---

## 💻 Usage Guide

### 1. Interactive Daily Start (Recommended)
Simply run:
```bash
python3 autofollow.py
```
You will be prompted to:
1. Choose mode: **Auto-Pilot** (250 follows → 30m break → repeat) or **Single Batch**.
2. Select gender filter:
   - `1) 🌟 All Kurdish Developers (Boys & Girls)`
   - `2) 👩 Kurdish Girls Only` (Female Fullstack / Backend / Software Engineers)
   - `3) 👨 Kurdish Boys Only` (Male Fullstack / Backend / Software Engineers)

---

### 2. Direct Auto-Pilot Commands
You can also run directly with command-line flags:

```bash
# Follow 250 Kurdish Girls (30-minute break cycle):
python3 autofollow.py --auto --gender female

# Follow 250 Kurdish Boys (30-minute break cycle):
python3 autofollow.py --auto --gender male

# Follow 250 All Kurdish Developers (30-minute break cycle):
python3 autofollow.py --auto --gender all
```

---

### 3. Run With Computer Shut Down (GitHub Actions Cloud 24/7)
If you close your terminal and **turn off/shut down your computer**, local software cannot run. 
To keep the tool following Kurdish developers **24/7 in the cloud without your computer**:

1. Go to your GitHub repository: [**`a4hmad1/github-following-`**](https://github.com/a4hmad1/github-following-)
2. Click **Settings** ➔ **Secrets and variables** ➔ **Actions**
3. Click **New repository secret**:
   - Name: `GH_PAT`
   - Value: Paste your GitHub Personal Access Token (`ghp_...`)
4. The workflow in [`.github/workflows/autopilot.yml`](file:///home/ahmad/github-auto-follower/.github/workflows/autopilot.yml) will automatically run every **30 minutes** in GitHub's cloud, follow 250 Kurdish developers, and save your follow history back to the repo!

---

### 4. Run in Background on Local Machine (Headless)
If your computer stays on and you just want to close the terminal:
```bash
nohup python3 /home/ahmad/github-auto-follower/autofollow.py --auto > autopilot.log 2>&1 &
```
To check live countdown and progress anytime:
```bash
tail -f autopilot.log
```

---

### 5. View Follow Log & Check Followed Users
To view recently followed developers with timestamps, roles, gender tags, and profile URLs:
```bash
# View last 30 followed developers:
python3 autofollow.py --log

# View last 50 followed developers:
python3 autofollow.py --log 50
```
Or open the menu with `python3 autofollow.py` and select **`3) 📜 View Follow Log & History`**. You can also enter any username to verify if they have already been followed!

All follows are also logged in plain text in **`follows.log`**:
```text
[2026-09-27 21:25:01] FOLLOWED: @dalalkurdish       | URL: https://github.com/dalalkurdish    | Role: Frontend Developer     | Gender: 👩 Female (name 'Dalal') | Location: Kurdistan • Dev
```

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<div align="center">

Developed with ❤️ by [**@a4hmad1**](https://github.com/a4hmad1)

☀️ **Dedicated to the Kurdish Developer Community** ☀️

</div>
