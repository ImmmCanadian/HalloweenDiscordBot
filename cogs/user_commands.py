import discord, random
from discord.ext import commands
from discord import app_commands
import sqlite3

async def create_user(user_id, username, cursor):
    '''Gets user information and adds it into the database'''
 
    cursor.execute('INSERT INTO Users (id, username) VALUES (?, ?)',
                       (user_id, username))
    

async def check_user_exists(interaction):
    '''Checks if user who used interaction exists, if not calls our
    create_user function and adds them to our exisitng db'''

    user_id = interaction.user.id
    username = interaction.user.name

    connection = sqlite3.connect('./database.db')
    cursor = connection.cursor()
    
    #Returns None if user does not exist in our DB
    cursor.execute('SELECT * FROM Users WHERE id = ?', (user_id,))
    result = cursor.fetchone()

    if result is None:
        await create_user(user_id, username, cursor)

    connection.commit()
    connection.close()


class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="daily-candy", description="Claim your daily candy!")
    async def dailycandy(self, interaction: discord.Interaction):

        await check_user_exists(interaction)

        reward = random.randint(100,200)

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()
        cursor.execute('UPDATE users SET candy = candy + ? WHERE id = ?', (reward, interaction.user.id))
        connection.commit()
        connection.close()

        await interaction.response.send_message(f"You won {reward} candy!")

async def setup(bot: commands.Bot):
    await bot.add_cog(UserCommands(bot))