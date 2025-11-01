import discord, random, time, asqlite
from typing import Optional
from discord.ext import commands
import datetime
import zoneinfo


class Utils(commands.Cog):
    @staticmethod
    def is_pst_blocked():
        """
        Returns True if current time is after October 31, 2025, 11:59 PM PST.
        """
        
        # Set cutoff: October 31, 2025, 11:59:59 PM PST
        cutoff = datetime.datetime(2025, 10, 31, 23, 59, 59, tzinfo=zoneinfo.ZoneInfo("America/Los_Angeles"))
        now = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles"))
        return now > cutoff

    name_reference = {
            'weekly': "weekly_cooldown",
            'daily': "daily_cooldown",
            'hourly': "hourly_cooldown",
            'rob': "rob_cooldown"
        }

    time_reference = {
            'weekly_cooldown': 604800,
            'daily_cooldown': 86400,
            'hourly_cooldown': 3600,
            'rob_cooldown': 21600
        }

    def __init__(self, bot):
        self.bot = bot

    async def create_user(self, user_id, username, cursor):
        '''Gets user information and adds it into the database'''
    
        await cursor.execute('INSERT INTO Users (id, username) VALUES (?, ?)',
                        (user_id, username))
    

    async def check_user_exists(self, user_id, user_name):
        '''Checks if user who used interaction exists, if not calls our
        create_user function and adds them to our exisitng db.'''

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                
                #Returns None if user does not exist in our DB
                await cursor.execute('SELECT * FROM Users WHERE id = ?', (user_id,))
                result = await cursor.fetchone()

                if result is None:
                    await self.create_user(user_id, user_name, cursor)

                await connection.commit()
    
    async def check_cooldown(self, interaction: discord.Interaction, target: Optional[discord.Member] = None):
        '''Checks if command is on cooldown for a user. For rob, additionality checks if target
        is on cooldown from being robbed'''

        data = {
            'user_on_cooldown': 0,
            'target_on_cooldown': 0,
            'user_time_left': 0,
            'target_time_left': 0,
            'cooldown_name': 0, 
            'executed_time': 0
        }

        command_name = interaction.command.name
        user_id = interaction.user.id

        cooldown_name = self.name_reference[command_name]
        cooldown_time = self.time_reference[cooldown_name]

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                
                await cursor.execute(f'SELECT {cooldown_name} FROM Users WHERE id = ?', (user_id,))
                db_result = await cursor.fetchone()

                #Logic for checking if target has been robbed and is on cooldown
                target_result = None
                if target != None and cooldown_name == "rob_cooldown":
                    await cursor.execute(f'SELECT robbed_cooldown FROM Users WHERE id = ?', (target.id,))
                    target_result = await cursor.fetchone()
                    target_result = target_result[0] if target_result else 0

                await connection.commit()

        result = db_result[0] if db_result else 0
        current_time = time.time() 

        data['user_on_cooldown'] = result + cooldown_time >= current_time
        data['user_time_left'] = current_time - (result + cooldown_time)
        data['cooldown_name'] = cooldown_name
        data['executed_time'] = current_time

        #Check for normal commands
        if target == None:
            return data

        data['target_on_cooldown'] = target_result + self.time_reference['rob_cooldown'] >= current_time
        data['target_time_left'] = current_time - (target_result + self.time_reference['rob_cooldown'])
            
        return data
    
    def convert_cooldown_into_time(self, cooldown_name, cooldown_exec_time):
        value = time.time() - (self.time_reference[cooldown_name] + cooldown_exec_time)
        if value < 0:
            return f"Next reset is in {self.convert_seconds_to_string(value)}."
        else:
            return "This command is ready!"

    def convert_seconds_to_string(self, time_left):
        time_left = abs(int(time_left)) 
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        seconds = time_left % 60
        return f"{hours:02}:{minutes:02}:{seconds:02}" 

    # @app_commands.command(name="testing")
    # @app_commands.checks.has_permissions(administrator=True)
    # async def testing(self, interaction: discord.Interaction):
        
    #     async with asqlite.connect('./database.db') as connection:
    #         async with connection.cursor() as cursor:

    #             await cursor.execute(f'UPDATE users SET rob_cooldown = ? WHERE id = ?', (0, interaction.user.id))
                    
    #             await connection.commit()
        
    #     await interaction.response.send_message("This is after sync!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))