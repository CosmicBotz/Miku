<div align="center">

  <!-- Animated Header Banner -->
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=0,2,10,12,30&height=250&section=header&text=FRIEREN%20MANAGEMENT%20BOT&fontSize=42&fontColor=ffffff&animation=fadeIn&fontAlignY=38&desc=Anime-Themed%20Modular%20Telegram%20Group%20Management%20Engine&descAlignY=62&descAlign=50" width="100%" alt="Frieren Header"/>

  <!-- Typing Animation -->
  <a href="https://git.io/typing-svg">
    <img src="https://readme-typing-svg.demolab.com?font=Fira+Code&weight=600&size=22&pause=1000&color=61AFEF&center=true&vCenter=true&width=700&lines=⚡+Modular+PTB+v22+Async+Telegram+Bot;🛡️+Advanced+Moderation+%7C+Anti-Spam+%7C+Anti-Flood;🔮+Custom+Auto-Reply+Filters;🏰+Multi-Chat+Federation+Mutes+%26+FBans;✨+Built+with+Python+3.11+%26+Async+MongoDB" alt="Typing SVG" />
  </a>

  <br/><br/>

  <!-- Badges -->
  <p align="center">
    <a href="https://www.python.org/">
      <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python Version"/>
    </a>
    <a href="https://github.com/python-telegram-bot/python-telegram-bot">
      <img src="https://img.shields.io/badge/PTB-v22.0%20Async-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white" alt="PTB Framework"/>
    </a>
    <a href="https://www.mongodb.com/">
      <img src="https://img.shields.io/badge/MongoDB-Async%20Motor-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB Database"/>
    </a>
    <a href="https://docker.com">
      <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker Ready"/>
    </a>
    <a href="https://opensource.org/licenses/MIT">
      <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge&logo=opensource&logoColor=white" alt="License"/>
    </a>
  </p>

  <!-- Quick Deployment Badges -->
  <p align="center">
    <a href="https://render.com">
      <img src="https://img.shields.io/badge/Deploy%20To-Render-46E3B7?style=for-the-badge&logo=render&logoColor=black" alt="Render Deploy"/>
    </a>
    <a href="https://koyeb.com">
      <img src="https://img.shields.io/badge/Deploy%20To-Koyeb-121019?style=for-the-badge&logo=koyeb&logoColor=white" alt="Koyeb Deploy"/>
    </a>
    <a href="https://heroku.com">
      <img src="https://img.shields.io/badge/Deploy%20To-Heroku-430098?style=for-the-badge&logo=heroku&logoColor=white" alt="Heroku Deploy"/>
    </a>
  </p>

  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-852c-151550a4207d.gif" width="100%" alt="Divider"/>

</div>

## 🌟 Overview

**Frieren Group Management Bot** is a high-performance, asynchronous Telegram group administration bot inspired by top-tier Telegram bots like *Rose*, *Marie*, and *Daisy*. Built with modern **Python 3.11+**, **python-telegram-bot v22 (async)**, and **MongoDB**, Frieren protects and manages public or private supergroups with lightning speed and elegant anime-themed responses.

> ℹ️ **Import Safety Update**: The custom auto-reply filter engine is named **`bot/modules/cust_filters.py`** to completely prevent namespace collisions with `telegram.ext.filters` across all execution environments.

---

## 🚀 Key Highlights & Features

<div align="center">

| Feature Module | Description & Capabilities | Status |
| :--- | :--- | :---: |
| 🛡️ **Moderation Core** | Ban, Kick, Mute, Warn, Purge, Temp-Ban, Temp-Mute with time syntax (`1h`, `2d`, `1w`) | 🟢 Active |
| 🔮 **Custom Auto-Filters** | Keyword & media trigger auto-replies powered by `cust_filters.py` | 🟢 Active |
| 📜 **Notes Engine** | Save rich text & media notes accessible via `/get` or `#notename` hashtag | 🟢 Active |
| 🔒 **Chat Lock Manager** | Lock stickers, photos, videos, GIFs, links, audio, forwards, bots & inline queries | 🟢 Active |
| ⚡ **Anti-Flood & Rate Limits** | Instant detection & configurable auto-restriction for flooders | 🟢 Active |
| 🚫 **Anti-Spam & Blacklist** | Per-chat keyword blacklist, link restriction, and automated spam filtering | 🟢 Active |
| 🏰 **Federation System** | Global bans across federated communities with multi-admin management | 🟢 Active |
| 🎫 **Captcha & Anti-Raid** | Interactive welcome captchas and emergency anti-raid lockouts | 🟢 Active |
| 📌 **Log Channels & Admin Tools** | Action logging to private channel, pinned message management, and admin controls | 🟢 Active |
| 🤝 **Approvals & Sudo** | Exempt trusted users from anti-flood, spam, and lock restrictions | 🟢 Active |
| 🎭 **Anime & Entertainment** | Dice rolls, magic 8-ball, quote generator, user ship matching, and power levels | 🟢 Active |

