# ModMail Bot

A production-ready, multi-server ModMail bot for Discord built with Python 3.11+ and discord.py 2.x. Designed for public use – any server owner can invite and configure independently.

## Invite the Bot

[Add to your server](https://discord.com/oauth2/authorize?client_id=1509197028910174268&permissions=8&integration_type=0&scope=bot+applications.commands)

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

### Staff Commands

| Command | Description |
|---------|-------------|
| `/modmail close` | Close current ticket |
| `/modmail claim` | Claim a ticket |
| `/modmail rename <name>` | Rename ticket channel |
| `/modmail adduser <user>` | Add user to ticket |
| `/modmail removeuser <user>` | Remove user from ticket |

### User Commands

| Command | Description |
|---------|-------------|
| `/modmail new [message]` | Open a new ticket (optional initial message) |
| Click the ticket button | Open ticket from panel |

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

### 2. MongoDB Setup

1. Create a free cluster at [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Get connection string (e.g., `mongodb+srv://user:pass@cluster.mongodb.net/`)

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
```

### 5. Run Locally (Development)

```bash
# Clone repository
git clone https://github.com/yourusername/modmail-bot.git
cd modmail-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your tokens

# Run bot
python main.py
```

### 6. Post-Deployment Setup in Discord

1. Invite bot to your server using the invite link above.
2. Run `/setup category` → provide a category ID (ticket channels go here).
3. Run `/setup staffrole` → add staff roles.
4. Run `/setup logs` → set channel for ticket logs.
5. Run `/setup transcripts` → set channel for transcripts.
6. Run `/setup panel` → set channel and deploy ticket button.

## File Structure

```
ModMail-Bot/
├── main.py                 # Entry point
├── requirements.txt
├── runtime.txt
├── railway.json
├── nixpacks.toml
├── .env.example
├── README.md
├── LICENSE
├── config/
│   └── config.py
├── database/
│   └── mongo.py
├── models/
│   ├── guild_config.py
│   ├── ticket.py
│   └── log_entry.py
├── cogs/
│   ├── setup.py
│   ├── modmail.py
│   ├── admin.py
│   └── tasks.py
├── views/
│   ├── ticket_panel.py
│   └── ticket_controls.py
├── services/
│   ├── guild_config_service.py
│   ├── ticket_service.py
│   ├── log_service.py
│   └── transcript_service.py
└── utils/
    ├── logger.py
    ├── helpers.py
    ├── permissions.py
    ├── embeds.py
    ├── cooldown.py
    ├── blacklist.py
    ├── rate_limiter.py
    ├── error_handler.py
    └── health_check.py
```

## Troubleshooting

### Bot doesn't respond to commands
- Ensure slash commands are synced (they sync on startup, but may take up to 1 hour globally).
- Re-invite bot with `applications.commands` scope.
- Check bot has `Send Messages` and `Embed Links` in the channel.

### Tickets not creating
- Verify category ID is correct and bot has `Manage Channels` permission in that category.
- Check that staff roles exist and bot has permission to assign channel overrides.

### MongoDB connection errors
- Verify `MONGO_URI` is correct and network allows connections.
- Use MongoDB Atlas → Network Access → Add IP Address `0.0.0.0/0` (for testing only).

### Transcripts not sending
- Ensure transcripts channel is set with `/setup transcripts`.
- Bot needs `Send Messages`, `Attach Files`, and `Embed Links` in that channel.

## License

MIT License – see [LICENSE](LICENSE) file.

---

**Built with ❤️ for the Discord community**
