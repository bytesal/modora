# ModMail Bot

A production-ready, multi-server ModMail bot for Discord built with Python 3.11+ and discord.py 2.x. Designed for public use – any server owner can invite and configure independently.

## Features

- **Multi-server support** – Separate settings per guild, stored in MongoDB.
- **Slash commands only** – Modern, clean interface with `/modmail`, `/setup`, etc.
- **Ticket system** – Users open tickets via button or `/modmail new`.
- **Staff relay** – Staff replies sync to user DMs; user replies sync back.
- **Transcripts** – HTML transcripts generated on close, sent to transcripts channel.
- **Cooldowns & anti-duplicate** – Prevent spam and duplicate tickets.
- **Auto-close** – Inactive tickets auto-close after configured minutes.
- **Logging** – Full audit log to Discord channel and database.
- **Blacklist** – Owner can blacklist users/guilds globally.
- **Persistent views** – Buttons and selects survive bot restarts.
- **Railway optimized** – Health checks, connection pooling, memory tuning.

## Tech Stack

- Python 3.11+
- discord.py 2.3.2
- MongoDB with Motor (async)
- aiohttp (health check)
- aiofiles (transcripts)

## Invite the Bot

[Add to your server](https://discord.com/api/oauth2/authorize?client_id=YOUR_CLIENT_ID&permissions=8&scope=bot%20applications.commands)

*(Replace `YOUR_CLIENT_ID` with your bot's client ID after deployment)*

## Commands

### Setup (Admin only)

| Command | Description |
|---------|-------------|
| `/setup category` | Set category where ticket channels are created |
| `/setup staffrole` | Add/remove staff roles |
| `/setup logs` | Set logs channel |
| `/setup transcripts` | Set transcripts channel |
| `/setup panel` | Set panel channel and deploy ticket button |
| `/setup cooldown <seconds>` | Set cooldown between tickets (0=disable) |
| `/setup autoclose <minutes>` | Set auto-close timeout (0=disable) |
| `/setup show` | Show current configuration |
| `/setup reset` | Reset all settings |

### User Commands

| Command | Description |
|---------|-------------|
| `/modmail new [message]` | Open a new ticket (optional initial message) |
| `/modmail adduser <user>` | Add a user to current ticket (staff) |
| `/modmail removeuser <user>` | Remove user from ticket (staff) |
| `/modmail close` | Close current ticket (staff) |
| `/modmail claim` | Claim ticket (staff) |
| `/modmail rename <name>` | Rename ticket channel (staff) |

### Owner Commands

| Command | Description |
|---------|-------------|
| `/blacklist add user <id> [reason]` | Blacklist a user |
| `/blacklist add guild <id> [reason]` | Blacklist a guild |
| `/blacklist remove <id>` | Remove from blacklist |
| `/blacklist list` | Show blacklisted items |
| `/stats` | Show bot statistics |

## Setup Guide

### 1. Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application → Bot → Add Bot
3. Copy the **Bot Token**.
4. Enable these Privileged Gateway Intents:
   - Server Members Intent
   - Message Content Intent
5. Generate OAuth2 URL with scopes: `bot`, `applications.commands`
   - Permissions: `Administrator` (or custom: `Send Messages`, `Manage Channels`, `Read Message History`, `Embed Links`, `Attach Files`)

### 2. MongoDB Setup

1. Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Get connection string (e.g., `mongodb+srv://user:pass@cluster.mongodb.net/`)
3. Create a database (name: `modmail_db`)

### 3. Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

Or manually:

1. Fork/clone this repository to GitHub.
2. Go to [Railway.app](https://railway.app) → New Project → Deploy from GitHub.
3. Add environment variables (see below).
4. Railway automatically builds and deploys.

### 4. Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
# Required
BOT_TOKEN=your_bot_token_here
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority

# Optional
BOT_PREFIX=/
BOT_ACTIVITY=ModMail | /help
LOG_LEVEL=INFO
ERROR_WEBHOOK_URL=https://discord.com/api/webhooks/...
DB_NAME=modmail_db
MONGO_MAX_POOL_SIZE=10
MONGO_MIN_POOL_SIZE=1
MONGO_MAX_IDLE_TIME_MS=10000
HEALTH_CHECK_PORT=8080
MAX_MESSAGES_CACHE=1000
DISABLE_VOICE=True