</div>

---

## 📁 Repository Structure

```
anime-mod-bot/
├── run.py                     # CLI entry point (loads config & starts app)
├── config.sample.yaml         # Configuration blueprint (YAML + Env support)
├── requirements.txt           # Python dependencies (PTB v22, Motor, PyYAML)
├── Dockerfile                 # Multi-stage production container build
├── docker-compose.yml         # Local Docker setup with Mongo service
├── render.yaml                 # Render Blueprint configuration
├── Procfile                   # Process descriptor for PaaS (Heroku/Railway)
└── bot/
    ├── app.py                 # Application builder & lifecycle hooks
    ├── config.py              # YAML config parser & environment overrides
    ├── logger.py              # Structured logging configuration
    ├── webserver.py            # Async dummy AIOHTTP health check server (for Render/Koyeb)
    ├── database/
    │   ├── base.py             # Motor async MongoDB connection lifecycle
    │   └── crud.py              # High-performance async CRUD queries
    ├── utils/
    │   ├── decorators.py        # @admin_only, @group_only, @bot_admin_required
    │   ├── extraction.py        # Target user & reason resolution utilities
    │   ├── permissions.py       # Admin hierarchy & approval checks
    │   └── flavor.py            # Anime-styled dialogue responses
    └── modules/                 # 🔌 Dynamic module auto-loader package
        ├── help_module.py        # Help matrix & /start router
        ├── welcome.py            # Custom welcome/goodbye & service message cleaner
        ├── moderation.py         # Ban, kick, mute, tban, tmute, unban
        ├── warns.py              # Warning counter & automated penalty enforcement
        ├── antiflood.py          # Message rate monitor & flood trigger
        ├── antispam.py           # Blacklist filters & URL link suppressor
        ├── antiraid.py           # Group raid protection & join locks
        ├── captcha.py            # Member verification captcha system
        ├── cust_filters.py       # 🔮 Custom auto-reply filter triggers (renamed)
        ├── notes.py              # Saved note storage & #hashtag parser
        ├── locks.py              # Granular media & content locks
        ├── federations.py        # Cross-chat federation bans & admin management
        ├── approvals.py          # User exemption & whitelisting
        ├── connections.py        # Remote PM chat administration connection
        ├── disabling.py          # Per-chat command toggles
        ├── log_channel.py        # Moderation event logging engine
        ├── admin_tools.py        # Rules, admin list & channel pin handlers
        ├── purge.py              # Message batch purging & deletion
        ├── reports.py            # User report notifications to admins
        ├── support.py            # Bot stats & support links
        ├── info.py               # Detailed user & chat lookup info
        └── fun.py                # Anime games, quotes, & entertainment commands
```

---

## ⚡ Interactive Command Matrix

<details>
<summary><b>🛡️ Moderation & Enforcement (Click to expand)</b></summary>

| Command | Usage | Admin Only? | Description |
| :--- | :--- | :---: | :--- |
| `/ban` | `/ban <user> [reason]` | Yes | Ban a user permanently from the chat. |
| `/unban` | `/unban <user>` | Yes | Lift a user's ban. |
| `/tban` | `/tban <user> <time>` | Yes | Temporarily ban user (e.g., `1h`, `12h`, `2d`). |
| `/kick` | `/kick <user> [reason]` | Yes | Kick user from chat (they can rejoin). |
| `/mute` | `/mute <user> [reason]` | Yes | Restrict user from sending messages. |
| `/unmute` | `/unmute <user>` | Yes | Restore user's messaging privileges. |
| `/tmute` | `/tmute <user> <time>` | Yes | Temporarily mute user (e.g., `30m`, `2h`). |
| `/purge` | Reply to message | Yes | Purge all messages from replied message to latest. |
| `/del` | Reply to message | Yes | Delete the replied message instantly. |

