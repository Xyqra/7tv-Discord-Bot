# 7TV Discord Emote Update Bot

A simple Discord bot that listens for [7TV](https://7tv.io) emote set changes (add, remove, rename) in specified Twitch channels and logs them as embeds in a Discord channel.

## Features

- **Real-time 7TV emote updates** (add, remove, rename) for any Twitch channel you add.
- **Discord embed notifications** in your chosen channel.
- **Easy channel management** via Discord text commands.
- **Persistent tracking**: Tracked channels are saved and auto-loaded on restart.

---

## Setup

1. **Clone this repo and install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

2. **Create a `.env` file** with your Discord bot token:

    ```
    DISCORD_TOKEN=your_discord_bot_token_here
    ```

3. **Edit the bot code** to set your Discord channel ID:

    ```python
    CHANNEL_ID = 1353345306711818314  # Replace with your channel ID
    ```

4. **Run the bot:**

    ```sh
    python bot.py
    ```

---

## Commands

Type these commands in any channel where the bot can read messages:

- **Add a Twitch channel to track:**
    ```
    !add <twitch_login>
    ```
    Example: `!add xyqra`

    > The bot will fetch the Twitch ID and 7TV emote set for that user and start tracking emote changes.

- **Remove a tracked Twitch channel:**
    ```
    !remove <twitch_login>
    ```
    Example: `!remove xyqra`

- **List all tracked channels:**
    ```
    !list
    ```

---

## How it works

- The bot listens to the 7TV EventAPI for emote set changes in all tracked channels.
- When an emote is **added**, **removed**, or **renamed**, it sends a Discord embed to your configured channel.
- The embed includes the emote name, ID, image, and the editor who made the change.
- All tracked channels are saved in `config.json` and auto-loaded on restart.
