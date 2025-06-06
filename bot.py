import os
import json
import asyncio
import aiohttp
from datetime import datetime
from discord.ext import commands
import discord
from dotenv import load_dotenv

CONFIG_FILE = "config.json"

load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

message_queue = asyncio.Queue()

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"channels": []}, f)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)

config = load_config()

async def get_twitch_id(session, login):
    url = f"https://api.ivr.fi/v2/twitch/user?login={login}"
    print(f"[API] Fetching Twitch ID for login: {login}")
    async with session.get(url) as resp:
        data = await resp.json()
        if not data:
            raise Exception(f"No user found for login: {login}")
        print(f"[API] Twitch ID for {login}: {data[0]['id']}")
        return str(data[0]["id"])

async def get_7tv_emoteset_id(session, twitch_id):
    url = f"https://7tv.io/v3/users/twitch/{twitch_id}"
    print(f"[API] Fetching 7TV emote set ID for Twitch ID: {twitch_id}")
    async with session.get(url) as resp:
        data = await resp.json()
        print(f"[API] 7TV emote set ID: {data['emote_set_id']}")
        return data["emote_set_id"]

async def eventapi_listener(bot):
    await bot.wait_until_ready()
    session = aiohttp.ClientSession()
    ws_url = "wss://events.7tv.io/v3"
    while True:
        try:
            print("[WS] Connecting to 7TV EventAPI WebSocket PauseChamp...")
            async with session.ws_connect(ws_url) as ws:
                print("[WS] Connected.")
                hello = await ws.receive_json()
                session_id = hello["d"]["session_id"]
                print(f"[WS] Session ID: {session_id}")
                for ch in config["channels"]:
                    print(f"[WS] Subscribing to emote_set.update for {ch['twitch_login']} ({ch['emote_set_id']})")
                    await ws.send_json({
                        "op": 35,
                        "d": {
                            "type": "emote_set.update",
                            "condition": {"object_id": ch["emote_set_id"]}
                        }
                    })
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        if data.get("op") == 0:
                            await handle_dispatch(bot, data["d"])
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"[WS] WebSocket error: {msg.data}")
                        break
        except Exception as e:
            print(f"[WS] WebSocket error: {e}, reconnecting in 5s...")
            await asyncio.sleep(5)

async def handle_dispatch(bot, d):
    if d.get("type") != "emote_set.update":
        return
    body = d["body"]
    actor = body.get("actor", {}).get("display_name", "Unknown")
    emote_set_id = body.get("id")
    channel_name = next(
        (ch["twitch_login"] for ch in config["channels"] if ch["emote_set_id"] == emote_set_id),
        "Unknown"
    )
    emote_events = []

    for emote in body.get("pushed", []):
        if emote.get("key") == "emotes":
            value = emote.get("value", {})
            emote_id = value.get("id")
            emote_name = value.get("name")
            if emote_id and emote_name:
                emote_events.append({
                    "action": "ADD",
                    "name": emote_name,
                    "id": emote_id,
                    "url": f"https://cdn.7tv.app/emote/{emote_id}/4x.webp",
                    "actor": actor,
                    "color": discord.Color.green(),
                })
                print(f"[7TV] ADD {emote_name} ({emote_id}) in {channel_name} by {actor}")

    for emote in body.get("pulled", []):
        if emote.get("key") == "emotes":
            old = emote.get("old_value", {})
            emote_id = old.get("id")
            emote_name = old.get("name")
            if emote_id and emote_name:
                emote_events.append({
                    "action": "REMOVE",
                    "name": emote_name,
                    "id": emote_id,
                    "url": f"https://cdn.7tv.app/emote/{emote_id}/4x.webp",
                    "actor": actor,
                    "color": discord.Color.red(),
                })
                print(f"[7TV] REMOVE {emote_name} ({emote_id}) in {channel_name} by {actor}")

    for emote in body.get("updated", []):
        if emote.get("key") == "emotes" and emote.get("value") is None:
            old = emote.get("old_value", {})
            emote_id = old.get("id")
            emote_name = old.get("name")
            if emote_id and emote_name:
                emote_events.append({
                    "action": "REMOVE",
                    "name": emote_name,
                    "id": emote_id,
                    "url": f"https://cdn.7tv.app/emote/{emote_id}/4x.webp",
                    "actor": actor,
                    "color": discord.Color.red(),
                })
                print(f"[7TV] REMOVE (updated/None) {emote_name} ({emote_id}) in {channel_name} by {actor}")

    for emote in body.get("removed", []):
        old = emote.get("old_value", {})
        emote_id = old.get("id")
        emote_name = old.get("name")
        if emote_id and emote_name:
            emote_events.append({
                "action": "REMOVE",
                "name": emote_name,
                "id": emote_id,
                "url": f"https://cdn.7tv.app/emote/{emote_id}/4x.webp",
                "actor": actor,
                "color": discord.Color.red(),
            })
            print(f"[7TV] REMOVE (removed) {emote_name} ({emote_id}) in {channel_name} by {actor}")
            
    for emote in body.get("updated", []):
        if emote.get("key") == "emotes":
            old = emote.get("old_value", {})
            new = emote.get("value", {})
            old_name = old.get("name")
            new_name = new.get("name")
            emote_id = old.get("id") or new.get("id") or body["id"]
            if old_name and new_name and old_name != new_name:
                emote_events.append({
                    "action": "RENAME",
                    "name": f"{old_name} → {new_name}",
                    "id": emote_id,
                    "url": f"https://cdn.7tv.app/emote/{emote_id}/4x.webp",
                    "actor": actor,
                    "color": discord.Color.orange(),
                })
                print(f"[7TV] RENAME {old_name} → {new_name} ({emote_id}) in {channel_name} by {actor}")

    for event in emote_events:
        embed = discord.Embed(
            title=f"7TV UPDATE - {event['action']} - {channel_name} - {event['name']}",
            url=f"https://7tv.app/emotes/{event['id']}",
            description=(
                f"Emote: {event['name']}\n"
                f"ID: {event['id']}\n"
                f"Editor: {event['actor']}"
            ),
            colour=event["color"],
            timestamp=datetime.now(),
        )
        embed.set_thumbnail(url=event["url"])
        embed.set_footer(
            text="7TV UPDATE",
            icon_url="https://xyqra.com/assets/7tv.webp",
        )

        plain_text = (
            f"[7TV] {event['action']} | Channel: {channel_name} | "
            f"Emotename: {event['name']} | ID: {event['id']} | Editor: {event['actor']}"
        )
        await message_queue.put({"content": plain_text, "embed": embed})

