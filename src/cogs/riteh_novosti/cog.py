import discord
from cogs.riteh_novosti.web import RitehNovost, get_novosti
from discord.ext import commands, tasks

ERROR_COLOR = 0xEA2915
SUCCESS_COLOR = 0x6BEA15
ONEOFF_COLOR = 0x15D6EA
REPEATING_COLOR = 0x9415EA


class NovostiDatabase:
    def __init__(self, db) -> None:
        self.db = db

        self.db.cur.execute(
            """\
            CREATE TABLE IF NOT EXISTS riteh_novost
            (id INTEGER PRIMARY KEY, hash TEXT)
            """
        )
        self.db.cur.execute(
            """\
            CREATE TABLE IF NOT EXISTS riteh_novost_subscriber
            (id INTEGER PRIMARY KEY, channel INTEGER)
            """
        )
        self.db.conn.commit()

    def check_novost(self, novost: RitehNovost):
        self.db.cur.execute(
            """\
            SELECT COUNT(*) FROM riteh_novost WHERE hash = ?
            """,
            (novost.hash,),
        )
        return self.db.cur.fetchone()[0]

    def add_novost(self, novost: RitehNovost):
        self.db.cur.execute(
            "INSERT INTO riteh_novost (hash) VALUES (?)",
            (novost.hash,),
        )
        self.db.conn.commit()

    def get_subs(self):
        self.db.cur.execute("SELECT channel FROM riteh_novost_subscriber")
        return self.db.cur.fetchall()

    def count_subs(self, channel_id: int):
        self.db.cur.execute(
            "SELECT COUNT(*) FROM riteh_novost_subscriber WHERE channel = ?",
            (channel_id,),
        )
        return self.db.cur.fetchone()[0]

    def add_sub(self, channel_id: int):
        self.db.cur.execute(
            "INSERT INTO riteh_novost_subscriber (channel) VALUES (?)",
            (channel_id,),
        )
        self.db.conn.commit()

    def del_sub(self, channel_id: int):
        self.db.cur.execute(
            "DELETE FROM riteh_novost_subscriber WHERE channel = ?",
            (channel_id,),
        )
        self.db.conn.commit()


class Novosti(commands.Cog):
    def __init__(self, bot, db: NovostiDatabase) -> None:
        self.bot = bot
        self.db = db

    def start(self):
        self.refresh_novosti_loop.start()

    @tasks.loop(hours=1)
    async def refresh_novosti_loop(self):
        await self._refresh_novosti()

    def _gen_novost(self, novost: RitehNovost, one_off: bool) -> discord.Embed:
        embed = discord.Embed(
            title=novost.title,
            url=novost.link,
            description=f"*{novost.category}*",
            color=ONEOFF_COLOR if one_off else REPEATING_COLOR,
        )
        if novost.img is not None:
            embed.set_image(url=novost.img)
        embed.add_field(name="", value=novost.summary)
        return embed

    async def _refresh_novosti(self):
        novosti = get_novosti()
        for novost in novosti:
            if self.db.check_novost(novost) > 0:
                continue

            for sub in self.db.get_subs():
                channel = self.bot.get_channel(sub[0])
                if channel is None:
                    continue
                await channel.send(embed=self._gen_novost(novost, one_off=False))

            self.db.add_novost(novost)

    @commands.command()
    async def novosti(self, ctx, n: int):
        novosti = get_novosti()[-n:]
        for novost in novosti:
            await ctx.send(embed=self._gen_novost(novost, True))

    @commands.command()
    async def novosti_sub(self, ctx):
        if self.db.count_subs(ctx.channel.id):
            await ctx.send(
                embed=discord.Embed(
                    title="Greška!",
                    description="Postoji pretplata novosti",
                    color=ERROR_COLOR,
                )
            )
            return

        self.db.add_sub(ctx.channel.id)

        await ctx.send(
            embed=discord.Embed(
                title="Uspjeh!",
                description="Pretplačeni na novosti",
                color=SUCCESS_COLOR,
            )
        )

    @commands.command()
    async def novosti_unsub(self, ctx):
        self.db.del_sub(ctx.channel.id)

        await ctx.send(
            embed=discord.Embed(
                title="Uspjeh!",
                description="Odjavljeni sa pretplane na novosti",
                color=SUCCESS_COLOR,
            )
        )

    @commands.command()
    async def dbg_refresh_novosti(self, ctx):
        if ctx.author.id != 213246013958258688:
            return
        await self._refresh_novosti()
