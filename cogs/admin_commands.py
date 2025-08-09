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
    
    @app_commands.command(name="admin-help", description="Check what all of your commands do.")
    @app_commands.checks.has_permissions(administrator=True)
    async def adminhelp(self, interaction: discord.Interaction):

        user_id = interaction.user.id
        user_name = interaction.user.name
        user = interaction.user

        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(user_id, user_name)

        embed = discord.Embed(title=f"Help!", description="These are all of the available admin commands! If a command throws an error, make sure to read what should be entered into the field or ask Noah", color=0x9B59B6)
        embed.set_author(
            name=f"{user.name}",
            icon_url=user.display_avatar.url)

        embed.add_field(name="Give Candy",value=f"Give a user candy.\n",inline=False)
        embed.add_field(name="Remove Candy",value=f"Remove a users candy\n",inline=False)
        embed.add_field(name="Add store item",value=f"Lets you add a store item. Make sure to put the role name without the @ or None if it is not a role. To add quantity follow the same instructions and simply put the quantity you want added into the quantity field\n",inline=False)
        embed.add_field(name="Remove store item",value=f"Lets you remove a store item. If you want a store item gone simply set the quantity to 999 (enough that the current stock goes to 0). If you want less quantity, put in the quantity you want removed.\n",inline=False)
        embed.add_field(name="Sync",value=f"Resyncs commands to the bot. You should never need to use this, this is for me to refresh code without resetting the bot.",inline=False)
    
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # @commands.command(name="clear_commands")
    # @commands.is_owner()
    # async def clear_commands(self, ctx: commands.Context):
    #     guild = discord.Object(id=1397169606891802784)

    #     self.bot.tree.clear_commands(guild=guild)
    #     await self.bot.tree.sync(guild=guild)
    #     self.bot.tree.clear_commands(guild=None)
    #     await self.bot.tree.sync()
    #     await ctx.send("Cleared guild and global commands.")
        

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCommands(bot))