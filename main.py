import discord
from discord.ext import commands
from discord import app_commands
import os
from dotenv import load_dotenv
import logging
import asyncio

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

bot = commands.Bot(command_prefix='?', description="Testing bot 123", intents=intents)

class Client(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix='?', intents=intents)

    async def setup_hook(self):
        self.tree.add_command(self.respond)
        await self.tree.sync()
        print("Commands synced")

    @bot.event
    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")

    @bot.event
    async def on_message(self, message):
        if message.author == self.user:
            return

        if message.content.startswith('$hello'):
            await message.channel.send('Hello!')
        await self.process_commands(message)

    @app_commands.command(name="respond", description="Bot responds with a message.")
    async def respond(self, interaction: discord.Interaction):
        await interaction.response.send_message("I am responding!")

bot = Client()
bot.run(token, log_handler=handler, log_level=logging.DEBUG)