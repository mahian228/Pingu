import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import json

load_dotenv()

TOKEN = os.getenv("TOKEN")

CONFIG_FILE = "config.json"

DEFAULT_SETTINGS = {
    "prefix": "-",
    "channel1": None,
    "channel2": None,
    "lines": 2,
    "format": "@everyone {message}",
    "whitelist": [],
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

    if "whitelist" not in configs[guild_id]:
        configs[guild_id]["whitelist"] = []
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

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)


def admin_only():
    async def predicate(ctx):
        return ctx.author.guild_permissions.administrator

    return commands.check(predicate)


def p_allowed():
    async def predicate(ctx):
        if ctx.author.guild_permissions.manage_guild:
            return True
        cfg = get_guild_config(ctx.guild.id)
        return any(
            (entry["id"] if isinstance(entry, dict) else entry) == ctx.author.id
            for entry in cfg["whitelist"]
        )

    return commands.check(predicate)


async def update_presence():
    count = len(bot.guilds)
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name=f"Watching {count} server{'s' if count != 1 else ''}, (-chelp)",
        )
    )


@bot.event
async def on_ready():
    print("=" * 50)
    print(f"Logged in as {bot.user}")
    print(f"Servers: {len(bot.guilds)}")
    print("=" * 50)
    await update_presence()


@bot.event
async def on_guild_join(guild):
    await update_presence()


@bot.event
async def on_guild_remove(guild):
    await update_presence()


@bot.event
async def on_command_error(ctx, error):
    prefix = get_guild_config(ctx.guild.id)["prefix"] if ctx.guild else "-"
    cmd = ctx.command.name if ctx.command else ""

    if isinstance(error, commands.CheckFailure):
        if cmd == "p":
            await ctx.send(
                "❌ You don't have permission to use `-p`. You need **Manage Server** permission or be whitelisted by an admin."
            )
        else:
            await ctx.send(
                "❌ You don't have permission to use this command. Administrator access is required."
            )
    elif isinstance(error, commands.MissingRequiredArgument):
        if cmd == "p":
            await ctx.send(f"❌ Missing message. Usage: `{prefix}p <message>`")
        elif cmd == "setformat":
            await ctx.send(
                f"❌ Missing format text. Usage: `{prefix}setformat <format>`\nInclude `{{message}}` in your format so the ping text gets inserted, e.g. `{prefix}setformat @everyone {{message}}`"
            )
        elif cmd == "say":
            await ctx.send(
                f"❌ Missing arguments. Usage: `{prefix}say #channel <message>`"
            )
        elif cmd in ("awhitelistp", "rwhitelistp"):
            await ctx.send(f"❌ Missing user. Usage: `{prefix}{cmd} @user`")
        else:
            await ctx.send(f"❌ Missing required argument for `{prefix}{cmd}`.")
    elif isinstance(error, commands.BadArgument):
        if cmd == "say":
            await ctx.send(
                f"❌ Invalid channel. Usage: `{prefix}say #channel <message>`"
            )
        elif cmd in ("awhitelistp", "rwhitelistp"):
            await ctx.send(f"❌ Invalid user. Please mention a valid server member.")
        else:
            await ctx.send(f"❌ Invalid argument: `{error}`")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"❌ An unexpected error occurred: `{error}`")


@bot.command()
@p_allowed()
async def p(ctx, *, message):
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
            "❌ No channels configured. Use `setchannel1` and/or `setchannel2` first."
        )

    failed = []
    for channel in channels:
        try:
            for _ in range(cfg["lines"]):
                await channel.send(output)
        except discord.Forbidden:
            failed.append(channel.mention)
        except discord.HTTPException as e:
            failed.append(f"{channel.mention} (error: {e})")

    if failed:
        await ctx.send(
            f"❌ Failed to send to: {', '.join(failed)} — missing Send Messages permission."
        )
    else:
        await ctx.message.add_reaction("✅")


@bot.command()
@admin_only()
async def awhitelistp(ctx, member: discord.Member):
    cfg = get_guild_config(ctx.guild.id)

    if any(
        (e["id"] if isinstance(e, dict) else e) == member.id for e in cfg["whitelist"]
    ):
        return await ctx.send(f"⚠️ {member.mention} is already whitelisted for `-p`.")

    cfg["whitelist"].append({"id": member.id, "name": member.display_name})
    save_config()

    await ctx.send(
        f"✅ **{member.display_name}** has been added to the `-p` whitelist."
    )


@bot.command()
@admin_only()
async def rwhitelistp(ctx, member: discord.Member):
    cfg = get_guild_config(ctx.guild.id)

    entry = next(
        (
            e
            for e in cfg["whitelist"]
            if (e["id"] if isinstance(e, dict) else e) == member.id
        ),
        None,
    )

    if entry is None:
        return await ctx.send(f"⚠️ {member.mention} is not on the `-p` whitelist.")

    cfg["whitelist"].remove(entry)
    save_config()

    await ctx.send(
        f"✅ **{member.display_name}** has been removed from the `-p` whitelist."
    )


