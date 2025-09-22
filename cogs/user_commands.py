import discord, random, asqlite, json
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import aiohttp, io, asyncio
import logging
from pathlib import Path
import os

logger = logging.getLogger(__name__)

ROB_CHOICES = ["SUCCEED", "FAIL"]
ROB_WEIGHTS = [0.7,0.3]

class UserCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    async def candy_cooldown(self, interaction):
        user_id = interaction.user.id
        user_name = interaction.user.name

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(user_id, user_name)

        cooldown_data = await utils_cog.check_cooldown(interaction)
        cooldown_name = cooldown_data['cooldown_name']
        executed_time = cooldown_data['executed_time']
        user_time_left = cooldown_data['user_time_left']

        if not cooldown_data['user_on_cooldown']:

            if cooldown_name == "daily_cooldown":
                reward = random.randint(1000, 2000)
            elif cooldown_name == "weekly_cooldown":
                reward = random.randint(5000, 10000)
            else:
                reward = random.randint(100, 200)

            async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(f'UPDATE users SET candy = candy + ?, {cooldown_name} = ? WHERE id = ? RETURNING candy', (reward, executed_time, user_id))
                    result = await cursor.fetchone()
                    await connection.commit()
                    new_candy_amount = result[0]
                    logger.info(f"DB_UPDATE: Added {reward} candy to user: {user_name}'s id: {user_id} total: {new_candy_amount}")

            await interaction.response.send_message(f"You got {reward} candy!")
        else:
            await interaction.response.send_message(f"This command is still on cooldown for another {utils_cog.convert_seconds_to_string(user_time_left)} hours.")

    @app_commands.command(name="daily-candy", description="Claim your daily candy!")
    async def dailycandy(self, interaction: discord.Interaction):
        await self.candy_cooldown(interaction)
    
    @app_commands.command(name="hourly-candy", description="Claim your hourly candy!")
    async def hourlycandy(self, interaction: discord.Interaction):
        await self.candy_cooldown(interaction)
    
    @app_commands.command(name="weekly-candy", description="Claim your weekly candy!")
    async def weeklycandy(self, interaction: discord.Interaction):
        await self.candy_cooldown(interaction)
        
        
    async def bank(self, interaction: discord.Interaction, amount: int):
        user_id = interaction.user.id
        user_name = interaction.user.name
        
        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(user_id, user_name)
        
        if interaction.command.name == "deposit":
            command_name = "deposit"
        else:
            command_name = "withdraw"
        
        async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    if command_name == "deposit":
                        await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (user_id,))
                    else:
                        await cursor.execute(f'SELECT bank FROM Users WHERE id = ?', (user_id,))
                    user_candy_amount = await cursor.fetchone()
                    user_candy_amount= user_candy_amount[0]
                    
                    if user_candy_amount < amount:
                        await interaction.response.send_message(f"You can't {command_name} candy that you dont got.")
                    elif command_name == "deposit":
                        await cursor.execute(f'UPDATE users SET candy = candy - ?, bank = bank + ? WHERE id = ? RETURNING candy, bank', (amount, amount, user_id))
                        result = await cursor.fetchone()
                        await connection.commit()
                        new_candy_amount, new_bank_amount = result[0], result[1]
                        await interaction.response.send_message(f"You have deposited {amount} candy successfully.")
                        logger.info(f"DB_UPDATE: Moved {amount} candy to user: {user_name}'s id: {user_id} bank. Candy balance: {new_candy_amount} Bank Balance: {new_bank_amount}")
                    else:
                        await cursor.execute(f'UPDATE users SET candy = candy + ?, bank = bank - ? WHERE id = ? RETURNING candy, bank', (amount, amount, user_id))
                        result = await cursor.fetchone()
                        await connection.commit()
                        new_candy_amount, new_bank_amount = result[0], result[1]
                        await interaction.response.send_message(f"You have withdrawn {amount} candy successfully.")
                        logger.info(f"DB_UPDATE: Moved {amount} candy to user: {user_name}'s id: {user_id} candy balance. Candy balance: {new_candy_amount} Bank Balance: {new_bank_amount}")
                        
                    
        
    @app_commands.command(name="deposit", description="Deposit your candy! Makes it safe from robbing.")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        await self.bank(interaction, amount)
          
    @app_commands.command(name="withdraw", description="Withdraw your candy!")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        await self.bank(interaction, amount)

    @app_commands.command(name="send-candy", description="Send candy to someone.")
    async def sendycandy(self, interaction: discord.Interaction, target: discord.Member, amount: int):

        user_id = interaction.user.id
        user_name = interaction.user.name
        target_id = target.id
        target_name = target.name

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(user_id, user_name)
        await utils_cog.check_user_exists(target_id, target_name)

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:

                await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (user_id,))
                user_candy_amount = await cursor.fetchone()
                user_candy_amount= user_candy_amount[0]

                if user_candy_amount >= amount:
                    await cursor.execute(f'UPDATE users SET candy = candy - ? WHERE id = ? RETURNING candy', (amount, user_id))
                    user_candy_amount = await cursor.fetchone()
                    user_candy_amount= user_candy_amount[0]
                    await cursor.execute(f'UPDATE users SET candy = candy + ? WHERE id = ? RETURNING candy', (amount, target_id))
                    target_candy_amount = await cursor.fetchone()
                    target_candy_amount= target_candy_amount[0]
                    await interaction.response.send_message(f"You gave {amount} candy to {target.mention}!")
                    
                
                await connection.commit()
                logger.info(f"DB_UPDATE: Sent {amount} candy From user: {user_name}'s id: {user_id} to target: {target_name}'s id: {target_id}. User balance: {user_candy_amount} Target balance: {target_candy_amount}")

        if user_candy_amount < amount:
            await interaction.response.send_message(f"You dont have enough candy to do that.")

    @app_commands.command(name="balance", description="Check your candy balance.")
    async def balance(self, interaction: discord.Interaction):

        user_id = interaction.user.id
        user_name = interaction.user.name

        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(user_id, user_name)

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:

                await cursor.execute(f'SELECT candy, bank FROM Users WHERE id = ?', (user_id,))
                user_candy_amount = await cursor.fetchone()
                 
                await connection.commit()
                
        bank_balance= user_candy_amount[1]
        user_candy_amount= user_candy_amount[0]
        
        await interaction.response.send_message(f"You have {user_candy_amount} pieces of candy in your pockets. \nYou have {bank_balance} in your bank!")

    @app_commands.command(name="cooldowns", description="Check all of your cooldowns.")
    async def cooldowns(self, interaction: discord.Interaction):

        user_id = interaction.user.id
        user_name = interaction.user.name
        user = interaction.user

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(user_id, user_name)

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:

                await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (user_id,))
                user_candy_amount = await cursor.fetchone()
                await cursor.execute(f'SELECT rob_cooldown FROM Users WHERE id = ?', (user_id,))
                rob_cooldown = await cursor.fetchone()
                await cursor.execute(f'SELECT robbed_cooldown FROM Users WHERE id = ?', (user_id,))
                robbed_cooldown = await cursor.fetchone()
                await cursor.execute(f'SELECT daily_cooldown FROM Users WHERE id = ?', (user_id,))
                daily_cooldown = await cursor.fetchone()
                await cursor.execute(f'SELECT hourly_cooldown FROM Users WHERE id = ?', (user_id,))
                hourly_cooldown = await cursor.fetchone()
                
                await connection.commit()

        user_candy_amount= user_candy_amount[0]
        rob_cooldown= rob_cooldown[0]
        robbed_cooldown= robbed_cooldown[0]
        daily_cooldown= daily_cooldown[0]
        hourly_cooldown= hourly_cooldown[0]

        hourly_name= "hourly_cooldown"
        daily_name= "daily_cooldown"
        rob_name= "rob_cooldown"
        robbed_name= "rob_cooldown"
        
        cooldown_embed = discord.Embed(title=f"Command Cooldowns", color=0x9B59B6)
        cooldown_embed.set_author(
            name=f"{user.name}",
            icon_url=user.display_avatar.url)
            
        cooldown_embed.add_field(name="Candy Balance",value=f"{user_candy_amount}\n")
        cooldown_embed.add_field(name="Hourly Cooldown",value=f"{utils_cog.convert_cooldown_into_time(hourly_name, hourly_cooldown)}\n",inline=False)
        cooldown_embed.add_field(name="Daily Cooldown",value=f"{utils_cog.convert_cooldown_into_time(daily_name, daily_cooldown)}\n",inline=False)
        cooldown_embed.add_field(name="Rob Cooldown",value=f"{utils_cog.convert_cooldown_into_time(rob_name, rob_cooldown)}\n",inline=False)
        cooldown_embed.add_field(name="Robbed Cooldown",value=f"{utils_cog.convert_cooldown_into_time(robbed_name, robbed_cooldown)}",inline=False)

        cooldown_embed.set_field_at(index=1,name="test test", value= "test test", inline=False)

        await interaction.response.send_message(embed=cooldown_embed)

    @app_commands.command(name="help", description="Check what all of your commands do.")
    async def help(self, interaction: discord.Interaction):

        user_id = interaction.user.id
        user_name = interaction.user.name
        user = interaction.user

        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(user_id, user_name)

        embed = discord.Embed(title=f"Help!", description="These are all of the available user commands! If a command throws an error, make sure to read what should be entered into the field (ex. when purchasing item_name is case sensitive)", color=0x9B59B6)
        embed.set_author(
            name=f"{user.name}",
            
            icon_url=user.display_avatar.url)

        embed.add_field(name="Profile",value=f"Shows your profile.\n",inline=False)
        embed.add_field(name="Balance",value=f"Shows you your total candy balance.\n")
        embed.add_field(name="Bank",value=f"You can /withdraw and /deposit your money into the bank, making it safe from robbers.\n",inline=False)
        embed.add_field(name="Send Candy",value=f"Lets you send candy to another user", inline=False)
        embed.add_field(name="Hourly Candy",value=f"Claim 100-200 candy every single hour!\n", inline=False)
        embed.add_field(name="Daily Candy",value=f"Claim a larger daily candy reward.\n", inline=False)
        embed.add_field(name="Weekly Candy",value=f"Claim a large weekly candy reward.\n", inline=False)
        embed.add_field(name="RPS",value=f"Gamble on rock paper and scissors.\n", inline=False)
        embed.add_field(name="Coin Toss",value=f"Gamble on coin toss.\n", inline=False)
        embed.add_field(name="Blackjack",value=f"Gamble on blackjack.", inline=False)
        embed.add_field(name="Slot Machine",value=f"Gamble on slots! The odds might be terrible or amazing I have no clue.", inline=False)
        embed.add_field(name="Roulette",value=f"Gamble on roulette!", inline=False)
        embed.add_field(name="Rob",value=f"Lets you rob another user. Be warned, you can also be robbed!\n", inline=False)
        embed.add_field(name="Cooldowns",value=f"Shows you the time left for every command and when you can be robbed next.", inline=False)
        embed.add_field(name="Store",value=f"Shows you all of the available items in the candy store/", inline=False)
        embed.add_field(name="Purchase",value=f"Buy an item from the store! Name is case sensitive.", inline=False)
        embed.add_field(name="Raffles",value=f"View all currently available raffles, their ticket prices, and how many tickets have been bought!", inline=False)
        embed.add_field(name="Buy raffle tickets",value=f"Lets you buy raffle tickets", inline=False)
        embed.add_field(name="My tickets",value=f"Lets you see all of your purchased tickets", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    # @app_commands.command(name="clearbgimage", description="Remove your background image and use color instead")
    # async def clearbgimage(self, interaction: discord.Interaction):
    #     user_id = interaction.user.id
    #     user_name = interaction.user.name
        
    #     # Check if user exists (creates user if doesn't exist)
    #     utils_cog = self.bot.get_cog("Utils")
    #     await utils_cog.check_user_exists(user_id, user_name)
        
    #     # Clear the image
    #     async with asqlite.connect('./database.db') as connection:
    #         async with connection.cursor() as cursor:
    #             await cursor.execute(
    #                 'UPDATE Users SET bg_image = NULL WHERE id = ?',
    #                 (user_id,)
    #             )
    #             await connection.commit()
        
    #     await interaction.response.send_message(
    #         "✅ Background image cleared!",
    #         ephemeral=True
    #     )
    
    # @app_commands.command(name="setbgimage", description="Set your profile background image!")
    # @app_commands.describe(link="Provide a direct link to an image (PNG, JPG, GIF)")
    # async def setbgimage(self, interaction: discord.Interaction, link: str):
    #     await interaction.response.defer(ephemeral=True)
        
    #     user_id = interaction.user.id
    #     user_name = interaction.user.name
        
    #     # Check if user exists
    #     utils_cog = self.bot.get_cog("Utils")
    #     await utils_cog.check_user_exists(user_id, user_name)
        
    #     headers = {
    #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    #         'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    #         'Accept-Language': 'en-US,en;q=0.9',
    #         'Accept-Encoding': 'gzip, deflate, br',
    #         'Connection': 'keep-alive',
    #         'Upgrade-Insecure-Requests': '1'
    #     }
        
    #     # Validate and test the image URL
    #     try:
    #         async with aiohttp.ClientSession() as session:
    #             async with session.get(link, headers=headers, timeout=10) as response:
    #                 # Check if request was successful
    #                 if response.status != 200:
    #                     await interaction.followup.send(
    #                         f"❌ Could not retrieve the image (HTTP {response.status}). Please make sure the link is valid and publicly accessible.",
    #                         ephemeral=True
    #                     )
    #                     return
                    
    #                 # Check content type
    #                 content_type = response.headers.get('content-type', '')
    #                 if not content_type.startswith('image/'):
    #                     await interaction.followup.send(
    #                         f"❌ The link doesn't appear to be an image (content-type: {content_type}). Please provide a direct link to an image file.",
    #                         ephemeral=True
    #                     )
    #                     return
                    
    #                 # Check file size (limit to 5MB)
    #                 content_length = response.headers.get('content-length')
    #                 if content_length and int(content_length) > 5 * 1024 * 1024:
    #                     await interaction.followup.send(
    #                         "❌ Image is too large! Please use an image under 5MB.",
    #                         ephemeral=True
    #                     )
    #                     return
                    
    #                 # Try to load the image to verify it's valid
    #                 image_data = await response.read()
    #                 try:
    #                     img = Image.open(BytesIO(image_data))
    #                     img.verify()  # Verify it's a valid image
    #                 except Exception as e:
    #                     await interaction.followup.send(
    #                         "❌ The file appears to be corrupted or not a valid image format.",
    #                         ephemeral=True
    #                     )
    #                     return
        
    #     except asyncio.TimeoutError:
    #         await interaction.followup.send(
    #             "❌ The image took too long to load. Please try a different image host.",
    #             ephemeral=True
    #         )
    #         return
    #     except Exception as e:
    #         await interaction.followup.send(
    #             f"❌ Failed to retrieve the image. Please make sure the link is valid.\nError: {str(e)}",
    #             ephemeral=True
    #         )
    #         return
        
    #     # If we got here, the image is valid - save it to database
    #     async with asqlite.connect('./database.db') as connection:
    #         async with connection.cursor() as cursor:
    #             await cursor.execute(
    #                 'UPDATE Users SET bg_image = ? WHERE id = ?',
    #                 (link, user_id)
    #             )
    #             await connection.commit()
        
    #     await interaction.followup.send(
    #         f"✅ Your profile background image has been set successfully!\nUse `/profile` to see it in action.",
    #         ephemeral=True
    #     )
    
    # @app_commands.command(name="setbgcolor", description="Set your profile background color!")
    # @app_commands.describe(color="Choose a color preset or provide a hex code (e.g., #FF5733)")
    # @app_commands.choices(color=[
    #     app_commands.Choice(name="Purple (Default)", value="purple"),
    #     app_commands.Choice(name="Blue", value="blue"),
    #     app_commands.Choice(name="Red", value="red"),
    #     app_commands.Choice(name="Green", value="green"),
    #     app_commands.Choice(name="Orange", value="orange"),
    #     app_commands.Choice(name="Pink", value="pink"),
    #     app_commands.Choice(name="Cyan", value="cyan"),
    #     app_commands.Choice(name="Gold", value="gold"),
    #     app_commands.Choice(name="Teal", value="teal"),
    #     app_commands.Choice(name="Indigo", value="indigo"),
    #     app_commands.Choice(name="Black", value="black"),
    #     app_commands.Choice(name="Gray", value="gray")
    # ])
    # async def setbgcolor(self, interaction: discord.Interaction, color: str = None):
    #     user_id = interaction.user.id
    #     user_name = interaction.user.name
        
    #     # Check if user exists
    #     utils_cog = self.bot.get_cog("Utils")
    #     await utils_cog.check_user_exists(user_id, user_name)
        
    #     # Validate hex color if provided
    #     if color.startswith("#"):
    #         if len(color) != 7 or not all(c in "0123456789ABCDEFabcdef" for c in color[1:]):
    #             await interaction.response.send_message(
    #                 "Invalid hex color! Please use format #RRGGBB (e.g., #FF5733)",
    #                 ephemeral=True
    #             )
    #             return
        
    #     # Update the database
    #     async with asqlite.connect('./database.db') as connection:
    #         async with connection.cursor() as cursor:
    #             await cursor.execute(
    #                 'UPDATE Users SET bg_color = ? WHERE id = ?',
    #                 (color.lower(), user_id)
    #             )
    #             await connection.commit()
        
    #     # Create a preview of the new color
    #     preview_image = await self.create_color_preview(color)
        
    #     await interaction.response.send_message(
    #         f"✅ Your profile background color has been set to **{color}**!",
    #         file=preview_image,
    #         ephemeral=True
    #     )

    # async def create_color_preview(self, color):
    #     """Create a small preview image of the color gradient"""
    #     width, height = 400, 100
    #     img = Image.new('RGB', (width, height))
    #     draw = ImageDraw.Draw(img)
        
    #     # Define color presets
    #     color_presets = {
    #         "purple": {"r": 155, "g": 89, "b": 182},
    #         "blue": {"r": 89, "g": 155, "b": 182},
    #         "red": {"r": 182, "g": 89, "b": 89},
    #         "green": {"r": 89, "g": 182, "b": 89},
    #         "orange": {"r": 255, "g": 140, "b": 0},
    #         "pink": {"r": 255, "g": 182, "b": 193},
    #         "cyan": {"r": 0, "g": 255, "b": 255},
    #         "gold": {"r": 255, "g": 215, "b": 0},
    #         "teal": {"r": 0, "g": 128, "b": 128},
    #         "indigo": {"r": 75, "g": 0, "b": 130},
    #         "black": {"r": 50, "g": 50, "b": 50},
    #         "gray": {"r": 128, "g": 128, "b": 128}
    #     }
        
    #     # Parse color
    #     if color.startswith("#") and len(color) == 7:
    #         try:
    #             base_r = int(color[1:3], 16)
    #             base_g = int(color[3:5], 16)
    #             base_b = int(color[5:7], 16)
    #         except:
    #             base_r, base_g, base_b = 155, 89, 182
    #     elif color.lower() in color_presets:
    #         preset = color_presets[color.lower()]
    #         base_r, base_g, base_b = preset["r"], preset["g"], preset["b"]
    #     else:
    #         base_r, base_g, base_b = 155, 89, 182
        
    #     # Create gradient
    #     for y in range(height):
    #         factor = 1 - y / height
    #         r = int(base_r * factor)
    #         g = int(base_g * factor)
    #         b = int(base_b * factor)
    #         draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    #     # Add border
    #     draw.rectangle([0, 0, width-1, height-1], outline='white', width=2)
        
    #     # Convert to Discord file
    #     buffer = io.BytesIO()
    #     img.save(buffer, format='PNG')
    #     buffer.seek(0)
        
    #     return discord.File(buffer, filename='color_preview.png')
    
    #   def draw_gradient_background(self, draw, width, height, bg_color):
    #     """Draw a gradient background"""
    #     # Define color presets for gradients
    #     color_presets = {
    #         "purple": {"r": 155, "g": 89, "b": 182},
    #         "blue": {"r": 89, "g": 155, "b": 182},
    #         "red": {"r": 182, "g": 89, "b": 89},
    #         "green": {"r": 89, "g": 182, "b": 89},
    #         "orange": {"r": 255, "g": 140, "b": 0},
    #         "pink": {"r": 255, "g": 182, "b": 193},
    #         "cyan": {"r": 0, "g": 255, "b": 255},
    #         "gold": {"r": 255, "g": 215, "b": 0},
    #         "teal": {"r": 0, "g": 128, "b": 128},
    #         "indigo": {"r": 75, "g": 0, "b": 130},
    #         "black": {"r": 50, "g": 50, "b": 50},
    #         "gray": {"r": 128, "g": 128, "b": 128}
    #     }
        
    #     # Parse color
    #     if bg_color and bg_color.startswith("#") and len(bg_color) == 7:
    #         try:
    #             base_r = int(bg_color[1:3], 16)
    #             base_g = int(bg_color[3:5], 16)
    #             base_b = int(bg_color[5:7], 16)
    #         except:
    #             base_r, base_g, base_b = 155, 89, 182
    #     elif bg_color and bg_color.lower() in color_presets:
    #         preset = color_presets[bg_color.lower()]
    #         base_r, base_g, base_b = preset["r"], preset["g"], preset["b"]
    #     else:
    #         base_r, base_g, base_b = 155, 89, 182
        
    #     # Create gradient
    #     for y in range(height):
    #         factor = 1 - y / height
    #         r = int(base_r * factor)
    #         g = int(base_g * factor)
    #         b = int(base_b * factor)
    #         draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    @app_commands.command(name="profile", description="Display your profile!")
    async def profile(self, interaction: discord.Interaction):
        
        user_id = interaction.user.id
        user_name = interaction.user.name
        
        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(user_id, user_name)
        
        async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(f'SELECT candy, bank, roles FROM Users WHERE id = ?', (user_id,))
                    db_result = await cursor.fetchone()
        
        candy, bank, roles_json = db_result
        roles = json.loads(roles_json) if roles_json else []
        
        # Create the profile image
        profile_image = await self.create_profile_image(interaction.user, candy, bank, roles)
        
        await interaction.response.send_message(file=profile_image)

    async def create_profile_image(self, user, candy, bank, roles):
        
        # Card dimensions
        width, height = 800, 500
        
        # Create base image
        img = Image.new('RGB', (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load the preset background image
        try:
            # Get the path to the background image
            cog_dir = Path(__file__).parent.parent 
            bg_image_path = cog_dir / "images" / "bgimage.jpg"  
            
            if bg_image_path.exists():
                bg_img = Image.open(bg_image_path).convert('RGB')
                
                # Resize to fit card dimensions
                bg_img = self.resize_image_cover(bg_img, width, height)
                
                # Paste background image
                img.paste(bg_img, (0, 0))
                
                # Add dark overlay for text readability
                overlay = Image.new('RGBA', (width, height), (0, 0, 0, 140))
                img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                draw = ImageDraw.Draw(img)
            else:
                print(f"Background image not found at {bg_image_path}")
                # Fill with a solid dark color as fallback
                draw.rectangle([0, 0, width, height], fill=(30, 30, 40))
        except Exception as e:
            print(f"Failed to load background image: {e}")
            draw.rectangle([0, 0, width, height], fill=(30, 30, 40))
        
        # Load fonts - try multiple font paths for better compatibility
        try:
            # Try different font paths depending on OS
            import platform
            system = platform.system()
            
            if system == "Windows":
                title_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
                header_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 24)
                text_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)
                small_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 16)
            elif system == "Linux":
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 36)
                header_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 24)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 20)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 16)
            else:  # macOS
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
                header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
                text_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
                small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except:
            # Fallback to default fonts
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Get and process user avatar
        avatar_img = await self.get_user_avatar(user)
        if avatar_img:
            # Resize and make circular
            avatar_size = 120
            avatar_img = avatar_img.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
            avatar_img = self.make_circular(avatar_img)
            
            # Paste avatar
            avatar_x = 50
            avatar_y = 50
            img.paste(avatar_img, (avatar_x, avatar_y), avatar_img)
        
        # User name
        name_x = 200
        name_y = 70
        draw.text((name_x, name_y), user.display_name, fill='white', font=title_font)
        
        # Discord tag
        tag_y = name_y + 45
        draw.text((name_x, tag_y), f"@{user.name}", fill=(200, 200, 200), font=text_font)
        
        # Main content area with better spacing
        content_y = 220
        
        # Balance section
        self.draw_section_header(draw, "BALANCES:", 50, content_y, header_font)
        
        # Candy in pocket
        candy_y = content_y + 45
        draw.text((70, candy_y), f"Candy in pocket:", fill='white', font=text_font)
        draw.text((300, candy_y), f"{candy:,}", fill=(255, 215, 0), font=text_font)
        
        # Bank candy
        bank_y = candy_y + 30
        draw.text((70, bank_y), f"Candy in bank:", fill='white', font=text_font)
        draw.text((300, bank_y), f"{bank:,}", fill=(173, 216, 230), font=text_font)
        
        # Total wealth with separator line
        draw.line([(70, bank_y + 35), (500, bank_y + 35)], fill=(100, 100, 100), width=1)
        total_y = bank_y + 40
        total_wealth = candy + bank
        draw.text((70, total_y), f"Total wealth:", fill='white', font=text_font)
        draw.text((300, total_y), f"{total_wealth:,}", fill=(50, 255, 50), font=text_font)
        
        # Roles section
        roles_y = total_y + 60
        self.draw_section_header(draw, "ROLES:", 50, roles_y, header_font)
        
        roles_text = "No special roles"
        if roles:
            if len(roles) <= 3:
                roles_text = ", ".join(roles)
            else:
                roles_text = ", ".join(roles[:3]) + f" +{len(roles)-3} more"
        
        roles_content_y = roles_y + 45
        draw.text((70, roles_content_y), roles_text, fill='white', font=text_font)
        
        # Add decorative border
        border_color = (255, 255, 255)
        border_width = 2
        draw.rectangle([10, 10, width-10, height-10], outline=border_color, width=border_width)
        
        # Convert to Discord file
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return discord.File(buffer, filename='profile.png')

    async def get_user_avatar(self, user):
        """Download user avatar"""
        try:
            avatar_url = user.display_avatar.url
            async with aiohttp.ClientSession() as session:
                async with session.get(str(avatar_url)) as resp:
                    if resp.status == 200:
                        data = await resp.read()
                        return Image.open(BytesIO(data)).convert('RGBA')
        except Exception as e:
            print(f"Failed to get avatar: {e}")
            return None

    def make_circular(self, img):
        """Make an image circular"""
        size = img.size
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([0, 0, size[0], size[1]], fill=255)
        
        # Apply mask
        img.putalpha(mask)
        return img

    def draw_section_header(self, draw, text, x, y, font):
        """Draw a section header with underline"""
        # Draw text
        draw.text((x, y), text, fill='white', font=font)
        
        # Get text width for underline
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        except:
            text_width = len(text) * 15
            text_height = 30
        
        # Draw underline
        draw.line([(x, y + text_height + 5), (x + text_width, y + text_height + 5)], 
                fill=(255, 255, 255), width=2)

    def resize_image_cover(self, img, target_width, target_height):
        
        img_width, img_height = img.size
        
        # Calculate scale factors
        scale_x = target_width / img_width
        scale_y = target_height / img_height
        
        # Use the larger scale factor to ensure coverage
        scale = max(scale_x, scale_y)
        
        # Calculate new dimensions
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to target dimensions (center crop)
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        
        return img.crop((left, top, right, bottom))
            

    @app_commands.command(name="rob", description="Steal someones candy!")
    async def rob(self, interaction: discord.Interaction, target: discord.Member):

        user_id = interaction.user.id
        user_name = interaction.user.name
        target_id = target.id
        target_name = target.name
        
        if user_id == target_id:
            await interaction.response.send_message(f"You can't rob yourself goofy.")
            return

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(user_id, user_name)
        await utils_cog.check_user_exists(target_id, target_name)

        cooldown_data = await utils_cog.check_cooldown(interaction, target)
        cooldown_name = cooldown_data['cooldown_name']
        executed_time = cooldown_data['executed_time']
        target_time_left = cooldown_data['target_time_left']
        user_time_left = cooldown_data['user_time_left']
        
        if not cooldown_data['user_on_cooldown'] and not cooldown_data['target_on_cooldown']:
            
            bot_choice = random.choices(ROB_CHOICES, weights=ROB_WEIGHTS, k=1)[0]
            if bot_choice == "SUCCEED":
                async with asqlite.connect('./database.db') as connection:
                    async with connection.cursor() as cursor:

                        await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (target_id,))
                        db_result = await cursor.fetchone()
                        db_result= db_result[0]

                        #Edge case: If user has no candy or has less than the max steal amount
                        if db_result == 0:
                            await interaction.response.send_message(f"You tried to steal candy {target.name}, but they had nothing to steal! Unlucky.")
                            return
                        elif db_result < 200:
                            steal = random.randint(0, db_result)
                        else:
                            steal = random.randint(0, 500)

                        await cursor.execute(f'UPDATE users SET candy = candy + ?, {cooldown_name} = ? WHERE id = ? RETURNING candy', (steal, executed_time, user_id))
                        user_candy_amount = await cursor.fetchone()
                        user_candy_amount= user_candy_amount[0]
                        await cursor.execute(f'UPDATE users SET candy = candy - ?, robbed_cooldown = ? WHERE id = ? RETURNING candy', (steal, executed_time, target_id))
                        target_candy_amount = await cursor.fetchone()
                        target_candy_amount= target_candy_amount[0]
                        
                logger.info(f"DB_UPDATE: Robbed {steal} candy to user: {user_name}'s id: {user_id} from target: {target_name}'s id: {target_id}. User balance: {user_candy_amount} Target balance: {target_candy_amount}")
                await interaction.response.send_message(f"{interaction.user.mention} stole {steal} candy from {target.mention}!")
                
            else: #Fail logic
                async with asqlite.connect('./database.db') as connection:
                    async with connection.cursor() as cursor:
                        await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (user_id,))
                        db_result = await cursor.fetchone()
                        db_result= db_result[0]

                        #Edge case: If user has no candy or has less than the max steal amount
                        if db_result == 0:
                            await interaction.response.send_message(f"You tried to steal candy from {target.name}, but you got caught! Luckily, you are poor and have nothing to lose.")
                            return
                        elif db_result < 200:
                            steal = random.randint(0, db_result)
                        else:
                            steal = random.randint(0, 500)
                        
                        
                        await cursor.execute(f'UPDATE users SET candy = candy - ?, {cooldown_name} = ? WHERE id = ?', (steal, executed_time, user_id))
                await interaction.response.send_message(f"You tried to steal candy from {target.name}, but you got caught! The cops beat your fucking ass and you lost {steal} candy.")        
                logger.info(f"DB_UPDATE: Robbed fail {steal} candy from user: {user_name}'s id: {user_id}. User balance: {user_candy_amount}")
                
        elif not cooldown_data['user_on_cooldown'] and cooldown_data['target_on_cooldown']: #Target cant be robbed
            await interaction.response.send_message(f"This user can't be robbed for another {utils_cog.convert_seconds_to_string(target_time_left)} hours.")
        elif cooldown_data['user_on_cooldown'] and cooldown_data['target_on_cooldown']: #Target cant be robbed and user on cooldown
            await interaction.response.send_message(f"This command is still on cooldown for another {utils_cog.convert_seconds_to_string(user_time_left)} hours and the user can't be robbed for {utils_cog.convert_seconds_to_string(target_time_left)} seconds.")
        else:
            await interaction.response.send_message(f"This command is still on cooldown for another {utils_cog.convert_seconds_to_string(user_time_left)} seconds.")

async def setup(bot: commands.Bot):
    
    await bot.add_cog(UserCommands(bot))