</details>

<details>
<summary><b>🔮 Custom Auto-Filters & Notes (Click to expand)</b></summary>

| Command | Usage | Admin Only? | Description |
| :--- | :--- | :---: | :--- |
| `/filter` | `/filter <keyword> <reply|media>` | Yes | Add custom keyword auto-reply (in `cust_filters.py`). |
| `/filters` | `/filters` | No | List all active auto-reply filters in chat. |
| `/stop` | `/stop <keyword>` | Yes | Remove a custom auto-reply filter. |
| `/stopall` | `/stopall` | Yes | Wipe all auto-reply filters in current chat. |
| `/save` | `/save <name> <content|media>` | Yes | Save a note triggered by `/get name` or `#name`. |
| `/get` | `/get <name>` | No | Retrieve saved note. |
| `/notes` | `/notes` | No | Display all saved notes in chat. |
| `/clear` | `/clear <name>` | Yes | Delete a specific note. |
| `/clearall` | `/clearall` | Owner Only | Delete all notes saved in the chat. |

</details>

<details>
<summary><b>🔒 Group Protection, Locks & Anti-Spam (Click to expand)</b></summary>

| Command | Usage | Admin Only? | Description |
| :--- | :--- | :---: | :--- |
| `/warn` | `/warn <user> [reason]` | Yes | Issue a formal warning to a user. |
| `/warns` | `/warns <user>` | No | Check active warning count for user. |
| `/rmwarn` | `/rmwarn <user>` | Yes | Remove last warning from user. |
| `/resetwarns` | `/resetwarns <user>` | Yes | Reset all warnings for user to zero. |
| `/setwarnlimit` | `/setwarnlimit <num>` | Yes | Set warning threshold before punishment. |
| `/setwarnmode` | `/setwarnmode ban\|kick\|mute` | Yes | Set warning limit action. |
| `/lock` | `/lock <type>` | Yes | Lock content type (`sticker`, `photo`, `url`, `bot`, etc.). |
| `/unlock` | `/unlock <type>` | Yes | Unlock specified content type. |
| `/locks` | `/locks` | No | View current lock settings. |
| `/setflood` | `/setflood <num\|off>` | Yes | Configure maximum messages before flood mute. |
| `/flood` | `/flood` | No | Check active anti-flood limit. |
| `/addspam` | `/addspam <word>` | Yes | Add keyword to chat blacklist. |
| `/rmspam` | `/rmspam <word>` | Yes | Remove keyword from blacklist. |
| `/blacklist` | `/blacklist` | No | Show chat blacklisted keywords. |

</details>

<details>
<summary><b>🏰 Federations & Global Mutes (Click to expand)</b></summary>

| Command | Usage | Admin Only? | Description |
| :--- | :--- | :---: | :--- |
| `/newfed` | `/newfed <name>` | Yes | Create a new federation. |
| `/delfed` | `/delfed <fed_id>` | Fed Owner | Delete federation. |
| `/joinfed` | `/joinfed <fed_id>` | Group Admin | Join current chat to federation. |
| `/leavefed` | `/leavefed` | Group Admin | Disconnect chat from federation. |
| `/fban` | `/fban <user> [reason]` | Fed Admin | Federation ban user across all fed chats. |
| `/unfban` | `/unfban <user>` | Fed Admin | Remove federation ban. |
| `/fedinfo` | `/fedinfo [fed_id]` | No | View federation information. |
| `/fedadmins` | `/fedadmins [fed_id]` | No | List federation administrators. |
| `/fedpromote` | `/fedpromote <user>` | Fed Owner | Add user as fed admin. |
| `/feddemote` | `/feddemote <user>` | Fed Owner | Demote fed admin. |

</details>

<details>
<summary><b>🎭 Anime & Entertainment (Click to expand)</b></summary>

| Command | Usage | Admin Only? | Description |
| :--- | :--- | :---: | :--- |
| `/roll` | `/roll [sides]` | No | Roll a dice (default 6 sides). |
| `/8ball` | `/8ball <question>` | No | Ask the mystic 8-ball a question. |
| `/quote` | `/quote` | No | Get an inspiring anime quote. |
| `/ship` | `/ship` | No | Ship two random members in the group! |
| `/power` | `/power [user]` | No | Measure user's anime power level over 9000. |

