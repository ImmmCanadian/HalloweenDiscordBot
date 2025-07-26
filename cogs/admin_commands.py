import discord, random
from discord.ext import commands
from discord import app_commands
import sqlite3

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="give-candy", description="Gives a user candy.")
    @app_commands.checks.has_permissions(administrator=True)
    async def givecandy(self, interaction: discord.Interaction , receipient: discord.Member, amount: int):
        try:
            await interaction.response.send_message("placeholder")
        except Exception as e:
            print(f"{e}")
    

    @commands.command(name="clear_commands")
    @commands.is_owner()
    async def clear_commands(self, ctx: commands.Context):
        guild = discord.Object(id=1397169606891802784)

        self.bot.tree.clear_commands(guild=guild)
        await self.bot.tree.sync(guild=guild)
        self.bot.tree.clear_commands(guild=None)
        await self.bot.tree.sync()
        await ctx.send("Cleared guild and global commands.")
        

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCommands(bot))