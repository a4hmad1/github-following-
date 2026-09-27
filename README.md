<div align="center">

# ☀️ Kurdish Developer Auto-Pilot (GitHub Compliance Edition)

**An intelligent, GitHub rule-compliant automation tool that follows Kurdish developers in safe 50-account batches separated by 2-hour rest breaks.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub license](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/a4hmad1/github-following-?style=for-the-badge&logo=github)](https://github.com/a4hmad1/github-following-/stargazers)
[![GitHub Followers](https://img.shields.io/github/followers/a4hmad1?style=for-the-badge&logo=github&label=Follow%20%40a4hmad1)](https://github.com/a4hmad1)

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-why-the-2-hour-break-matters">GitHub Rules & 2h Break</a> •
  <a href="#-how-auto-pilot-works">Auto-Pilot Workflow</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage-guide">Usage Guide</a>
</p>

</div>

---

## 🚀 Overview

**Kurdish Developer Auto-Pilot** is engineered specifically to respect **GitHub's Rate Limits & Anti-Abuse Policies**. 

Instead of aggressively following hundreds of accounts all at once (which triggers GitHub spam alarms and secondary rate limits), the tool operates on an intelligent **Duty-Cycle Auto-Pilot**:
- Follows a safe batch of **50 fresh Kurdish developers** (~1 minute).
- Takes a mandatory **2-hour rest break** to completely reset GitHub's rolling 60-minute window.
- Shows a live countdown timer during the break.
- Automatically wakes up after 2 hours, discovers the next 50 Kurdish developers, and repeats all day.

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

### 1. Start Auto-Pilot (Follow 50 → 2-Hour Break → Repeat)
```bash
python3 autofollow.py --auto
```
*(Runs continuously: follows 50 Kurdish developers, counts down 2 hours on screen, then automatically starts the next batch).*

---

### 2. Run in Background Permanently (Headless)
To keep it running 24/7 on your Linux machine (even after closing terminal):
```bash
nohup python3 /home/ahmad/github-auto-follower/autofollow.py --auto > autopilot.log 2>&1 &
```
To check live countdown and progress anytime:
```bash
tail -f autopilot.log
```

---

### 3. Customize Batch Size or Break Hours
```bash
# Follow 60 accounts, rest 2 hours:
python3 autofollow.py --auto --batch-size 60 --break-hours 2

# Follow 50 accounts, rest 3 hours:
python3 autofollow.py --auto --batch-size 50 --break-hours 3
```

---

### 4. Run a Single Batch Right Now (No Loop)
```bash
python3 autofollow.py --once
```

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<div align="center">

Developed with ❤️ by [**@a4hmad1**](https://github.com/a4hmad1)

☀️ **Dedicated to the Kurdish Developer Community** ☀️

</div>
