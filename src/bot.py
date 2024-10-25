import discord
from discord.ext import commands
import os

from cogs.menza import Menza

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    menza_cog = Menza(bot)
    await bot.add_cog(menza_cog)
    menza_cog.start()

    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="!menza riteh"))


bot.run(os.getenv("DISCORD_BOT_TOKEN", ""))
