import discord, random
from discord.ext import commands
from discord import app_commands

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="respond", description="Bot responds with a message.")
    @app_commands.checks.has_permissions(administrator=True)
    async def respond(self, interaction: discord.Interaction , string: str):
        try:
            await interaction.response.send_message(string)
        except Exception:
            print(Exception)

    
    @app_commands.command(name="daily-candy", description="Claim your daily candy!")
    async def dailycandy(self, interaction: discord.Interaction):
        reward = random.randint(1,2)
        #Insert SQL logic here
        await interaction.response.send_message(f"You won {reward} candy!")

async def setup(bot: commands.Bot):
    await bot.add_cog(UserCommands(bot))