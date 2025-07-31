import discord, random, time
from typing import Optional
from discord.ext import commands
from discord import app_commands
import sqlite3

class Utils(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    def create_user(self, user_id, username, cursor):
        '''Gets user information and adds it into the database'''
    
        cursor.execute('INSERT INTO Users (id, username) VALUES (?, ?)',
                        (user_id, username))
    

    async def check_user_exists(self, interaction):
        '''Checks if user who used interaction exists, if not calls our
        create_user function and adds them to our exisitng db.'''

        user_id = interaction.user.id
        username = interaction.user.name

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()
        
        #Returns None if user does not exist in our DB
        cursor.execute('SELECT * FROM Users WHERE id = ?', (user_id,))
        result = cursor.fetchone()

        if result is None:
            self.create_user(user_id, username, cursor)

        connection.commit()
        connection.close()
    
    async def check_cooldown(self, interaction: discord.Interaction, target: Optional[int] = None):
        '''Checks if command is on cooldown for a user. For rob, additionality checks if target
        is on cooldown from being robbed'''

        name_reference = {
            'daily-candy': "daily_cooldown",
            'hourly-candy': "hourly_cooldown",
            'rob': "rob_cooldown"
        }

        time_reference = {
            'daily_cooldown': 86400,
            'hourly_cooldown': 3600,
            'rob_cooldown': 3600
        }

        command_name = interaction.command.name
        user_id = interaction.user.id

        cooldown_name = name_reference[command_name]
        cooldown_time = time_reference[cooldown_name]

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()
        
        cursor.execute(f'SELECT {cooldown_name} FROM Users WHERE id = ?', (user_id,))
        db_result = cursor.fetchone()

        #Logic for checking if target has been robbed and is on cooldown
        if target != None and cooldown_name == "rob_cooldown":
            cursor.execute(f'SELECT robbed_cooldown FROM Users WHERE id = ?', (target,))
            target_result = cursor.fetchone()
            target_result = target_result[0]

        connection.commit()
        connection.close()

        result = db_result[0]
        current_time = time.time() 


        if target == None:
            return result + cooldown_time >= current_time, current_time - (result + cooldown_time), cooldown_name, current_time

        if result + cooldown_time >= current_time or target_result + time_reference['rob_cooldown'] >= current_time:
            return True, current_time - (result + cooldown_time), cooldown_name, current_time

        return False, current_time - (result + cooldown_time), cooldown_name, current_time

        
    @app_commands.command(name="sync")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_commands(self, interaction: discord.Interaction):
        
        for cmd in self.bot.tree.walk_commands():
            print(f"[Slash Command] /{cmd.name} - {cmd.description}")
        
        await self.bot.tree.sync()
        await interaction.response.send_message("Commands synced!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))