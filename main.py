import discord
from discord.ext import commands
import json
import os

TOKEN = os.getenv("TOKEN")

CONFIG_FILE = "config.json"

DEFAULT_PREFIX = "-"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump({}, f)

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)


configs = load_config()


def get_prefix(bot, message):
    if not message.guild:
        return DEFAULT_PREFIX

    guild_id = str(message.guild.id)

    if guild_id not in configs:
        configs[guild_id] = {
            "prefix": DEFAULT_PREFIX,
            "channel1": None,
            "channel2": None,
            "lines": 2,
            "format": "@everyone {message}"
        }
        save_config(configs)

    return configs[guild_id]["prefix"]


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None
)


def is_admin():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator
    return commands.check(predicate)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


def get_guild_config(guild_id):
    guild_id = str(guild_id)

    if guild_id not in configs:
        configs[guild_id] = {
            "prefix": DEFAULT_PREFIX,
            "channel1": None,
            "channel2": None,
            "lines": 2,
            "format": "@everyone {message}"
        }
        save_config(configs)

    return configs[guild_id]


@bot.command()
@is_admin()
async def ping(ctx, *, message):

    cfg = get_guild_config(ctx.guild.id)

    output = cfg["format"].replace("{message}", message)

    channels = []

    if cfg["channel1"]:
        channels.append(ctx.guild.get_channel(cfg["channel1"]))

    if cfg["channel2"]:
        channels.append(ctx.guild.get_channel(cfg["channel2"]))

    if not channels:
        await ctx.send("No channels configured.")
        return

    for channel in channels:
        if channel:
            for _ in range(cfg["lines"]):
                await channel.send(output)

    await ctx.message.add_reaction("✅")


@bot.command()
@is_admin()
async def setchannel1(ctx, channel: discord.TextChannel):
    cfg = get_guild_config(ctx.guild.id)
    cfg["channel1"] = channel.id
    save_config(configs)
    await ctx.send(f"Channel 1 set to {channel.mention}")


@bot.command()
@is_admin()
async def setchannel2(ctx, channel: discord.TextChannel):
    cfg = get_guild_config(ctx.guild.id)
    cfg["channel2"] = channel.id
    save_config(configs)
    await ctx.send(f"Channel 2 set to {channel.mention}")


@bot.command()
@is_admin()
async def setlines(ctx, amount: int):

    if amount < 1 or amount > 10:
        return await ctx.send("Allowed range: 1-10")

    cfg = get_guild_config(ctx.guild.id)
    cfg["lines"] = amount

    save_config(configs)

    await ctx.send(f"Lines set to {amount}")


@bot.command()
@is_admin()
async def setprefix(ctx, prefix):

    cfg = get_guild_config(ctx.guild.id)

    cfg["prefix"] = prefix

    save_config(configs)

    await ctx.send(f"Prefix changed to `{prefix}`")


@bot.command()
@is_admin()
async def setformat(ctx, *, text):

    cfg = get_guild_config(ctx.guild.id)

    cfg["format"] = text

    save_config(configs)

    await ctx.send("Format updated.")


@bot.command()
@is_admin()
async def viewconfig(ctx):

    cfg = get_guild_config(ctx.guild.id)

    await ctx.send(
        f"""
Prefix: {cfg['prefix']}
Lines: {cfg['lines']}
Channel1: {cfg['channel1']}
Channel2: {cfg['channel2']}
Format: {cfg['format']}
"""
    )


@bot.command()
async def help(ctx):

    embed = discord.Embed(
        title="Admin Ping Bot",
        color=0x2F3136
    )

    embed.add_field(
        name="Commands",
        value="""
ping <message>
setchannel1 #channel
setchannel2 #channel
setlines <number>
setprefix <prefix>
setformat <text>
viewconfig
help
""",
        inline=False
    )

    await ctx.send(embed=embed)


bot.run(TOKEN)
