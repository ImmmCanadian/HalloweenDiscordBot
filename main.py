import discord, os, logging, asqlite, asyncio
from cogs import EXTENSIONS
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime

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
intents.guilds = True

# Create timestamped log file
def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create timestamped filename
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    log_filename = os.path.join(log_dir, f'discord_{timestamp}.log')
    
    # Setup logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8', mode='w'),
            logging.StreamHandler()  # This will also print to console
        ]
    )
    
    # Set discord.py logging level
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.INFO)
    
    print(f"Logging to: {log_filename}")
    return log_filename

# Setup logging
log_file = setup_logging()

async def load_database():
    async with asqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            
            await cursor.execute("DROP TABLE Users")
            await connection.commit()
            
            # Create Users tables if doesnt exist
            create_users_table_query = '''
            CREATE TABLE IF NOT EXISTS Users (
                id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                candy INTEGER DEFAULT 0,
                bank INTEGER DEFAULT 0,
                rob_cooldown REAL DEFAULT 0,
                robbed_cooldown REAL DEFAULT 0,
                daily_cooldown REAL DEFAULT 0,
                hourly_cooldown REAL DEFAULT 0,
                weekly_cooldown REAL DEFAULT 0,
                roles TEXT DEFAULT '[]',
                pets TEXT DEFAULT '[]'
            );
            '''
            await cursor.execute(create_users_table_query)

            # await cursor.execute("DROP TABLE Store")
            # await connection.commit()

            # Create Store tables if doesnt exist
            create_store_table_query = '''
            CREATE TABLE IF NOT EXISTS Store (
                name TEXT DEFAULT 0 PRIMARY KEY,
                role INTEGER DEFAULT 0,
                quantity TEXT DEFAULT 0,
                role_id INTEGER DEFAULT 0,
                price INTEGER DEFAULT 0,
                pet TEXT DEFAULT 0
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
        logging.info(f"Bot logged in as {self.user} (ID: {self.user.id})")
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        
        for guild in self.guilds:
            logging.info(f"Guild: {guild.name} (ID: {guild.id})")
            logging.info(f"  Roles: {[role.name for role in guild.roles]}")
            print(f"Guild: {guild.name} (ID: {guild.id})")
            print(f"  Roles: {[role.name for role in guild.roles]}")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            await ctx.send("Unknown Error.")
        else:
            raise error
    


if __name__ == "__main__":
    bot = HalloweenBot()
    bot.run(token) #, log_handler=handler, log_level=logging.DEBUG