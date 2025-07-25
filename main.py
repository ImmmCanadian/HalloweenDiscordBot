import discord, os, logging, asyncio, random
#from user_commands import UserCommands
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import sqlite3

#Set the path to out current working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

#Load our token
load_dotenv('secret.env')
token = os.getenv('token')

#Creating log handler
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

#Loads all py files in cogs
async def load_extensions():
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                cog_name = filename[:-3]
                if cog_name in bot.cogs:
                    print(f'{cog_name} is already loaded.')
                else:
                    try:
                        await bot.load_extension(f'cogs.{cog_name}')
                        print(f'Loaded extension {cog_name}.')
                    except discord.ClientException as e:
                        print(f'Failed to load extension {cog_name}: {e}')

async def create_load_database():
    with sqlite3.connect('database.db') as connection:
        cursor = connection.cursor()

        # Create Users tables if doesnt exist
        create_users_table_query = '''
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            candy INTEGER DEFAULT 0,
            rob_cooldown TEXT DEFAULT 0,
            robbed_cooldown TEXT DEFAULT 0,
            daily_cooldown TEXT DEFAULT 0,
            hourly_cooldown TEXT DEFAULT 0
        );
        '''
        cursor.execute(create_users_table_query)
        connection.commit()

        # Create Store tables if doesnt exist
        create_store_table_query = '''
        CREATE TABLE IF NOT EXISTS Store (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            role INTEGER DEFAULT 0,
            quantity TEXT DEFAULT 0
        );
        '''
        cursor.execute(create_store_table_query)
        connection.commit()

        print("Database connected successfully!")

class Client(commands.Bot):
    
    def __init__(self):
        super().__init__(command_prefix='?', intents=intents)
    
    async def setup_hook(self):
         
        #Load our cogs
        await load_extensions()

        await create_load_database()

        #Add our manual sync command 
        self.tree.add_command(self.sync_commands)

        #Auto sync on startup
        #for cmd in self.tree.walk_commands():
            #print(f"[Slash Command] /{cmd.name} - {cmd.description}")
        #await self.tree.sync()
        #print("Synced new commands to guild.")

        for cmd in self.tree.walk_commands():
            print(f"[Slash Command] /{cmd.name} - {cmd.description}")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Unknown Error.")
        else:
            raise error
    
    @app_commands.command(name="sync")
    @app_commands.checks.has_permissions(administrator=True)
    async def sync_commands(self, interaction: discord.Interaction):
        await load_extensions()

        for cmd in self.tree.walk_commands():
            print(f"[Slash Command] /{cmd.name} - {cmd.description}")
    
        await self.tree.sync()

        print("Synced new commands.")

if __name__ == "__main__":
    bot = Client()
    bot.run(token, log_handler=handler, log_level=logging.DEBUG)