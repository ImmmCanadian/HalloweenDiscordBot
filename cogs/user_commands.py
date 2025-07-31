import discord, random
from discord.ext import commands
from discord import app_commands
import sqlite3

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily-candy", description="Claim your daily candy!")
    async def dailycandy(self, interaction: discord.Interaction):

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(interaction)

        on_cooldown, time_left, cooldown_name, time = await utils_cog.check_cooldown(interaction)

        if not on_cooldown:

            reward = random.randint(100,200)

            connection = sqlite3.connect('./database.db')
            cursor = connection.cursor()
            cursor.execute(f'UPDATE users SET candy = candy + ?, {cooldown_name} = ? WHERE id = ?', (reward, time, interaction.user.id))
            connection.commit()
            connection.close()

            await interaction.response.send_message(f"You won {reward} candy!")
        
        else:
            await interaction.response.send_message(f"This command is still on cooldown for another {time_left} seconds.")

    @app_commands.command(name="rob", description="Steal someones candy!")
    async def rob(self, interaction: discord.Interaction, target: discord.Member):

        if interaction.user.id == target.id:
            await interaction.response.send_message(f"You can't rob yourself goofy.")
            return

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(interaction)

        on_cooldown, time_left, cooldown_name, time = await utils_cog.check_cooldown(interaction)
        
        if not on_cooldown:

            steal = random.randint(100,200)

            connection = sqlite3.connect('./database.db')
            cursor = connection.cursor()
            cursor.execute(f'UPDATE users SET candy = candy + ?, {cooldown_name} = ? WHERE id = ?', (steal, time, interaction.user.id))
            if cooldown_name == "rob_cooldown":
                cursor.execute(f'UPDATE users SET candy = candy - ?, robbed_cooldown = ? WHERE id = ?', (steal, time, target.id))
            connection.commit()
            connection.close()

            await interaction.response.send_message(f"You stole {steal} candy from {target.name}!")
        
        elif time_left < 0: #This would mean that it isnt on cooldown for the user but the target cant be robbed
            await interaction.response.send_message(f"This user can't be robbed right now.")
        else:
            await interaction.response.send_message(f"This command is still on cooldown for another {time_left} seconds.")

async def setup(bot: commands.Bot):
    await bot.add_cog(UserCommands(bot))