async def send_messages_task(bot):
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"[DISCORD] Channel {CHANNEL_ID} not found.")
        return

    while True:
        msg = await message_queue.get()
        try:
            await channel.send(content=msg["content"], embed=msg["embed"])
            await asyncio.sleep(1.1)  # 1.1s is safe for 5/5s per-channel limit
        except discord.errors.HTTPException as e:
            if e.status == 429:
                # Rate limited, retry after the specified time
                retry_after = getattr(e, "retry_after", 5)
                print(f"[DISCORD] Rate limited! Retrying after {retry_after} seconds.")
                await asyncio.sleep(retry_after)
                await message_queue.put(msg)  # Put message back in queue
            else:
                print(f"[DISCORD] Failed to send message: {e}")
        except Exception as e:
            print(f"[DISCORD] Unexpected error: {e}")
        finally:
            message_queue.task_done()

@bot.command()
async def add(ctx, twitch_login: str):
    print(f"[CMD] !add {twitch_login} by {ctx.author}")
    async with aiohttp.ClientSession() as session:
        try:
            twitch_id = await get_twitch_id(session, twitch_login)
            emoteset_id = await get_7tv_emoteset_id(session, twitch_id)
        except Exception as e:
            print(f"[CMD] Failed to add {twitch_login}: {e}")
            await ctx.send(f"Failed to add: {e}")
            return
    # Check if already exists
    for ch in config["channels"]:
        if ch["twitch_login"] == twitch_login:
            print(f"[CMD] Channel {twitch_login} already added.")
            await ctx.send("Channel already added.")
            return
    config["channels"].append({
        "twitch_login": twitch_login,
        "twitch_id": twitch_id,
        "emote_set_id": emoteset_id,
    })
    save_config(config)
    print(f"[CMD] Added channel {twitch_login} (emote set {emoteset_id}).")
    await ctx.send(f"Added channel {twitch_login} (emote set {emoteset_id}). Please restart the bot to subscribe.")

@bot.command()
async def remove(ctx, twitch_login: str):
    print(f"[CMD] !remove {twitch_login} by {ctx.author}")
    before = len(config["channels"])
    config["channels"] = [
        ch for ch in config["channels"] if ch["twitch_login"] != twitch_login
    ]
    after = len(config["channels"])
    save_config(config)
    if before == after:
        print(f"[CMD] Channel {twitch_login} not found.")
        await ctx.send("Channel not found.")
    else:
        print(f"[CMD] Removed channel {twitch_login}.")
        await ctx.send(f"Removed channel {twitch_login}. Please restart the bot to unsubscribe.")

@bot.command()
async def list(ctx):
    print(f"[CMD] !list by {ctx.author}")
    if not config["channels"]:
        await ctx.send("No channels tracked.")
        print("[CMD] No channels tracked.")
        return
    msg = "\n".join(
        f"{ch['twitch_login']} (emote set {ch['emote_set_id']})"
        for ch in config["channels"]
    )
    await ctx.send(f"Tracked channels:\n{msg}")
    print(f"[CMD] Tracked channels:\n{msg}")

@bot.event
async def on_ready():
    print(f"[DISCORD] Logged in as {bot.user}")
    bot.loop.create_task(eventapi_listener(bot))
    bot.loop.create_task(send_messages_task(bot))

if __name__ == "__main__":
    print("[BOT] Starting 7TV Discord bot...")
    bot.run(DISCORD_TOKEN)
