import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json

load_dotenv()

TOKEN = os.getenv("MTUxMjcwMzY3Mjg2MDE1MTgyOA.G9NsgE.CGc4rg2N6iQoSuSlgJhWOTbs8CwCTuwR4QZHss")

CONFIG_FILE = "config.json"

DEFAULT_SETTINGS = {
    "prefix": "-",
    "channel1": None,
    "channel2": None,
    "lines": 2,
    "format": "@everyone {message}"
}


def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except:
        return {}


def save_config():
    with open(CONFIG_FILE, "w") as f:
        json.dump(configs, f, indent=4)


configs = load_config()


def get_guild_config(guild_id):
    guild_id = str(guild_id)

    if guild_id not in configs:
        configs[guild_id] = DEFAULT_SETTINGS.copy()
        save_config()

    return configs[guild_id]


def get_prefix(bot, message):
    if not message.guild:
        return "-"

    cfg = get_guild_config(message.guild.id)
    return cfg["prefix"]


intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None
)


def admin_only():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator

    return commands.check(predicate)


@bot.event
async def on_ready():
    print("=" * 50)
    print(f"Logged in as {bot.user}")
    print(f"Servers: {len(bot.guilds)}")
    print("=" * 50)


@bot.command()
@admin_only()
async def ping(ctx, *, message):

    cfg = get_guild_config(ctx.guild.id)

    output = cfg["format"].replace("{message}", message)

    channels = []

    if cfg["channel1"]:
        ch = bot.get_channel(cfg["channel1"])
        if ch:
            channels.append(ch)

    if cfg["channel2"]:
        ch = bot.get_channel(cfg["channel2"])
        if ch:
            channels.append(ch)

    if len(channels) == 0:
        return await ctx.send(
            "No channels configured.\nUse setchannel1 and setchannel2."
        )

    for channel in channels:
        for _ in range(cfg["lines"]):
            await channel.send(output)

    await ctx.message.add_reaction("✅")


@bot.command()
@admin_only()
async def setchannel1(ctx, channel: discord.TextChannel):

    cfg = get_guild_config(ctx.guild.id)

    cfg["channel1"] = channel.id

    save_config()

    await ctx.send(
        f"✅ Channel 1 set to {channel.mention}"
    )


@bot.command()
@admin_only()
async def setchannel2(ctx, channel: discord.TextChannel):

    cfg = get_guild_config(ctx.guild.id)

    cfg["channel2"] = channel.id

    save_config()

    await ctx.send(
        f"✅ Channel 2 set to {channel.mention}"
    )


@bot.command()
@admin_only()
async def setlines(ctx, amount: int):

    if amount < 1 or amount > 10:
        return await ctx.send(
            "Choose a value between 1 and 10."
        )

    cfg = get_guild_config(ctx.guild.id)

    cfg["lines"] = amount

    save_config()

    await ctx.send(
        f"✅ Lines changed to {amount}"
    )


@bot.command()
@admin_only()
async def setprefix(ctx, prefix):

    cfg = get_guild_config(ctx.guild.id)

    cfg["prefix"] = prefix

    save_config()

    await ctx.send(
        f"✅ Prefix changed to `{prefix}`"
    )


@bot.command()
@admin_only()
async def setformat(ctx, *, text):

    cfg = get_guild_config(ctx.guild.id)

    cfg["format"] = text

    save_config()

    await ctx.send(
        "✅ Format updated."
    )


@bot.command()
@admin_only()
async def resetconfig(ctx):

    configs[str(ctx.guild.id)] = DEFAULT_SETTINGS.copy()

    save_config()

    await ctx.send(
        "✅ Server configuration reset."
    )


@bot.command()
@admin_only()
async def viewconfig(ctx):

    cfg = get_guild_config(ctx.guild.id)

    embed = discord.Embed(
        title="Server Configuration",
        color=discord.Color.blue()
    )

    embed.add_field(
        name="Prefix",
        value=cfg["prefix"],
        inline=False
    )

    embed.add_field(
        name="Lines",
        value=cfg["lines"],
        inline=False
    )

    embed.add_field(
        name="Channel 1",
        value=str(cfg["channel1"]),
        inline=False
    )

    embed.add_field(
        name="Channel 2",
        value=str(cfg["channel2"]),
        inline=False
    )

    embed.add_field(
        name="Format",
        value=cfg["format"],
        inline=False
    )

    await ctx.send(embed=embed)


@bot.command()
async def help(ctx):

    prefix = get_guild_config(ctx.guild.id)["prefix"]

    embed = discord.Embed(
        title="Admin Ping Bot",
        description="Administrator-only utility bot",
        color=discord.Color.green()
    )

    embed.add_field(
        name="Commands",
        value=f"""
`{prefix}ping message`
`{prefix}setchannel1 #channel`
`{prefix}setchannel2 #channel`
`{prefix}setlines number`
`{prefix}setprefix newprefix`
`{prefix}setformat text`
`{prefix}viewconfig`
`{prefix}resetconfig`
`{prefix}help`
""",
        inline=False
    )

    await ctx.send(embed=embed)


bot.run(TOKEN)
