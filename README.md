# 7TV Discord Emote Update Bot

A simple Discord bot that listens for 7TV emote set changes (add, remove, rename) in specified Twitch channels and logs them as embeds and text in a Discord channel.

## Features

- **Real-time 7TV emote updates** (add, remove, rename) for any Twitch channel you add.
- **Discord embed notifications** in your chosen channel.
- **Easy channel management** via Discord text commands.

---

## Setup

1. **Clone this repo:**

    ```sh
    git clone https://github.com/Xyqra/7tv-Discord-Bot.git
    ```

2. **Install dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

3. **Create a `.env` file** (or edit the example) **with your Discord bot token and the id of the Discord channel:**

    ```
    DISCORD_TOKEN=your_discord_bot_token_here
    DISCORD_CHANNEL_ID=your_discord_channel_id_here
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
    !add <twitch_username>
    ```
    Example: `!add xyqra`

- **Remove a tracked Twitch channel:**

    ```
    !remove <twitch_username>
    ```
    Example: `!remove xyqra`

- **List all tracked channels:**

    ```
    !list
    ```

- When an emote is **added**, **removed**, or **renamed**, it sends a Discord embed to your configured channel.
- The embed includes the emote name, ID, image, and the editor who made the change.
- All tracked channels are saved in `config.json`.