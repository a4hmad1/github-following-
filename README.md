<div align="center">

# ☀️ Kurdish Developer Auto-Follow Pro

**An automated, intelligent CLI tool to discover and connect with Kurdish developers across GitHub.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub license](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/a4hmad1/github-following-?style=for-the-badge&logo=github)](https://github.com/a4hmad1/github-following-/stargazers)
[![GitHub Followers](https://img.shields.io/github/followers/a4hmad1?style=for-the-badge&logo=github&label=Follow%20%40a4hmad1)](https://github.com/a4hmad1)

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-kurdish-discovery-engine">Kurdish Discovery</a> •
  <a href="#-daily-automation">Daily Automation</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-usage-guide">Usage Guide</a>
</p>

</div>

---

## 🚀 Overview

**Kurdish Developer Auto-Follow Pro** is an open-source utility built exclusively to connect you with Kurdish developers (both boys and girls) worldwide. 

Instead of manual searches, it automatically scans GitHub across all Kurdish cities, regions, bios, and communities—following **250 brand-new Kurdish developers per day** while ensuring zero duplicate follows.

---

## ☀️ Kurdish Discovery Engine

The tool automatically searches and cycles through 18+ Kurdish developer vectors:

- 📍 **Cities & Regions**: Erbil (Hawler), Sulaymaniyah (Slemani), Duhok, Kirkuk, Halabja, Zakho, Kalar, Ranya, Diyarbakir, Mahabad, Sanandaj, Qamishlo.
- 🏷️ **Bio & Community Keywords**: `Kurdistan`, `Kurdish`, `kurd`, `کوردستان`, `کورد`.
- 🔍 **Freshness Scanner**: Automatically filters out accounts you already follow and saves page positions in `page_cursor.json` so you always find new developers.

---

## 🔄 Daily Batch & 24h Daemon Workflow

```text
╭──────────────────────────────────────────────────────────────╮
│           ☀️ KURDISH DEVELOPER NETWORK EXPANDER ☀️           │
├──────────────────────────────────────────────────────────────┤
│  👤 Operator:  @a4hmad1           👥 Followers: 27             │
│  📍 Target:    Kurdish Devs      🔄 Following: 537            │
│  🎯 Daily Goal:250 Kurdish Devs  ⚡ Speed:     ~120/min       │
│  ⏱️  Est Time:  02m 05s           🏁 Batch ETA: 09:15 PM       │
╰──────────────────────────────────────────────────────────────╯

[████████████████░░░░]  78.4% (196/250) │ ⏱️ Rem: 00m 27s │ 🏁 ETA: 09:15 PM
  → Following @PawanOsman [📍 Sulaymaniyah]... ✓ Followed!
  → Following @HekarNizarki [📍 Duhok]... ✓ Followed!
  → Following @ShahramShakiba [📍 Erbil]... ✓ Followed!

╭──────────────────────────────────────────────────────────────╮
│     ☀️ TODAY'S BATCH COMPLETED (250/250 NEW KURDISH DEVS) ☀️ │
├──────────────────────────────────────────────────────────────┤
│  ✓ Kurdish Devs Followed Today: 250 accounts                  │
│  🔄 Current Total Following:     787 accounts                 │
│  ⏱️  Time Elapsed:                 02m 04s                     │
│  💾 Saved To:                     followed_history.json       │
╰──────────────────────────────────────────────────────────────╯
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
Edit `.env`:
```env
GITHUB_TOKEN=ghp_yourTokenHere
```

---

## 💻 Usage Guide

### 1. Run Today's Batch (250 Kurdish Devs)
Simply run the script and press **Enter**:
```bash
python3 autofollow.py
```
*(Finds 250 fresh Kurdish developers across Erbil, Sulaymaniyah, Duhok, etc., and follows them safely).*

---

### 2. Automatic Daily Daemon Mode (Continuous Every 24 Hours)
Run continuously in the background—it will follow 250 Kurdish developers, sleep for 24 hours, and repeat automatically every day:
```bash
python3 autofollow.py --daily
```

---

### 3. Run in the Background (Headless)
If you want to leave it running on your machine:
```bash
nohup python3 autofollow.py --daily > daily.log 2>&1 &
```
To check live logs:
```bash
tail -f daily.log
```

---

## 🛡️ Anti-Ban & Safety Features
- **Zero Duplicate Guarantee**: Synchronizes your following list into memory at launch; you will never follow the same developer twice.
- **Safe Batch Size**: 250 follows per day stays safely within GitHub's abuse limits.
- **Auto-Cooldown Protection**: Automatically backs off if GitHub signals rate limits.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<div align="center">

Developed with ❤️ by [**@a4hmad1**](https://github.com/a4hmad1)

☀️ **Dedicated to the Kurdish Developer Community** ☀️

</div>
