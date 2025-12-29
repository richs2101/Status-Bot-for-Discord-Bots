import discord
from discord.ext import commands, tasks
import datetime
import asyncio

TOKEN = 'YOUR_DISCORD_BOT_TOKEN_HERE'
TARGET_BOT_IDS = [, ] Add more IDs as needed
STATUS_CHANNEL_ID = 		Replace with actual channel ID
ADDITIONAL_FOOTER = "Made by Dave Davidson: (Discord user: richs2101)"

intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix='!', intents=intents)

status_message_id = None
status_messages = []
last_updated = "Never"

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    update_status.start()

@tasks.loop(seconds=60)
async def update_status():
    global status_message_id, status_messages, last_updated

    channel = bot.get_channel(STATUS_CHANNEL_ID)
    if channel is None:
        print("[ERROR] Status channel not found.")
        return

    status_messages.clear()

    # Gather each bot's status
    for bot_id in TARGET_BOT_IDS:
        target_member = channel.guild.get_member(bot_id)
        if target_member is None:
            msg = f"Bot with ID {bot_id} not found in this server."
            print(f"[WARNING] {msg}")
            status_messages.append(msg)
            continue

        bot_name = target_member.display_name
        status = target_member.status
        if status in [discord.Status.online, discord.Status.idle, discord.Status.dnd]:
            status_messages.append(f"🟢 {bot_name}: Online")
        else:
            status_messages.append(f"🔴 {bot_name}: Offline")

    last_updated = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')

    embed = discord.Embed(
        title="Bot Status Update",
        description="\n".join(status_messages) + f"\n\nLast updated: {last_updated}",
        color=0x00ff00
    )
    embed.set_footer(text="Updating every 60 seconds")

    additional_embed = discord.Embed(
        description=ADDITIONAL_FOOTER,
        color=0x00ff00
    )

    try:
        if status_message_id is None:
            print("[INFO] Sending initial status message.")
            message = await channel.send(embeds=[embed, additional_embed])
            status_message_id = message.id
            print(f"[INFO] Status message sent with ID: {status_message_id}")
        else:
            print(f"[INFO] Fetching existing status message ID: {status_message_id}")
            message = await channel.fetch_message(status_message_id)
            print("[INFO] Editing status message...")
            await message.edit(embeds=[embed, additional_embed])
            print("[INFO] Status message updated successfully.")

    except discord.NotFound:
        print("[WARNING] Status message not found (deleted?). Sending a new message.")
        message = await channel.send(embeds=[embed, additional_embed])
        status_message_id = message.id
        print(f"[INFO] New status message created with ID: {status_message_id}")

    except discord.errors.HTTPException as e:
        if e.status == 429:
            retry_after = getattr(e, 'retry_after', 10)
            print(f"[WARNING] Rate limited by Discord. Sleeping for {retry_after} seconds before retry.")
            await asyncio.sleep(retry_after)
        else:
            print(f"[ERROR] HTTPException occurred: {e}")

    except discord.errors.DiscordServerError as e:
        print(f"[ERROR] DiscordServerError (503) occurred: {e} Retrying in 10 seconds.")
        await asyncio.sleep(10)

    except Exception as e:
        print(f"[ERROR] Unexpected error in update_status: {e}")

@bot.command()
async def status(ctx):
    await ctx.send("Status updates are automatic in the designated channel. Check there!")

bot.run(TOKEN)
