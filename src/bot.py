import discord
from discord.ext import commands
import os

from cogs.scri_menza.cog import Menza, MenzaDatabase
from cogs.riteh_novosti.cog import Novosti, NovostiDatabase
from cogs.scri_student_servis.cog import SSObjave, ObjaveDatabase
from db import Database

intents = discord.Intents.default()
intents.message_content = True

db = Database("bot.db")
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    menza_cog = Menza(bot, MenzaDatabase(db))
    await bot.add_cog(menza_cog)
    menza_cog.start()

    novosti_cog = Novosti(bot, NovostiDatabase(db))
    await bot.add_cog(novosti_cog)
    novosti_cog.start()

    ssobjave_cog = SSObjave(bot, ObjaveDatabase(db))
    await bot.add_cog(ssobjave_cog)
    ssobjave_cog.start()

    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="!menza riteh"))


bot.run(os.getenv("DISCORD_BOT_TOKEN", ""))
