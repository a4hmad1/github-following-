<div align="center">

# ⚡ GitHub Auto-Follower Pro

**A blazing-fast, intelligent, and resilient CLI automation tool for GitHub networking.**

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![GitHub license](https://img.shields.io/badge/license-MIT-green.svg?style=for-the-badge)](LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/a4hmad1/github-auto-follower?style=for-the-badge&logo=github)](https://github.com/a4hmad1/github-auto-follower/stargazers)
[![GitHub Followers](https://img.shields.io/github/followers/a4hmad1?style=for-the-badge&logo=github&label=Follow%20%40a4hmad1)](https://github.com/a4hmad1)

<p align="center">
  <a href="#-key-features">Key Features</a> •
  <a href="#-speed-benchmarks">Speed Benchmarks</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-token-setup">Token Setup</a> •
  <a href="#-usage-guide">Usage Guide</a> •
  <a href="#-rate-limit--safety-shield">Safety Shield</a>
</p>

</div>

---

## 🚀 Overview

**GitHub Auto-Follower Pro** is a high-performance Python automation utility engineered to help developers expand their open-source network efficiently. Built with asynchronous connection pooling, in-memory pre-caching, and intelligent rate-limit backoff, it delivers the fastest possible execution speed while remaining compliant with GitHub's REST API standards.

---

## ✨ Key Features

- **⚡ Turbo Engine (~150 Follows/min)**: Leverages HTTP keep-alive connection pooling (`urllib3` / `requests.adapters.HTTPAdapter`) to eliminate TLS handshake overhead on every request.
- **🧠 In-Memory Smart Cache**: Bulk pre-syncs your current following list into memory at launch. Eliminates 100% of individual check requests, doubling execution speed.
- **🛡️ Adaptive Rate-Limit Shield**: Actively inspects response headers (`x-ratelimit-reset`, `Retry-After`). If GitHub signals secondary rate limits, the tool automatically pauses for the exact cooldown duration and resumes seamlessly.
- **💾 Safe Pause & Auto-Resume**: Automatically tracks every processed user in `followed_history.json`. Stop at any time with `Ctrl+C` and restart without duplicate follows.
- **🔗 Smart URL Cleaning**: Paste raw input like `https://github.com/laravel`, `@torvalds`, or `owner/repo`—the tool automatically extracts clean identifiers.
- **🎯 Multi-Targeting Discovery**:
  - **Account Followers**: Target followers of any individual developer or organization.
  - **Repository Contributors**: Target active contributors of any repository.
  - **Search Queries**: Target active developers by programming language, location, or follower count.

---

## 📊 Speed Benchmarks

| Mode | Delay | Rate | 1,000 Accounts | 10,000 Accounts | Recommended For |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **🚀 Turbo** | `0.5s` | **~120–150 / min** | ~7 mins | ~1.2 hrs | Fast bulk networking |
| **⚡ Fast** *(Default)* | `1.0s` | **~60 / min** | ~16 mins | ~2.8 hrs | Balanced daily use |
| **🛡️ Safe** | `2.5s` | **~24 / min** | ~40 mins | ~7.0 hrs | Extended conservative runs |

---

## 📦 Installation

### 1. Clone the repository
```bash
git clone https://github.com/a4hmad1/github-auto-follower.git
cd github-auto-follower
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Token Setup

The tool communicates with GitHub's REST API using a **Personal Access Token (PAT)**.

1. Go to **[GitHub Token Settings (Classic)](https://github.com/settings/tokens)**.
2. Click **Generate new token (classic)**.
3. Set note name (e.g. `github-follower-tool`).
4. Select **ONLY** the following scope:
   - `[x] user:follow` (Access to follow/unfollow users).
5. Copy your generated token.
6. Create your `.env` file from the provided template:
```bash
cp .env.example .env
```
7. Open `.env` and add your token:
```env
GITHUB_TOKEN=ghp_yourTokenHere
```
*(Permissions are automatically restricted to protect your secret).*

---

## 💻 Usage Guide

### 1. Interactive Menu Mode
Run without flags to open the interactive command console:
```bash
python3 autofollow.py
```
```text
✓ Authenticated as @a4hmad1
  Followers: 26 | Following: 218

Choose target mode:
  1) Follow followers of a user or organization (e.g. laravel, octocat)
  2) Search users by keyword/location/language (e.g. location:Iraq)
  3) Follow contributors of a repository (e.g. laravel/framework)
  4) Enter specific usernames manually (comma separated)
  5) Exit
```

---

### 2. Command-Line Direct Modes

#### A. Follow Followers of a User or Organization
```bash
# Turbo mode (max speed)
python3 autofollow.py --user laravel --turbo

# Custom batch limit
python3 autofollow.py --user https://github.com/torvalds --limit 50
```

#### B. Search Active Developers by Tech Stack or Location
```bash
# Target Python developers in a specific country
python3 autofollow.py --search "location:Iraq language:python" --turbo

# Target developers actively participating in follow communities
python3 autofollow.py --search "follow-back" --turbo
```

#### C. Follow Active Contributors of a Repository
```bash
python3 autofollow.py --repo laravel/framework --turbo
python3 autofollow.py --repo flutter/flutter --limit 100
```

#### D. Dry-Run Mode (Simulation)
Preview targets without sending real API requests:
```bash
python3 autofollow.py --user laravel --limit 10 --dry-run
```

#### E. Custom Delay Speed
Specify any custom delay in seconds:
```bash
python3 autofollow.py --user laravel --delay 0.8
```

---

## 🛡️ Rate Limit & Safety Shield

> [!IMPORTANT]
> **GitHub Anti-Abuse Compliance**
> - GitHub limits standard authenticated tokens to **5,000 API requests per hour**.
> - Write operations (such as follows) are monitored by GitHub's abuse detection algorithms.
> - **GitHub Auto-Follower Pro** includes built-in protection:
>   - Automatic backoff on HTTP `403` / `429` status codes.
>   - Adheres to `Retry-After` headers sent by GitHub servers.
>   - Pre-caches following states to minimize unnecessary network traffic.
>   - Never stores credentials in code or repository commits.

---

## 📂 Project Structure

```text
github-auto-follower/
├── autofollow.py           # Core CLI automation engine
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template for GITHUB_TOKEN
├── .env                    # Local private token configuration (git-ignored)
├── .gitignore              # Protects secrets & logs from commits
├── followed_history.json   # Persistent history of followed users
└── README.md               # Project documentation
```

---

## 🤝 Contributing

Contributions, feature requests, and bug reports are welcome!
1. Fork the Project.
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`).
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the Branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

---

<div align="center">

Developed with ❤️ by [**@a4hmad1**](https://github.com/a4hmad1)

⭐ **Star this repository if you find it helpful!**

</div>
