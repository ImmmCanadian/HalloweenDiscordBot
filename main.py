import discord, os, logging, asyncio, random
#from user_commands import UserCommands
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

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='?', intents=intents)

    async def setup_hook(self):
        guild = discord.Object(id=1397169606891802784)
        self.tree.clear_commands(guild=guild)
        await self.load_extension("user_commands")
        self.tree.copy_global_to(guild=guild)
        await self.tree.sync(guild=guild)
        print("Commands synced")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")


bot = Client()
bot.run(token, log_handler=handler, log_level=logging.DEBUG)