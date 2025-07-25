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

class Client(commands.Bot):
    
    def __init__(self):
        super().__init__(command_prefix='?', intents=intents)
    
    async def setup_hook(self):
         
        #Load our cogs
        await load_extensions()

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
    
    @commands.command(name="sync")
    @commands.is_owner()
    async def sync_commands(self, ctx: commands.Context):
        await load_extensions()

        for cmd in self.tree.walk_commands():
            print(f"[Slash Command] /{cmd.name} - {cmd.description}")
    
        await self.tree.sync()

        print("Synced new commands to guild.")

    

bot = Client()
bot.run(token, log_handler=handler, log_level=logging.DEBUG)