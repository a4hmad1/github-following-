<div align="center">

# 🚀 Developer Auto-Pilot Pro (Software Engineers, Software Devs & Backend Devs)

**An intelligent, GitHub rule-compliant automation tool that discovers and follows verified Software Engineers, Software Developers, and Backend Developers worldwide and regionally (including Kurdish tech hubs) in safe batches separated by anti-ban rest breaks.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub license](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/a4hmad1/github-following-?style=for-the-badge&logo=github)](https://github.com/a4hmad1/github-following-/stargazers)
[![GitHub Followers](https://img.shields.io/github/followers/a4hmad1?style=for-the-badge&logo=github&label=Follow%20%40a4hmad1)](https://github.com/a4hmad1)

<p align="center">
  <a href="#-overview">Overview</a> •
  <a href="#-core-features">Features</a> •
  <a href="#-why-the-rest-break-matters">Anti-Ban Protection</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-cli-options">CLI Options</a> •
  <a href="#-cloud-247-github-actions">Cloud 24/7</a>
</p>

</div>

---

## 🚀 Overview

**Developer Auto-Pilot Pro** is designed to grow your developer network organically and steadily while strictly adhering to **GitHub's Rate Limits & Anti-Abuse Policies**.

Instead of only targeting a small localized pool that runs out of results, the tool features **Global & Regional Discovery**:
- **Target Tech Roles**: Specifically searches for and verifies **Software Engineers**, **Software Developers**, and **Backend Developers** (along with Fullstack and framework specialists).
- **Global & Regional Scopes**:
  - **`global` (Default)**: International Software Engineers, Software Developers & Backend Developers worldwide across top global tech hubs and remote talent.
  - **`software-engineer` (or `swe`)**: Core systems engineers, Senior SWEs, and lead engineers worldwide.
  - **`software-developer` (or `dev`)**: Application, web, and software developers worldwide.
  - **`backend`**: Backend specialists (Python, Golang, Node.js, Java, Rust, PHP / Laravel, C#).
  - **`kurdish`**: Dedicated Kurdish developer communities (Kurdistan, Erbil, Sulaymaniyah, Duhok, Kirkuk, Hawler, Slemani).
  - **`all`**: Combines all global software engineers, software developers, backend specialists, and regional developer pools.
- **Gender Selection**: Choose **All Developers**, **Girls Only**, or **Boys Only**.
- **Safe Batching & Rate Limiting**: Follows **250 developers** per cycle, then takes an automatic **30-minute rest break** to reset GitHub's rolling hourly rate limit.
- **Zero Duplicate Risk ("Not Again")**: Pre-caches your existing following list and maintains a local database to guarantee no account is ever followed twice.
- **Auto-Wrap & Cursor Protection**: Automatically wraps search cursors and handles rate limiting backoff so searches never get permanently stuck.

---

## 🛡️ Why the Rest Break Matters (GitHub Anti-Ban Shield)

| Risk on GitHub | Without Rest Break | With Developer Auto-Pilot (30m Break) |
| :--- | :--- | :--- |
| **Secondary Abuse Limit** | ⚠️ Triggers `403 Secondary Rate Limit` within minutes | ✅ **100% avoided** — 30-minute rest clears the write buffer |
| **Hourly Rolling Window** | ⚠️ Exceeds max write actions per 60-minute window | ✅ **Fully resets** the hourly API quota every single cycle |
| **Search API Limit** | ⚠️ Hits 30 req/min search ceiling | ✅ **Polite pacing** (1.2s delay + auto-cooldown backoff) |
| **Duplicate Follows** | ⚠️ Wastes requests on already-followed users | ✅ **Zero duplicates** — in-memory cache pre-filters everyone |

---

## ⚡ Quick Start

### 1. One-Command Background Launcher
Run:
```bash
./start.sh
```
- Automatically launches in the background and works **24/7**.
- Automatically resumes after computer reboot.
- If interactive, streams live progress until you press `Ctrl+C` (detaching cleanly while bot keeps running!).

### 2. Check Status
```bash
# View complete dashboard metrics and exit immediately:
./status.sh

# Or stream live activity in real-time:
./status.sh -f
```

### 3. Stop Bot
```bash
./stop.sh
```

---

## 💻 CLI Options

You can run `autofollow.py` directly with flexible flags:

```bash
# 1. 24/7 Auto-Pilot with default global developers (Software Engineers, Software Devs, Backend Devs):
python3 autofollow.py --auto

# 2. Target Backend Developers specifically:
python3 autofollow.py --auto --target backend

# 3. Target Software Engineers specifically:
python3 autofollow.py --auto --target software-engineer

# 4. Filter by gender (e.g. female developers):
python3 autofollow.py --auto --gender female

# 5. Run a single batch of 50 developers now and exit:
python3 autofollow.py --once --batch-size 50

# 6. Reset all search cursors back to page 1:
python3 autofollow.py --reset-cursors

# 7. View recently followed developers:
python3 autofollow.py --log 30
```

### Command-Line Arguments Reference

| Flag | Options / Default | Description |
| :--- | :--- | :--- |
| `--auto` | Flag | Runs continuous 24/7 Auto-Pilot (Batch ➔ 30m break ➔ Repeat) |
| `--target`, `--scope` | `global` (default), `backend`, `software-engineer`, `software-developer`, `kurdish`, `all` | Target audience and search queries |
| `--role` | `all` (default), `software-engineer`, `software-developer`, `backend` | Filter candidate verified role |
| `--gender` | `all` (default), `female`, `male` | Gender filter |
| `--batch-size` | `250` (default) | Number of developers to follow per batch |
| `--break-hours` | `0.5` (default: 30 minutes) | Rest duration between batches in hours |
| `--delay` | `1.0` (default: 1.0s) | Delay between follow requests |
| `--once` | Flag | Runs one single batch and exits |
| `--reset-cursors` | Flag | Resets all search pagination cursors to page 1 |
| `--log [N]` | `30` (default) | Displays recent followed developers from log |
| `--dry-run` | Flag | Simulates discovery and inspection without following |

---

## ☁️ Cloud 24/7 (GitHub Actions)

If you turn off or shut down your personal computer, GitHub Actions can continue following developers in the cloud:

1. Open your repository: [**`a4hmad1/github-following-`**](https://github.com/a4hmad1/github-following-)
2. Go to **Settings** ➔ **Secrets and variables** ➔ **Actions**
3. Add a **Repository Secret**:
   - Name: `GH_PAT`
   - Value: Your GitHub Personal Access Token (`ghp_...`) with `user:follow` scope.
4. The workflow in [`.github/workflows/autopilot.yml`](file:///home/ahmad/github-auto-follower/.github/workflows/autopilot.yml) runs every **30 minutes** in GitHub's cloud, runs a batch, and syncs history back to your repository!

---

## 📜 Follow Logs & History

Every followed user is recorded in multiple layers:
1. `followed_history.json`: Machine-readable unique list and metadata.
2. `follows.log`: Plain-text activity log with timestamps, roles, and GitHub URLs:
```text
[2026-09-28 00:55:36] FOLLOWED: @Morning-Star213       | URL: https://github.com/Morning-Star213  | Role: Software Engineer      | Gender: Dev                | Location: Global • Software Engineer
```
3. Interactive query: Run `python3 autofollow.py --log` to search if an account has already been followed.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

<div align="center">

Developed with ❤️ by [**@a4hmad1**](https://github.com/a4hmad1)

</div>
