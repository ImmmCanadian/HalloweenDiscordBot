import discord, os, logging, asqlite, asyncio
from cogs import EXTENSIONS
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv


#Set the path to out current working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

#Load our token
load_dotenv('secret.env')
token = os.getenv('token')

#Creating log handler
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

intents = discord.Intents.none()
intents.members = True
intents.message_content = True
intents.messages = True

async def load_database():
    async with asqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            
            # Create Users tables if doesnt exist
            create_users_table_query = '''
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                candy INTEGER DEFAULT 0,
                rob_cooldown REAL DEFAULT 0,
                robbed_cooldown REAL DEFAULT 0,
                daily_cooldown REAL DEFAULT 0,
                hourly_cooldown REAL DEFAULT 0
            );
            '''
            await cursor.execute(create_users_table_query)

            # cursor.execute("DROP TABLE Store")
            # connection.commit()

            # Create Store tables if doesnt exist
            create_store_table_query = '''
            CREATE TABLE IF NOT EXISTS Store (
                name TEXT DEFAULT 0 PRIMARY KEY,
                role INTEGER DEFAULT 0,
                quantity TEXT DEFAULT 0,
                role_id INTEGER DEFAULT 0,
                price INTEGER DEFAULT 0
            );
            '''
            await cursor.execute(create_store_table_query)
            await connection.commit()

        print("Database connected successfully!")

class HalloweenBot(commands.Bot):
    
    def __init__(self):
        super().__init__(command_prefix='?', intents=intents)
    
    async def setup_hook(self):
         
        #Load our cogs
        for extension in EXTENSIONS:
            await bot.load_extension(extension)

        await load_database()
        
        @self.command(name="sync", hidden=True)
        @commands.is_owner()
        async def sync(ctx):
            """Sync slash commands - owner only"""
            # Reload all cogs
            for extension in EXTENSIONS:
                await self.reload_extension(extension)
            
            # Sync commands
            try:
                synced = await self.tree.sync()
                await ctx.send(f"Synced {len(synced)} command(s)")
                print(f"Synced {len(synced)} command(s)")
            except Exception as e:
                await ctx.send(f"Failed to sync: {e}")
                print(f"Failed to sync: {e}")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Unknown Error.")
        else:
            raise error
    


if __name__ == "__main__":
    bot = HalloweenBot()
    bot.run(token) #, log_handler=handler, log_level=logging.DEBUG