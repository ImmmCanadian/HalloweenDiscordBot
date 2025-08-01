import discord, random
from discord.ext import commands
from discord import app_commands
import sqlite3

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="give-candy", description="Gives a user candy.")
    @app_commands.checks.has_permissions(administrator=True)
    async def givecandy(self, interaction: discord.Interaction , target: discord.Member, amount: int):

        target_id = target.id
        target_name = target.name

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(target_id, target_name)

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()

        cursor.execute(f'UPDATE users SET candy = candy + ? WHERE id = ?', (amount, target.id))
            
        connection.commit()
        connection.close()

        await interaction.response.send_message(f"You gave {amount} candy to {target.name}!")
    
    @app_commands.command(name="remove-candy", description="Take a users candy.")
    @app_commands.checks.has_permissions(administrator=True)
    async def removecandy(self, interaction: discord.Interaction , target: discord.Member, amount: int):

        target_id = target.id
        target_name = target.name

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(target_id, target_name)

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()

        cursor.execute(f'UPDATE users SET candy = candy - ? WHERE id = ?', (amount, target.id))
            
        connection.commit()
        connection.close()

        await interaction.response.send_message(f"You took {amount} candy from {target.name}!")


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