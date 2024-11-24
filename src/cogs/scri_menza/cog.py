import discord
from discord.ext import commands, tasks
from cogs.scri_menza.web import get_meni
from itertools import count
from datetime import datetime, timezone, timedelta
import time

ERROR_COLOR = 0xEA2915
SUCCESS_COLOR = 0x6BEA15
ONEOFF_COLOR = 0x15D6EA
REPEATING_COLOR = 0x9415EA


class MenzaDatabase:
    def __init__(self, db) -> None:
        self.db = db

        self.db.cur.execute(
            """\
            CREATE TABLE IF NOT EXISTS menza_subscriber
            (id INTEGER PRIMARY KEY, channel INTEGER, message INTEGER, menza TEXT)
            """
        )
        self.db.conn.commit()

    def get_subs(self):
        self.db.cur.execute("SELECT channel, message, menza FROM menza_subscriber")
        return self.db.cur.fetchall()

    def count_subs(self, channel_id: int, menza_name: str):
        self.db.cur.execute(
            "SELECT COUNT(*) FROM menza_subscriber WHERE channel = ? AND menza = ?",
            (channel_id, menza_name),
        )
        return self.db.cur.fetchone()[0]

    def add_sub(self, channel_id, message_id, menza_name):
        self.db.cur.execute(
            "INSERT INTO menza_subscriber (channel, message, menza) VALUES (?, ?, ?)",
            (channel_id, message_id, menza_name),
        )
        self.db.conn.commit()

    def del_sub(self, channel_id, menza_name):
        self.db.cur.execute(
            "DELETE FROM menza_subscriber WHERE channel = ? AND menza = ?",
            (channel_id, menza_name),
        )
        self.db.conn.commit()


class Menza(commands.Cog):
    def __init__(self, bot, db: MenzaDatabase) -> None:
        self.bot = bot
        self.db = db

    def start(self):
        self.refresh_menza_loop.start()

    @staticmethod
    def _gen_menza(menza_name: str, one_off: bool) -> discord.Embed:
        tab1, tab2 = get_meni(menza_name)
        datetime_gmt_2 = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=2)))
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

        for sub in self.db.get_subs():
            try:
                channel = self.bot.get_channel(sub[0])
                if channel is None:
                    continue
                message = await channel.fetch_message(sub[1])  # type: ignore
                await message.edit(embed=self._gen_menza(sub[2], False))
            except Exception as e:
                print("???", e.__class__.__name__, str(e))  # TODO: Ne ovo radit

    @commands.command()
    async def menza(self, ctx, menza_name: str):
        await ctx.send(embed=self._gen_menza(menza_name, True))

    @commands.command()
    async def menza_sub(self, ctx, menza_name: str):
        if self.db.count_subs(ctx.channel.id, menza_name):
            await ctx.send(
                embed=discord.Embed(
                    title="Greška!",
                    description=f"Postoji pretplata na meni menze {menza_name}",
                    color=ERROR_COLOR,
                )
            )
            return

        message = await ctx.send(embed=self._gen_menza(menza_name, False))

        self.db.add_sub(ctx.channel.id, message.id, menza_name)

        await ctx.send(
            embed=discord.Embed(
                title="Uspjeh!",
                description=f"Pretplačeni na meni menze {menza_name}",
                color=SUCCESS_COLOR,
            )
        )

    @commands.command()
    async def menza_unsub(self, ctx, menza_name: str):
        self.db.del_sub(ctx.channel.id, menza_name)

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