@bot.command()
@admin_only()
async def swhitelistp(ctx):
    cfg = get_guild_config(ctx.guild.id)

    whitelist = cfg["whitelist"]

    embed = discord.Embed(
        title="Whitelist — `-p` Command", color=discord.Color.orange()
    )

    if not whitelist:
        embed.description = "No users are currently whitelisted."
    else:
        lines = []
        for entry in whitelist:
            if isinstance(entry, dict):
                uid = entry["id"]
                saved_name = entry["name"]
            else:
                uid = entry
                saved_name = None

            member = ctx.guild.get_member(uid)
            display = member.display_name if member else (saved_name or f"Unknown")
            lines.append(f"• **{display}** (`{uid}`)")

        embed.description = "\n".join(lines)

    embed.set_footer(text="© Created by Steven Hudson (AI REFINED)")

    await ctx.send(embed=embed)


@bot.command()
@admin_only()
async def setchannel1(ctx, channel: discord.TextChannel):
    cfg = get_guild_config(ctx.guild.id)

    cfg["channel1"] = channel.id

    save_config()

    await ctx.send(f"✅ Channel 1 set to {channel.mention}")


@bot.command()
@admin_only()
async def setchannel2(ctx, channel: discord.TextChannel):
    cfg = get_guild_config(ctx.guild.id)

    cfg["channel2"] = channel.id

    save_config()

    await ctx.send(f"✅ Channel 2 set to {channel.mention}")


@bot.command()
@admin_only()
async def setlines(ctx, amount: int):
    if amount < 1 or amount > 10:
        return await ctx.send("Choose a value between 1 and 10.")

    cfg = get_guild_config(ctx.guild.id)

    cfg["lines"] = amount

    save_config()

    await ctx.send(f"✅ Lines changed to {amount}")


@bot.command()
@admin_only()
async def setprefix(ctx, prefix):
    cfg = get_guild_config(ctx.guild.id)

    cfg["prefix"] = prefix

    save_config()

    await ctx.send(f"✅ Prefix changed to `{prefix}`")


@bot.command()
@admin_only()
async def setformat(ctx, *, text):
    cfg = get_guild_config(ctx.guild.id)

    cfg["format"] = text

    save_config()

    await ctx.send("✅ Format updated.")


@bot.command()
@admin_only()
async def say(ctx, channel: discord.TextChannel, *, message):
    try:
        await channel.send(message)
        await ctx.message.add_reaction("✅")
    except discord.Forbidden:
        await ctx.send(
            f"❌ I don't have permission to send messages in {channel.mention}."
        )
    except discord.HTTPException as e:
        await ctx.send(f"❌ Failed to send message: `{e}`")


@bot.command()
@admin_only()
async def resetconfig(ctx):
    configs[str(ctx.guild.id)] = DEFAULT_SETTINGS.copy()

    save_config()

    await ctx.send("✅ Server configuration reset.")


@bot.command()
@admin_only()
async def viewconfig(ctx):
    cfg = get_guild_config(ctx.guild.id)

    embed = discord.Embed(title="Server Configuration", color=discord.Color.blue())

    embed.add_field(name="Prefix", value=cfg["prefix"], inline=False)

    embed.add_field(name="Lines", value=cfg["lines"], inline=False)

    ch1 = bot.get_channel(cfg["channel1"]) if cfg["channel1"] else None
    ch2 = bot.get_channel(cfg["channel2"]) if cfg["channel2"] else None

    def channel_value(ch):
        if not ch:
            return "Not set"
        return f"<#{ch.id}> (`{ch.id}`)"

    embed.add_field(name="Channel 1", value=channel_value(ch1), inline=False)

    embed.add_field(name="Channel 2", value=channel_value(ch2), inline=False)

    embed.add_field(name="Format", value=cfg["format"], inline=False)

    embed.set_footer(text="© Created by Steven Hudson (AI REFINED)")

    await ctx.send(embed=embed)


@bot.command()
async def chelp(ctx):
    prefix = get_guild_config(ctx.guild.id)["prefix"]

    embed = discord.Embed(
        title="Admin Ping Bot",
        description="Administrator-only utility bot",
        color=discord.Color.green(),
    )

    embed.add_field(
        name="Ping",
        value=f"`{prefix}p message` — Send a ping (Manage Server or whitelisted)",
        inline=False,
    )

    embed.add_field(
        name="Whitelist",
        value=f"""`{prefix}awhitelistp @user` — Add user to `-p` whitelist
`{prefix}rwhitelistp @user` — Remove user from `-p` whitelist
`{prefix}swhitelistp` — Show `-p` whitelist""",
        inline=False,
    )

    embed.add_field(
        name="Utility",
        value=f"""`{prefix}say #channel message` — Make bot send a message
`{prefix}setchannel1 #channel` — Set ping channel 1
`{prefix}setchannel2 #channel` — Set ping channel 2
`{prefix}setlines number` — Set how many times to repeat
`{prefix}setprefix newprefix` — Change command prefix
`{prefix}setformat text` — Set ping message format
`{prefix}viewconfig` — View server settings
`{prefix}resetconfig` — Reset server settings
`{prefix}chelp` — Show this menu""",
        inline=False,
    )

    embed.set_footer(text="© Created by Steven Hudson (AI REFINED)")

    await ctx.send(embed=embed)


bot.run(TOKEN)
