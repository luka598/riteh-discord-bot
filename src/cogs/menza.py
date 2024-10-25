import sqlite3
import discord
from discord.ext import commands, tasks
from scri import get_meni
from itertools import count
from datetime import datetime, timezone, timedelta
import time

ERROR_COLOR = 0xEA2915
SUCCESS_COLOR = 0x6BEA15
ONEOFF_COLOR = 0x15D6EA
REPEATING_COLOR = 0x9415EA


class Menza(commands.Cog):
    def __init__(self, bot) -> None:
        self.bot = bot

        self.conn = sqlite3.connect("menza.db")
        self.cur = self.conn.cursor()

    def start(self):
        self.init_db()
        self.refresh_menza_loop.start()

    def init_db(self):
        self.cur.execute(
            """\
            CREATE TABLE IF NOT EXISTS menza_subscriber
            (id INTEGER PRIMARY KEY, channel INTEGER, message INTEGER, menza TEXT)
            """
        )
        self.conn.commit()

    @staticmethod
    def _gen_menza(menza_name: str, one_off: bool) -> discord.Embed:
        tab1, tab2 = get_meni(menza_name)
        datetime_gmt_2 = datetime.now(timezone.utc).astimezone(
            timezone(timedelta(hours=2))
        )
        embed = discord.Embed(
            title="Menza",
            description=f"ID: *`{menza_name}`* | Ažurirano: `{datetime_gmt_2.strftime('%Y-%m-%d %H:%M:%S')}`",
            color=ONEOFF_COLOR if one_off else REPEATING_COLOR,
        )

        def add_tab(tab, tab_name):
            embed.add_field(name=tab_name, value="", inline=False)
            for meni, i in zip(tab, count()):
                embed.add_field(
                    name=meni[0],
                    value="\n".join([item[1] + " " + item[0] for item in meni[1]]),
                    inline=True,
                )
                if i % 2 == 1:
                    embed.add_field(name="", value="", inline=False)

        if tab1 is not None:
            add_tab(tab1, "**=== Tablica 1 - Ručak ===**")

        if tab2 is not None:
            add_tab(tab2, "**=== Tablica 2 - Večera ===**")

        return embed

    async def _refresh_menza(self):
        print("Refresh", time.time())
        self.cur.execute("SELECT channel, message, menza FROM menza_subscriber")

        subs = self.cur.fetchall()

        for sub in subs:
            try:
                channel = self.bot.get_channel(sub[0])
                if channel is None:
                    continue
                message = await channel.fetch_message(sub[1])  # type: ignore
                await message.edit(embed=self._gen_menza(sub[2], False))
            except Exception:
                pass  # TODO: Ne ovo radit

    @commands.command()
    async def menza(self, ctx, menza_name: str):
        await ctx.send(embed=self._gen_menza(menza_name, True))

    @commands.command()
    async def menza_sub(self, ctx, menza_name: str):
        self.cur.execute(
            "SELECT COUNT(*) FROM menza_subscriber WHERE channel = ? AND menza = ?",
            (ctx.channel.id, menza_name),
        )
        res = self.cur.fetchone()
        if res[0] > 0:
            print("Not ok!", res)
            await ctx.send(
                embed=discord.Embed(
                    title="Greška!",
                    description=f"Postoji pretplata na meni menze {menza_name}",
                    color=ERROR_COLOR,
                )
            )
            return
        print("OK!", res)

        message = await ctx.send(embed=self._gen_menza(menza_name, False))

        self.cur.execute(
            "INSERT INTO menza_subscriber (channel, message, menza) VALUES (?, ?, ?)",
            (ctx.channel.id, message.id, menza_name),
        )
        self.conn.commit()

        await ctx.send(
            embed=discord.Embed(
                title="Uspjeh!",
                description=f"Pretplačeni na meni menze {menza_name}",
                color=SUCCESS_COLOR,
            )
        )

    @commands.command()
    async def menza_unsub(self, ctx, menza_name: str):
        self.cur.execute(
            "DELETE FROM menza_subscriber WHERE channel = ? AND menza = ?",
            (ctx.channel.id, menza_name),
        )
        self.conn.commit()

        await ctx.send(
            embed=discord.Embed(
                title="Uspjeh!",
                description=f"Odjavljeni sa pretplane na meni menze {menza_name}",
                color=SUCCESS_COLOR,
            )
        )

    @commands.command()
    async def dbg_refresh_menza(self, ctx):
        if ctx.author.id != 213246013958258688:
            return
        await self._refresh_menza()

    @tasks.loop(hours=1)
    async def refresh_menza_loop(self):
        print("Refresh loop", time.time())
        await self._refresh_menza()
