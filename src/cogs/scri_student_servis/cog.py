from cogs.scri_student_servis.web import Objava, get_jobs
import discord
from discord.ext import commands, tasks

ERROR_COLOR = 0xEA2915
SUCCESS_COLOR = 0x6BEA15
ONEOFF_COLOR = 0x15D6EA
REPEATING_COLOR = 0x9415EA


class ObjaveDatabase:
    def __init__(self, db) -> None:
        self.db = db

        self.db.cur.execute(
            """\
            CREATE TABLE IF NOT EXISTS scri_student_servis_objava
            (id INTEGER PRIMARY KEY, hash TEXT)
            """
        )
        self.db.cur.execute(
            """\
            CREATE TABLE IF NOT EXISTS scri_student_servis_subscriber
            (id INTEGER PRIMARY KEY, channel INTEGER)
            """
        )
        self.db.conn.commit()

    def check_objava(self, objava: Objava):
        self.db.cur.execute(
            """\
            SELECT COUNT(*) FROM scri_student_servis_objava WHERE hash = ?
            """,
            (objava.hash,),
        )
        return self.db.cur.fetchone()[0]

    def add_objava(self, objava: Objava):
        self.db.cur.execute(
            "INSERT INTO scri_student_servis_objava (hash) VALUES (?)",
            (objava.hash,),
        )
        self.db.conn.commit()

    def get_subs(self):
        self.db.cur.execute("SELECT channel FROM scri_student_servis_subscriber")
        return self.db.cur.fetchall()

    def count_subs(self, channel_id: int):
        self.db.cur.execute(
            "SELECT COUNT(*) FROM scri_student_servis_subscriber WHERE channel = ?",
            (channel_id,),
        )
        return self.db.cur.fetchone()[0]

    def add_sub(self, channel_id: int):
        self.db.cur.execute(
            "INSERT INTO scri_student_servis_subscriber (channel) VALUES (?)",
            (channel_id,),
        )
        self.db.conn.commit()

    def del_sub(self, channel_id: int):
        self.db.cur.execute(
            "DELETE FROM scri_student_servis_subscriber WHERE channel = ?",
            (channel_id,),
        )
        self.db.conn.commit()


class SSObjave(commands.Cog):
    def __init__(self, bot, db: ObjaveDatabase) -> None:
        self.bot = bot
        self.db = db

    def start(self):
        self.refresh_objave_loop.start()

    @tasks.loop(hours=1)
    async def refresh_objave_loop(self):
        await self._refresh_objave()

    def _gen_objava(self, objava: Objava, one_off: bool) -> discord.Embed:
        """
        obrok: T.Union[bool, str]
        smještaj: T.Union[bool, str]
        putni_trosak: T.Union[bool, str]
        """

        embed = discord.Embed(
            title=objava.naziv,
            url=objava.link,
            description=f"**{objava.kategorija}** | Objavljeno: *{objava.objavljeno}*",
            color=ONEOFF_COLOR if one_off else REPEATING_COLOR,
        )
        if objava.img:
            embed.set_image(url=objava.img)

        embed.add_field(name="", value=":office:", inline=False)
        embed.add_field(name="Poslodavac", value=objava.poslodavac, inline=True)
        embed.add_field(name="Mjesto", value=objava.mjesto, inline=True)

        embed.add_field(name="", value=":money_with_wings:", inline=False)
        embed.add_field(name="Cijena redovnog sata", value=objava.cijena_sat)
        embed.add_field(name="Rad nedjeljom", value=objava.cijena_sat_ned)

        embed.add_field(name="", value=":calendar:", inline=False)
        embed.add_field(name="Početak rada", value=objava.pocetak)
        embed.add_field(name="Završetak rada", value=objava.zavrsetak)

        embed.add_field(name="", value=":scroll:", inline=False)
        embed.add_field(name="Sanitarna knjižica", value=objava.sanitarna)
        embed.add_field(name="Obrok", value=objava.obrok)
        embed.add_field(name="Smještaj", value=objava.smještaj)
        embed.add_field(name="Putni trošak", value=objava.putni_trosak)
        return embed

    async def _refresh_objave(self):
        objave = get_jobs()
        for objava in objave:
            if self.db.check_objava(objava) > 0:
                continue
            if not objava.novo:
                continue

            for sub in self.db.get_subs():
                channel = self.bot.get_channel(sub[0])
                if channel is None:
                    continue
                await channel.send(embed=self._gen_objava(objava, one_off=False))

            self.db.add_objava(objava)

    @commands.command()
    async def ssobjave(self, ctx, n: int):
        objave = get_jobs()[-n:]
        for objava in objave:
            await ctx.send(embed=self._gen_objava(objava, True))

    @commands.command()
    async def ssobjave_sub(self, ctx):
        if self.db.count_subs(ctx.channel.id):
            await ctx.send(
                embed=discord.Embed(
                    title="Greška!",
                    description="Postoji pretplata student servis objave",
                    color=ERROR_COLOR,
                )
            )
            return

        self.db.add_sub(ctx.channel.id)

        await ctx.send(
            embed=discord.Embed(
                title="Uspjeh!",
                description="Pretplačeni na student servis objave",
                color=SUCCESS_COLOR,
            )
        )

    @commands.command()
    async def objave_unsub(self, ctx):
        self.db.del_sub(ctx.channel.id)

        await ctx.send(
            embed=discord.Embed(
                title="Uspjeh!",
                description="Odjavljeni sa pretplane na student servis objave",
                color=SUCCESS_COLOR,
            )
        )

    @commands.command()
    async def dbg_refresh_ssobjave(self, ctx):
        if ctx.author.id != 213246013958258688:
            return
        await self._refresh_objave()
