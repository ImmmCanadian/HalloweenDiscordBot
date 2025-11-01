import discord, os, logging, asqlite, io
from cogs import EXTENSIONS
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
import asyncio
from datetime import date
from datetime import date

#Set the path to out current working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

#Load our token
load_dotenv('secret.env')
token = os.getenv('TOKEN')

intents = discord.Intents.none()
intents.members = True
intents.message_content = True
intents.messages = True
intents.guilds = True

def setup_logging():
    # Create logs directory if it doesn't exist
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Use dated filename from the start
    today = datetime.now().strftime('%Y-%m-%d')
    log_filename = os.path.join(log_dir, f'discord_bot_{today}.log')
    # Use dated filename from the start
    today = datetime.now().strftime('%Y-%m-%d')
    log_filename = os.path.join(log_dir, f'discord_bot_{today}.log')
    
    # Clear any existing handlers first
    logger = logging.getLogger()
    logger.handlers.clear()
    
    # Create file handler (append mode)
    file_handler = logging.FileHandler(
    # Clear any existing handlers first
    logger = logging.getLogger()
    logger.handlers.clear()
    
    # Create file handler (append mode)
    file_handler = logging.FileHandler(
        log_filename,
        encoding='utf-8',
        mode='a'  # Append, don't overwrite
        encoding='utf-8',
        mode='a'  # Append, don't overwrite
    )
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    logger.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    
    # Configure discord logger
    # Configure discord logger
    discord_logger = logging.getLogger('discord')
    discord_logger.setLevel(logging.DEBUG)
    discord_logger.propagate = True
    
    logger.info(f"Logging to {log_filename}")
    discord_logger.propagate = True
    
    logger.info(f"Logging to {log_filename}")
    
    return log_filename

# Setup logging
log_file = setup_logging()

async def load_database():
    async with asqlite.connect('database.db') as connection:
        async with connection.cursor() as cursor:
            
            # await cursor.execute("DROP TABLE Users")
            # await connection.commit()
            
            # await cursor.execute("DROP TABLE RaffleTickets")
            # await cursor.execute("DROP TABLE Raffle")
            # await connection.commit()
            
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
            bg_color TEXT DEFAULT 'purple',
            bg_image TEXT DEFAULT NULL,
            accusation_count INTEGER DEFAULT 0,
            interrogation_count INTEGER DEFAULT 0,
            wedgie_count INTEGER DEFAULT 0,
            flower_count INTEGER DEFAULT 0,
            skinnydip_count INTEGER DEFAULT 0,
            murder_count INTEGER DEFAULT 0,
            hero_count INTEGER DEFAULT 0,
            makeasacrifice_count INTEGER DEFAULT 0
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
                category TEXT DEFAULT 0
            );
            '''
            
            await cursor.execute(create_store_table_query)
            
            
            
            
            # Create Store tables if doesnt exist
            create_raffle_table_query = '''
            CREATE TABLE IF NOT EXISTS Raffle (
                item TEXT DEFAULT 0 PRIMARY KEY,
                winner_count INTEGER DEFAULT 0,
                ticket_cost INTEGER DEFAULT 1,
                time TEXT DEFAULT 0,
                been_raffled TEXT DEFAULT NULL
            );
            '''
            
            await cursor.execute(create_raffle_table_query)
            
            
            
            # Add this new table
            create_raffle_tickets_table_query = '''
            CREATE TABLE IF NOT EXISTS RaffleTickets (
                user_id INTEGER NOT NULL,
                raffle_item TEXT NOT NULL,
                ticket_count INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, raffle_item),
                FOREIGN KEY (raffle_item) REFERENCES Raffle(item),
                FOREIGN KEY (user_id) REFERENCES Users(id)
            );
            '''
            
            await cursor.execute(create_raffle_tickets_table_query)
            
            await connection.commit()

        print("Database connected successfully!")

class HalloweenBot(commands.Bot):
    
    def __init__(self):
        super().__init__(command_prefix=';', intents=intents)
        self.image_cache = {}
    
    async def setup_hook(self):
        
        self.preload_images()
        print("Cache keys:", self.image_cache.keys())
         
        #Load our cogs
        for extension in EXTENSIONS:
            await self.load_extension(extension)

        await load_database()
        
        @self.command(name="sync", hidden=True)
        @commands.is_owner()
        async def sync(ctx):
            """Sync slash commands - owner only"""
            
            logger = logging.getLogger(__name__)
            logger.info(f"Syncing commands")
            
            # Reload all cogs
            for extension in EXTENSIONS:
                try:
                    await self.reload_extension(extension)
                except Exception as e:
                    logger.info(f"Failed to sync commands")
                    return
            
            # Sync the commands
            try:
                synced = await self.tree.sync()
                logger.info(f"Synced {len(synced)} command(s)")
                
                await ctx.send(f"Synced {len(synced)} command(s)")
            except Exception as e:
                await ctx.send(f"Failed to sync.")
                logger.error(f"Failed to sync: {e}")
    
    def preload_images(self): 
        files = {
            "start.png": "images/start.png",
            "heads.gif": "images/heads.gif",
            "tails.gif": "images/tails.gif",
            "side.gif": "images/side.gif",
            "end-heads.webp": "images/end-heads.webp",
            "end-tails.webp": "images/end-tails.webp",
            "end-side.webp": "images/end-side.webp"
        }

        for key, path in files.items():
            with open(path, "rb") as f:
                self.image_cache[key] = f.read()

        print(f"Preloaded {len(self.image_cache)} images into memory.")


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
    bot.run(token) 
