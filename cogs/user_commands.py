import discord, random
from discord.ext import commands
from discord import app_commands

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily-candy", description="Claim your daily candy!")
    async def dailycandy(self, interaction: discord.Interaction):
        reward = random.randint(100,200)
        #Insert SQL logic here
        await interaction.response.send_message(f"You won {reward} candy!")

async def setup(bot: commands.Bot):
    await bot.add_cog(UserCommands(bot))