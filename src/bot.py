import discord
from discord.ext import commands, tasks
import sqlite3
from menza import get_meni
from itertools import count
from datetime import datetime
import os

conn = sqlite3.connect("menza.db")
cur = conn.cursor()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


def init_db():
    cur.execute(
        """\
        CREATE TABLE IF NOT EXISTS menza_subscriber
        (id INTEGER PRIMARY KEY, channel INTEGER, message_id INTEGER, menza_id INTEGER)
        """
    )
    conn.commit()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    init_db()
    refresh_menza_loop.start()


def gen_menza(menza_id: int) -> discord.Embed:
    tab1, tab2 = get_meni(menza_id)
    embed = discord.Embed(
        title="Menza",
        description=f"ID: *`{menza_id}`* | Ažurirano: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
    )
    if tab1 is not None:
        embed.add_field(name="Tablica 1", value="", inline=False)
        for item, i in zip(tab1, count()):
            embed.add_field(
                name=item[0],
                value="\n".join(item[1]),
                inline=True,
            )

    if tab2 is not None:
        embed.add_field(name="Tablica 2", value="", inline=False)
        for item, i in zip(tab2, count()):
            embed.add_field(
                name=item[0],
                value="\n".join(item[1]),
                inline=True,
            )
    return embed


async def refresh_menza():
    cur.execute("SELECT channel, message_id, menza_id FROM menza_subscriber")

    subs = cur.fetchall()

    for sub in subs:
        channel = bot.get_channel(sub[0])
        if channel is None:
            continue
        message = await channel.fetch_message(sub[1])  # type: ignore
        await message.edit(embed=gen_menza(sub[2]))


@bot.command()
async def menza(ctx, menza_id: int):
    await ctx.send(embed=gen_menza(menza_id))


@bot.command()
async def sub_menza(ctx, menza_id: int):
    cur.execute(
        "SELECT COUNT(*) FROM menza_subscriber WHERE channel = ? AND menza_id = ?",
        (ctx.channel.id, menza_id),
    )
    if cur.fetchone()[0] > 0:
        await ctx.send(
            embed=discord.Embed(
                title="Greška!",
                description=f"Postoji pretplata na meni za menzu {menza_id}",
            )
        )

    message = await ctx.send(embed=gen_menza(menza_id))

    cur.execute(
        "INSERT INTO menza_subscriber (channel, message_id, menza_id) VALUES (?, ?, ?)",
        (ctx.channel.id, message.id, menza_id),
    )
    conn.commit()

    await ctx.send(
        embed=discord.Embed(
            title="Uspjeh!",
            description=f"Pretplačeni na meni menze {menza_id}",
        )
    )


@bot.command()
async def unsub_menza(ctx, menza_id: int):
    cur.execute(
        "DELETE FROM menza_subscriber WHERE channel = ? AND menza_id = ?",
        (ctx.channel.id, menza_id),
    )
    conn.commit()

    await ctx.send(
        embed=discord.Embed(
            title="Uspjeh!",
            description=f"Odjavljeni sa pretplane na meni menze {menza_id}",
        )
    )


@bot.command()
async def dbg_refresh_menza(ctx):
    if ctx.author.id != 213246013958258688:
        return
    await refresh_menza()


@tasks.loop(hours=1)
async def refresh_menza_loop():
    await refresh_menza()


bot.run(os.getenv("DISCORD_BOT_TOKEN", ""))