</details>

---

## 🛠️ Quick Start & Installation

### Prerequisites
- **Python 3.10+** installed
- **MongoDB** instance (Local or [MongoDB Atlas Free Cluster](https://www.mongodb.com/atlas))
- **Telegram Bot Token** from [@BotFather](https://t.me/BotFather)
- **Owner Telegram User ID** from [@userinfobot](https://t.me/userinfobot)

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-username/anime-mod-bot.git
cd anime-mod-bot

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Copy configuration template
cp config.sample.yaml config.yaml

# 5. Edit configuration or export environment variables
export ANIME_BOT_TOKEN="your_bot_token_here"
export ANIME_BOT_OWNER_ID="123456789"
export ANIME_BOT_MONGO_URI="mongodb+srv://user:pass@cluster.mongodb.net/frieren"

# 6. Launch the bot
python run.py
```

---

## ⚙️ Environment Configuration Guide

Frieren supports seamless dual-mode configuration via `config.yaml` or direct environment variables (ideal for PaaS cloud deployments):

| Configuration Field | Config YAML Key | Environment Variable | Default |
| :--- | :--- | :--- | :--- |
| **Bot Token** | `telegram.bot_token` | `ANIME_BOT_TOKEN` | *Required* |
| **Owner User ID** | `owner.owner_id` | `ANIME_BOT_OWNER_ID` | *Required* |
| **Sudo Users** | `owner.sudo_users` | `ANIME_BOT_SUDO_USERS` | `[]` (Comma-separated) |
| **Mongo Connection URI** | `mongodb.uri` | `ANIME_BOT_MONGO_URI` | `mongodb://localhost:27017` |
| **Database Name** | `mongodb.db_name` | `ANIME_BOT_MONGO_DB_NAME` | `frieren_bot` |
| **Health Check Port** | `server.port` | `PORT` / `ANIME_BOT_PORT` | `8080` |
| **Logging Level** | `logging.level` | `ANIME_BOT_LOG_LEVEL` | `INFO` |

---

## 🐳 Docker & Cloud Deployment

### 1. Docker Compose (Local Mongo included)

```bash
cp config.sample.yaml config.yaml
docker compose up -d --build
```

### 2. Render Blueprint Deployment

1. Fork/Push this repository to GitHub.
2. Go to **[Render Dashboard](https://dashboard.render.com)** → **New +** → **Blueprint**.
3. Connect your repository — Render automatically detects `render.yaml`.
4. Provide `ANIME_BOT_TOKEN`, `ANIME_BOT_OWNER_ID`, and `ANIME_BOT_MONGO_URI` in the prompt.
5. Click **Deploy**!

### 3. Koyeb / Heroku PaaS

This repository comes pre-packaged with a standard `Procfile` (`web: python run.py`) and an integrated `aiohttp` web listener (`bot/webserver.py`). PaaS providers will automatically route HTTP health-check pings to `/health` while the bot maintains persistent Telegram long-polling.

```bash
heroku create frieren-mod-bot
heroku config:set ANIME_BOT_TOKEN="your_token" ANIME_BOT_OWNER_ID="123456" ANIME_BOT_MONGO_URI="your_mongo_url"
git push heroku main
```

---

## 🔌 Adding Custom Modules

Frieren's dynamic auto-loader (`bot/modules/__init__.py`) automatically discovers every module in `bot/modules/`. To add a new feature:

1. Create `bot/modules/my_feature.py`.
2. Define your command logic using PTB v22 handlers.
3. Export a `register(application)` entrypoint:

```python
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from ..utils.decorators import admin_only, group_only

@group_only
@admin_only
async def magic_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text("✨ Casting Zoltraak magic spell!")

def register(application):
    application.add_handler(CommandHandler("magic", magic_cmd))
```

---

<div align="center">

  <img src="https://user-images.githubusercontent.com/73097560/115834477-dbab4500-a447-11eb-852c-151550a4207d.gif" width="100%" alt="Divider"/>

  <h3>⭐ Star this repository if you find it helpful! ⭐</h3>

  <p align="center">
    <i>"It's custom magic... created with care."</i><br/>
    Made with ❤️ for the Telegram Community
  </p>

  <a href="#top"><b>⬆️ Back to Top</b></a>

</div>
