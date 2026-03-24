# TG-Chan Handler Bot

TG-Chan is a privacy-focused Telegram bot built with Pyrogram. It allows users to submit messages, media, and files to a designated Telegram channel either anonymously or using a custom nickname. To ensure user privacy, the bot stores hashes and seeded identities rather than direct Telegram IDs.

## Features
* **Anonymity & Nicknames:** Users can post completely anonymously or set a persistent, sanitized nickname (ASCII only).
* **Media Support:** Forwards text, photos, videos, audio, documents, and animations seamlessly.
* **Self-Deletion:** Users are given a secure inline button to delete their own posts from the channel.
* **Rate Limiting:** Built-in cooldowns for API requests, read operations, and write operations to prevent spam.
* **Admin Moderation:** Admins can securely blacklist/unblacklist abusive users and pull ("yank") specific posts via commands.

## Prerequisites
* Python 3.x
* [Pyrogram](https://docs.pyrogram.org/)
* `AShelve` (for local `blacklist`, `seedlist`, and `nicknames` storage)

## Installation & Setup

1. **Clone the repository:** Download the project files to your local environment.
2. **Configure Credentials:** * Rename `config.txt` to `config.py`.
   * Fill in your `SESSION_NAME`, `API_ID`, and `API_HASH` from my.telegram.org.
   * Add your `BOT_TOKEN` from @BotFather.
   * Set your `CHANNEL_ID`, `CHANNEL_USERNAME`, and a list of `ADMINS` IDs.
3. **Run the bot:**
   ```bash
   python main.py
   ```

## Commands

### User Commands
* `/start` - Register your seed and view the welcome message.
* `/info` - View your current hash, seed, and active nickname.
* `/nick [name]` - Change your display name (2-32 characters, A-Z, 0-9, `_`, `-`).
* `/privacy` - View the bot's data collection and privacy policy.
* `/delete [seed]` - Completely delete your stored user data and reset your identity.

### Admin Commands
* `/blacklist [user_hash]` - Ban a user from posting and delete their data.
* `/unblacklist [user_hash]` - Remove a user from the blacklist.
* `/yank [message_id]` - Force-delete a specific post from the channel.
* `/logs` - Retrieve the bot's log file for the current day.

## Logging
Logs are automatically generated and stored in a local `logs/` directory, rotating daily to preserve storage space. Admin users can access the current day's logs directly via Telegram using the `/logs` command.
