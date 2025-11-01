import discord, random, asqlite, json, platform, logging, aiohttp, io, asyncio
from discord.ext import commands
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from pathlib import Path

logger = logging.getLogger(__name__)

USERS_PER_PAGE = 10

EXCLUDED_USER_IDS = [
    1198639825411129375,
    802733611140644915,
    737819231940378685,
    496236198948503563,
    359555744422559747,
    239474338351415306,
    1144727878936838154,
    192819869664673812,
    394993603497426945,
    732637562912374825,
    555093222175539220,
    356559404956516352,
    1202963715125936225,
    374679702599892994,
    316320318979440640,
    526185212271394817,
    729738838817374308
]

ROB_CHOICES = ["SUCCEED", "FAIL"]
ROB_WEIGHTS = [0.5,0.5]
WEAPON_ROLE_IDS = {
    1421374048700596305,  
    1421374098109497444,
    1421374134331375697,
    1421374287230533662,
    1421374308336402452,
    1421374343178620938,
    1421374395401895946
}



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
                reward = random.randint(2000, 4000)
                reward = random.randint(2000, 4000)
            elif cooldown_name == "weekly_cooldown":
                reward = random.randint(10000, 20000)
                reward = random.randint(10000, 20000)
            else:
                reward = random.randint(200, 400)
                reward = random.randint(200, 400)

            async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(f'UPDATE users SET candy = candy + ?, {cooldown_name} = ? WHERE id = ? RETURNING candy', (reward, executed_time, user_id))
                    result = await cursor.fetchone()
                    await connection.commit()
                    new_candy_amount = result[0]
                    logger.info(f"DB_UPDATE: Added {reward} candy to user: {user_name}'s id: {user_id} total: {new_candy_amount}")

            await interaction.response.send_message(f"🍬 You got {reward} candy!")
        else:
            await interaction.response.send_message(f"This command is still on cooldown for another {utils_cog.convert_seconds_to_string(user_time_left)} hours.")

    @app_commands.command(name="daily", description="Claim your daily candy!")
    async def dailycandy(self, interaction: discord.Interaction):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        await self.candy_cooldown(interaction)
    
    @app_commands.command(name="hourly", description="Claim your hourly candy!")
    async def hourlycandy(self, interaction: discord.Interaction):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        await self.candy_cooldown(interaction)
    
    @app_commands.command(name="weekly", description="Claim your weekly candy!")
    async def weeklycandy(self, interaction: discord.Interaction):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        await self.candy_cooldown(interaction)
        
        
    async def bank(self, interaction: discord.Interaction, amount: int):
        
        if amount <= 0:
            await interaction.response.send_message(f"Nice try bucko, debt does not exist in these camping grounds.")
            return
            
        
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
                        await interaction.response.send_message(f"🏦 You have deposited {amount} candy successfully.")
                        logger.info(f"DB_UPDATE: Moved {amount} candy to user: {user_name}'s id: {user_id} bank. Candy balance: {new_candy_amount} Bank Balance: {new_bank_amount}")
                    else:
                        await cursor.execute(f'UPDATE users SET candy = candy + ?, bank = bank - ? WHERE id = ? RETURNING candy, bank', (amount, amount, user_id))
                        result = await cursor.fetchone()
                        await connection.commit()
                        new_candy_amount, new_bank_amount = result[0], result[1]
                        await interaction.response.send_message(f"🏦 You have withdrawn {amount} candy successfully.")
                        logger.info(f"DB_UPDATE: Moved {amount} candy to user: {user_name}'s id: {user_id} candy balance. Candy balance: {new_candy_amount} Bank Balance: {new_bank_amount}")
                        
                    
        
    @app_commands.command(name="deposit", description="Deposit your candy! Makes it safe from robbing.")
    async def deposit(self, interaction: discord.Interaction, amount: int):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        await self.bank(interaction, amount)
          
    @app_commands.command(name="withdraw", description="Withdraw your candy!")
    async def withdraw(self, interaction: discord.Interaction, amount: int):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        await self.bank(interaction, amount)

    @app_commands.command(name="send-candy", description="Send candy to someone.")
    async def sendycandy(self, interaction: discord.Interaction, target: discord.Member, amount: int):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return

        # Ensure we compare integers (IDs are ints, not strings)
        if interaction.user.id == 729738838817374308:
            await interaction.response.send_message("You can't send candy as you have been DQ'd.", ephemeral=True)
            return

        if target.id == 729738838817374308:
            await interaction.response.send_message("You can't send candy to this user as they have been DQ'd.", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("You must send a positive amount of candy!", ephemeral=True)
            return

        user_id = interaction.user.id
        user_name = interaction.user.name
        
        
        target_id = target.id
        target_name = target.name
        
        

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(user_id, user_name)
        await utils_cog.check_user_exists(target_id, target_name)
        
        if user_id == target_id:
            await interaction.response.send_message(f"Why are your trying this *sigh*")
            return

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("BEGIN IMMEDIATE")

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
                    await connection.commit()
                    await interaction.response.send_message(f"🎁 You gave {amount} candy to {target.mention}!")
                else:
                    await connection.rollback()
                    await interaction.response.send_message(f"You dont have enough candy to do that.")
                    target_candy_amount = 0
                
                await connection.commit()
                logger.info(f"DB_UPDATE: Sent {amount} candy From user: {user_name}'s id: {user_id} to target: {target_name}'s id: {target_id}. User balance: {user_candy_amount} Target balance: {target_candy_amount}")

        

    @app_commands.command(name="my-balance", description="Check your candy balance.")
    async def mybalance(self, interaction: discord.Interaction):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return

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
        
        await interaction.response.send_message(f"🍬 You have {user_candy_amount} pieces of candy in your pockets. \n🏦 You have {bank_balance} in your bank!")
        
    @app_commands.command(name="balance", description="Check someones balance.")
    async def balance(self, interaction: discord.Interaction, target: discord.Member):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return

        target_id = target.id
        target_name = target.name
        target_display = target.display_name

        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(target_id, target_name)

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:

                await cursor.execute(f'SELECT candy, bank FROM Users WHERE id = ?', (target_id,))
                target_candy_amount = await cursor.fetchone()
                 
                await connection.commit()
                
        bank_balance= target_candy_amount[1]
        target_candy_amount= target_candy_amount[0]
        
        await interaction.response.send_message(f"{target_display} has 🍬 {target_candy_amount} pieces of candy in their pockets. \n🏦 They have {bank_balance} in their bank!")

    @app_commands.command(name="cooldowns", description="Check all of your cooldowns.")
    async def cooldowns(self, interaction: discord.Interaction):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return

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
                await cursor.execute(f'SELECT weekly_cooldown FROM Users WHERE id = ?', (user_id,))
                weekly_cooldown = await cursor.fetchone()
                
                await connection.commit()

        user_candy_amount= user_candy_amount[0]
        rob_cooldown= rob_cooldown[0]
        robbed_cooldown= robbed_cooldown[0]
        daily_cooldown= daily_cooldown[0]
        hourly_cooldown= hourly_cooldown[0]
        weekly_cooldown = weekly_cooldown[0]

        hourly_name= "hourly_cooldown"
        daily_name= "daily_cooldown"
        weekly_name = "weekly_cooldown"
        rob_name= "rob_cooldown"
        robbed_name= "rob_cooldown"
        
        cooldown_embed = discord.Embed(title=f"Command Cooldowns", color=0x9B59B6)
        cooldown_embed.set_author(
            name=f"{user.display_name}",
            name=f"{user.display_name}",
            icon_url=user.display_avatar.url)
            
        cooldown_embed.add_field(name="🍬 Candy Balance",value=f"{user_candy_amount}\n")
        cooldown_embed.add_field(name="⏰ Hourly Cooldown",value=f"{utils_cog.convert_cooldown_into_time(hourly_name, hourly_cooldown)}\n",inline=False)
        cooldown_embed.add_field(name="☀️ Daily Cooldown",value=f"{utils_cog.convert_cooldown_into_time(daily_name, daily_cooldown)}\n",inline=False)
        cooldown_embed.add_field(name="📅 Weekly Cooldown",value=f"{utils_cog.convert_cooldown_into_time(weekly_name, weekly_cooldown)}\n",inline=False)
        cooldown_embed.add_field(name="🦹 Rob Cooldown",value=f"{utils_cog.convert_cooldown_into_time(rob_name, rob_cooldown)}\n",inline=False)
        cooldown_embed.add_field(name="🛡️ Robbed Cooldown",value=f"{utils_cog.convert_cooldown_into_time(robbed_name, robbed_cooldown)}",inline=False)

        await interaction.response.send_message(embed=cooldown_embed)

    @app_commands.command(name="help", description="Check what all of your commands do.")
    async def help(self, interaction: discord.Interaction):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return

        user_id = interaction.user.id
        user_name = interaction.user.name
        user = interaction.user

        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(user_id, user_name)

        embed = discord.Embed(title=f"Help!", description="These are all of the available user commands! If a command throws an error, make sure to read what should be entered into the field (ex. when purchasing item_name is case sensitive)", color=0x9B59B6)
        embed.set_author(
            name=f"{user.display_name}",
            name=f"{user.display_name}",
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
        #embed.add_field(name="Slot Machine",value=f"Gamble on slots! The odds might be terrible or amazing I have no clue.", inline=False)
        embed.add_field(name="Roulette",value=f"Gamble on roulette!", inline=False)
        embed.add_field(name="Rob",value=f"Lets you rob another user. Be warned, you can also be robbed!\n", inline=False)
        embed.add_field(name="Cooldowns",value=f"Shows you the time left for every command and when you can be robbed next.", inline=False)
        embed.add_field(name="Store",value=f"Shows you all of the available items in the candy store/", inline=False)
        embed.add_field(name="Purchase",value=f"Buy an item from the store! Name is case sensitive.", inline=False)
        embed.add_field(name="Interactions",value=f"Murder, make a sacrifice, etc, all unique commands you can use upon purchase from the store!\n Hint: Make sure you are prepared before trying to murder someone ;)", inline=False)
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
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
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
        
        avatar_bytes = await self.get_user_avatar(interaction.user)
        
        # Create the profile image
        profile_image = await asyncio.to_thread(self.create_profile_image, interaction.user, candy, bank, roles, avatar_bytes)
        
        await interaction.response.send_message(file=profile_image)

    def create_profile_image(self, user, candy, bank, roles, avatar_bytes):
        
        # Card dimensions
        width, height = 800, 500
        
        # Create base image
        img = Image.new('RGB', (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load the preset background image
        try:
            # Get the path to the background image
            cog_dir = Path(__file__).parent.parent 
            bg_image_path = cog_dir / "images" / "bgimage.png"  
            
            if bg_image_path.exists():
                bg_img = Image.open(bg_image_path).convert('RGB')
                
                # Resize to fit card dimensions
                bg_img = self.resize_image_cover(bg_img, width, height)
                
                # Paste background image
                img.paste(bg_img, (0, 0))
                
                # Add dark overlay for text readability
                # overlay = Image.new('RGBA', (width, height), (0, 0, 0, 140))
                # img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
                # draw = ImageDraw.Draw(img)
            else:
                print(f"Background image not found at {bg_image_path}")
                # Fill with a solid dark color as fallback
                draw.rectangle([0, 0, width, height], fill=(30, 30, 40))
        except Exception as e:
            print(f"Failed to load background image: {e}")
            draw.rectangle([0, 0, width, height], fill=(30, 30, 40))
        
        try:
            
            system = platform.system()
            
            if system == "Windows":
                title_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 38)  # Increased
                header_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 26)  # Increased
                text_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 22)  # Increased
                small_font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 20)  # Increased
            elif system == "Linux":
                # Use DejaVu instead of Liberation for better Unicode support
                title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 38)
                header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 26)
                text_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            else:  # macOS
                title_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 42)
                header_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
                text_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
                small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except Exception as e:
            print(f"Font loading error: {e}")
            # Fallback to default fonts
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        # Get and process user avatar
        avatar_img = Image.open(BytesIO(avatar_bytes)).convert('RGBA')
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
        self.draw_section_header(draw, "★ BALANCES:", 50, content_y, header_font)
        
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
        self.draw_section_header(draw, "★ ROLES:", 50, roles_y, header_font)
        
        roles_text = "No special roles"
        if roles:
            if len(roles) <= 10:
                roles_text = ", ".join(roles)
            else:
                roles_text = ", ".join(roles[:10]) + f" +{len(roles)-10} more"
        
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
                        return data
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
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        user_id = interaction.user.id
        user_name = interaction.user.name
        target_id = target.id
        target_name = target.name
        
        if user_id == target_id:
            await interaction.response.send_message(f"You can't rob yourself goofy.")
            return
        
        is_admin = target.get_role(637868242932858911)
        is_owner = target.get_role(689473122423799900)
        
        if is_admin != None:
            await interaction.response.send_message(f"You can't rob a camp counsellor!", ephemeral=True)
            return

        if is_owner != None:
            await interaction.response.send_message(f"You can't rob the Head Counselor!", ephemeral=True)
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
                        
                        steal_percent = (random.randint(1, 50))/100
                        stolen_candy = int(steal_percent*db_result)

                        #Edge case: If user has no candy or has less than the max steal amount
                        if db_result == 0:
                            await interaction.response.send_message(f"You tried to steal candy {target.name}, but they had nothing to steal! Unlucky.")
                            return
                        # elif db_result < 200: # Steal fixed amounts from users
                        #     steal = random.randint(0, db_result)
                        # else:
                        #     steal = random.randint(0, 500)
                        
                        await cursor.execute(f'UPDATE users SET candy = candy - ?, robbed_cooldown = ? WHERE id = ? RETURNING candy', (stolen_candy, executed_time, target_id))
                        target_candy_amount = await cursor.fetchone()
                        target_candy_amount= target_candy_amount[0]
                        await cursor.execute(f'UPDATE users SET candy = candy + ?, {cooldown_name} = ? WHERE id = ? RETURNING candy', (stolen_candy, executed_time, user_id))
                        user_candy_amount = await cursor.fetchone()
                        user_candy_amount= user_candy_amount[0]
                        
                        await connection.commit()
                        
                        
                logger.info(f"DB_UPDATE: Robbed {stolen_candy} candy {steal_percent}% {db_result} to user: {user_name}'s id: {user_id} from target: {target_name}'s id: {target_id}. User balance: {user_candy_amount} Target balance: {target_candy_amount}")
                await interaction.response.send_message(f"🦹 {interaction.user.mention} stole {stolen_candy} candy from {target.mention}!")
            
            else: #Fail logic lose 10% of bank
                async with asqlite.connect('./database.db') as connection:
                    async with connection.cursor() as cursor:
                        await cursor.execute(f'SELECT bank FROM Users WHERE id = ?', (user_id,))
                        db_result = await cursor.fetchone()
                        db_result= db_result[0]

                        #Edge case: If user has no candy or has less than the max steal amount
                        if db_result == 0:
                            await interaction.response.send_message(f"You tried to steal candy from {target.mention}, but you got caught! Luckily, you have no candy in your bank and have nothing to lose.")
                            return
                        else:
                            steal = int(0.1 * db_result)

                        await cursor.execute(f'UPDATE users SET robbed_cooldown = ? WHERE id = ?', ( executed_time, target_id))
                        await cursor.execute(f'UPDATE users SET bank = bank - ?, {cooldown_name} = ? WHERE id = ?', (steal, executed_time, user_id))
                        
                await interaction.response.send_message(f"🚨 You tried to steal candy from {target.mention}, but you got caught! The counselors beat your fucking ass and you got fined {steal} candy, taken directly from your bank...")        
                logger.info(f"DB_UPDATE: Robbed fail {steal} candy from user: {user_name}'s id: {user_id}. User balance: {db_result}")
                
            # else: #Fail logic with flat rate
            #     async with asqlite.connect('./database.db') as connection:
            #         async with connection.cursor() as cursor:
            #             await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (user_id,))
            #             db_result = await cursor.fetchone()
            #             db_result= db_result[0]

            #             #Edge case: If user has no candy or has less than the max steal amount
            #             if db_result == 0:
            #                 await interaction.response.send_message(f"You tried to steal candy from {target.mention}, but you got caught! Luckily, you are poor and have nothing to lose.")
            #                 return
            #             elif db_result < 200:
            #                 steal = random.randint(0, db_result)
            #             else:
            #                 steal = random.randint(0, 500)
                        
            #             await cursor.execute(f'UPDATE users SET robbed_cooldown = ? WHERE id = ?', ( executed_time, target_id))
            #             await cursor.execute(f'UPDATE users SET candy = candy - ?, {cooldown_name} = ? WHERE id = ?', (steal, executed_time, user_id))
                        
            #     await interaction.response.send_message(f"🚨 You tried to steal candy from {target.mention}, but you got caught! The cops beat your fucking ass and you lost {steal} candy.")        
            #     logger.info(f"DB_UPDATE: Robbed fail {steal} candy from user: {user_name}'s id: {user_id}. User balance: {db_result}")
                
        elif not cooldown_data['user_on_cooldown'] and cooldown_data['target_on_cooldown']: #Target cant be robbed
            await interaction.response.send_message(f"This user can't be robbed for another {utils_cog.convert_seconds_to_string(target_time_left)} hours.")
        elif cooldown_data['user_on_cooldown'] and cooldown_data['target_on_cooldown']: #Target cant be robbed and user on cooldown
            await interaction.response.send_message(f"This command is still on cooldown for another {utils_cog.convert_seconds_to_string(user_time_left)} hours and the user can't be robbed for {utils_cog.convert_seconds_to_string(target_time_left)} seconds.")
        else:
            await interaction.response.send_message(f"This command is still on cooldown for another {utils_cog.convert_seconds_to_string(user_time_left)} seconds.")
        
        
            
    @app_commands.command(name="murder", description="Use your murder interaction and kill someone!")
    async def murder(self, interaction: discord.Interaction, target: discord.Member):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        is_admin = target.get_role(637868242932858911)
        is_owner = target.get_role(689473122423799900)
        
        if is_admin != None:
            await interaction.response.send_message(f"You can't murder a camp counsellor! They have plot armor.", ephemeral=True)
            return

        if is_owner != None:
            await interaction.response.send_message(f"You can't murder the Head Counselor! They have plot armor.", ephemeral=True)
            return
        
        if target.get_role(1421440686946783292) != None:
            await interaction.response.send_message(f"You tried to murder {target.name}, but they are already dead!", ephemeral=True)
            return
        
        if interaction.user.id == target.id:
            await interaction.response.send_message(f"You can't commit suicide bucko.")
            return
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(f'SELECT murder_count FROM users WHERE id = ?', (interaction.user.id, ))
                db_result = await cursor.fetchone()
                murder_count= db_result[0]
                if murder_count == 0:
                    await interaction.response.send_message(f"You tried to murder {target.mention}, but you havent purchased this command!", ephemeral=True)
                    return
                await cursor.execute(f'UPDATE users SET murder_count = murder_count - 1 WHERE id = ?', (interaction.user.id,))
                
        user_role_ids = {role.id for role in interaction.user.roles}
        has_weapon = bool(WEAPON_ROLE_IDS & user_role_ids)
        
        if has_weapon:
            await target.add_roles(interaction.guild.get_role(1421440686946783292))
            await interaction.response.send_message(f"🔪 You murdered {target.mention}, how brutal!", ephemeral=False)
        else:
            role = interaction.guild.get_role(637868242932858911)
            channel = discord.utils.get(interaction.guild.channels, name="shop-logs")
            await channel.send(f"{interaction.user.name} tried to murder {target.name} but failed! {role.mention}")
            await interaction.response.send_message(f"😱 {interaction.user.mention} approached {target.mention} attempting to kill them! But since they forgot to buy a weapon, {target.display_name} managed to escape and alert the camp counsellors!", ephemeral=False)
        
    @app_commands.command(name="flower", description="Give a user a flower <3")
    async def flower(self, interaction: discord.Interaction, target: discord.Member):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        if target.get_role(1421971324221526149) != None:
            await interaction.response.send_message(f"Someone else beat you to the punch and already gave {target.mention} a flower! Guess you just dont care as much...", ephemeral=False)
            return
        
        if interaction.user.id == target.id:
            await interaction.response.send_message(f"Trying to give a flower to yourself... how sad :(.")
            return
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(f'SELECT flower_count FROM users WHERE id = ?', (interaction.user.id, ))
                db_result = await cursor.fetchone()
                flower_count= db_result[0]
                if flower_count == 0:
                    await interaction.response.send_message(f"You tried to give a flower to {target.mention}, but you couldn't afford it... how embarassing!", ephemeral=False)
                    return
                await cursor.execute(f'UPDATE users SET flower_count = flower_count - 1 WHERE id = ?', (interaction.user.id,))
        
        await target.add_roles(interaction.guild.get_role(1421971324221526149))
        await interaction.response.send_message(f"🌸 You gave a flower to {target.mention}, how cute!", ephemeral=False)
        
    @app_commands.command(name="hero", description="Protect the user from the killer (they can still be killed by other camp goers!)")
    async def hero(self, interaction: discord.Interaction, target: discord.Member):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        if target.get_role(1421440686946783292) != None:
            await interaction.response.send_message(f"You tried to protect {target.name}, but they are already dead!", ephemeral=True)
            return
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(f'SELECT hero_count FROM users WHERE id = ?', (interaction.user.id, ))
                db_result = await cursor.fetchone()
                hero_count= db_result[0]
                if hero_count == 0:
                    await interaction.response.send_message(f"You tried to protect {target.display_name}, but you are too weak! Purchase it from the store noob.", ephemeral=True)
                    return
                await cursor.execute(f'UPDATE users SET hero_count = hero_count - 1 WHERE id = ?', (interaction.user.id,))
        
        role = interaction.guild.get_role(637868242932858911)
        channel = discord.utils.get(interaction.guild.channels, name="shop-logs")
        await channel.send(f"{interaction.user.name} has used the hero interaction to protect {target.name} {role.mention}")
        
        await interaction.response.send_message(f"You have protected {target.display_name}! If the killer targets them tonight, they are safe.", ephemeral=True)
        
    @app_commands.command(name="accusation", description="Make any accusation against another member or one of the counselors and see if you are right!")
    async def accusation(self, interaction: discord.Interaction, target: discord.Member):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        if interaction.user.id == target.id:
            await interaction.response.send_message(f"Just look in a mirror.")
            return
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(f'SELECT accusation_count FROM users WHERE id = ?', (interaction.user.id, ))
                db_result = await cursor.fetchone()
                accusation_count= db_result[0]
                if accusation_count == 0:
                    await interaction.response.send_message(f"You tried to accuse {target.mention} of something without any evidence!", ephemeral=False)
                    return
                await cursor.execute(f'UPDATE users SET accusation_count = accusation_count - 1 WHERE id = ?', (interaction.user.id,))
                
        role = interaction.guild.get_role(637868242932858911)
        await interaction.response.send_message(f"⚖️ You have accused {target.mention} of a serious crime! Wait for a camp counselor before proceeding.", ephemeral=False)
        channel = discord.utils.get(interaction.guild.channels, name="shop-logs")
        await channel.send(f"{target.mention} has been accused by {interaction.user.mention}! {role.mention}")
        
    @app_commands.command(name="interrogate", description="Ask one of the counselors a line of questions they have to answer.")
    async def interrogate(self, interaction: discord.Interaction, target: discord.Member):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        if interaction.user.id == target.id:
            await interaction.response.send_message(f"You can't interrogate yourself goofy.")
            return
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(f'SELECT interrogation_count FROM users WHERE id = ?', (interaction.user.id, ))
                db_result = await cursor.fetchone()
                interrogate_count= db_result[0]
                if interrogate_count == 0:
                    await interaction.response.send_message(f"You tried to interrogate {target.mention}, but you aren't intimidating at all!", ephemeral=False)
                    return
                await cursor.execute(f'UPDATE users SET interrogation_count = interrogation_count - 1 WHERE id = ?', (interaction.user.id,))
                
        role = interaction.guild.get_role(637868242932858911)
        await interaction.response.send_message(f"🕵️ You are interrogating {target.mention}! Lets see what they say.", ephemeral=False)
        channel = discord.utils.get(interaction.guild.channels, name="shop-logs")
        await channel.send(f"{target.mention} is being interrogated by {interaction.user.mention}! {role.mention}")
        
    @app_commands.command(name="make-a-sacrifice", description="Sacrifice one member to revive another.")
    async def makeasacrifice(self, interaction: discord.Interaction, sacrifice_target: discord.Member, revive_target: discord.Member):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        if interaction.user.get_role(1421440686946783292) != None:
            await interaction.response.send_message(f"You tried to sacrifice {sacrifice_target.name}, but you cant use your ritual materials as a ghost!", ephemeral=True)
            return
        
        if interaction.user.get_role(637868242932858911) != None or interaction.user.get_role(689473122423799900) != None:
            await interaction.response.send_message(f"You tried to sacrifice {sacrifice_target.name}, but strangely their uniform seems to have a strange enchantment on it, protecting them.", ephemeral=False)
            return
        
        if sacrifice_target.get_role(1421440686946783292) != None:
            await interaction.response.send_message(f"You tried to sacrifice {sacrifice_target.name}, but they are already dead!", ephemeral=True)
            return
        
        if revive_target.get_role(1421440686946783292) == None:
            await interaction.response.send_message(f"You tried to revive {revive_target.name}, but they are not dead!", ephemeral=True)
            return
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(f'SELECT makeasacrifice_count FROM users WHERE id = ?', (interaction.user.id, ))
                db_result = await cursor.fetchone()
                makeasacrifice_count= db_result[0]
                if makeasacrifice_count == 0:
                    await interaction.response.send_message(f"You tried to revive {revive_target.name}, but you don't have the correct sacrificial materials! Go purchase them.", ephemeral=True)
                    return
                await cursor.execute(f'UPDATE users SET makeasacrifice_count = makeasacrifice_count - 1 WHERE id = ?', (interaction.user.id,))
                
        role = interaction.guild.get_role(1421440686946783292) #deceased role
        await sacrifice_target.add_roles(role)
        await revive_target.remove_roles(role)
        await interaction.response.send_message(f"🩸 {interaction.user.mention} sacrificed {sacrifice_target.mention}! The demon accepted your offering, and brought {revive_target.mention} back to life.", ephemeral=False)
        
    @app_commands.command(name="skinny-dip", description="Go skinny dipping! Don't get caught or you might get in trouble.")
    async def skinnydip(self, interaction: discord.Interaction):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(f'SELECT skinnydip_count FROM users WHERE id = ?', (interaction.user.id, ))
                db_result = await cursor.fetchone()
                skinnydip_count= db_result[0]
                if skinnydip_count == 0:
                    await interaction.response.send_message(f"You tried to skinny dip, but your clothes seem magically stuck to you! I wonder why?", ephemeral=False)
                    return
                await cursor.execute(f'UPDATE users SET skinnydip_count = skinnydip_count - 1 WHERE id = ?', (interaction.user.id,))
                
        await interaction.response.send_message(f"{interaction.user.mention} is going skinny dipping! Lets hope no one sees you...", ephemeral=False)
    
    @app_commands.command(name="wedgie", description="Give someone a wedgie.")
    async def wedgie(self, interaction: discord.Interaction, target: discord.Member):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute(f'SELECT wedgie_count FROM users WHERE id = ?', (interaction.user.id, ))
                db_result = await cursor.fetchone()
                wedgie_count= db_result[0]
                if wedgie_count == 0:
                    await interaction.response.send_message(f"You tried to give {target.name} a wedgie, but you are too weak!", ephemeral=False)
                    return
                await cursor.execute(f'UPDATE users SET wedgie_count = wedgie_count - 1 WHERE id = ?', (interaction.user.id,))
                # await cursor.execute('SELECT bank FROM users WHERE id = ?', (target.id,))
                # original_bank = (await cursor.fetchone())[0]
                
                # loss = random.randint(10,20)*0.001
                # new_bal = int(original_bank*(1-loss))
                # await cursor.execute(f'UPDATE users SET bank = ? WHERE id = ?', (new_bal,target.id))
                # new_bank = new_bal
             
        await interaction.response.send_message(f"🩲 {interaction.user.mention} gave {target.mention} a wedgie!", ephemeral=False)        
        #await interaction.response.send_message(f"{interaction.user.mention} gave {target.mention} a wedgie! Looks like they had deposited some candy in there and lost {original_bank-new_bank}", ephemeral=False)
        #logger.info(f"DB_UPDATE: User: {target.name} id: {target.id} lost {original_bank-new_bank} candy. Old total: {original_bank} New total {new_bank}.")

    async def get_total_users(self):
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                if EXCLUDED_USER_IDS:
                    placeholders = ','.join(['?' for _ in EXCLUDED_USER_IDS])
                    await cursor.execute(f"""
                        SELECT COUNT(*) FROM Users 
                        WHERE (candy + bank) > 0 
                        AND id NOT IN ({placeholders})
                    """, tuple(EXCLUDED_USER_IDS))
                else:
                    await cursor.execute("SELECT COUNT(*) FROM Users WHERE (candy + bank) > 0")
                total_users = await cursor.fetchone()
                total_users = total_users[0]
                await connection.commit()
                
        return total_users

    async def get_page_users(self, page):
        offset = page * USERS_PER_PAGE
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                if EXCLUDED_USER_IDS:
                    placeholders = ','.join(['?' for _ in EXCLUDED_USER_IDS])
                    query = f"""
                        SELECT id, username, candy, bank, (candy + bank) as total 
                        FROM Users 
                        WHERE id NOT IN ({placeholders})
                        ORDER BY total DESC 
                        LIMIT ? OFFSET ?
                    """
                    await cursor.execute(query, tuple(EXCLUDED_USER_IDS) + (USERS_PER_PAGE, offset))
                else:
                    await cursor.execute("""
                        SELECT id, username, candy, bank, (candy + bank) as total 
                        FROM Users 
                        ORDER BY total DESC 
                        LIMIT ? OFFSET ?
                    """, (USERS_PER_PAGE, offset))
                data = await cursor.fetchall()
                await connection.commit()
                
        return data

    @app_commands.command(name="leaderboard", description="View the candy leaderboard")
    async def leaderboard(self, interaction: discord.Interaction):
        view = self.LeaderboardView(self, interaction.user, interaction.guild)
        await view.initialize()
        embed = await view.generate_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    class LeaderboardView(discord.ui.View):
        def __init__(self, cog, user, guild, page=0):
            super().__init__(timeout=180)
            self.cog = cog
            self.user = user
            self.guild = guild
            self.page = page
            self.total_users = 0
            self.max_page = 0
        
        async def initialize(self):
            self.total_users = await self.cog.get_total_users()
            self.max_page = (self.total_users - 1) // USERS_PER_PAGE if self.total_users > 0 else 0
            self.update_buttons()

        async def generate_embed(self):
            users = await self.cog.get_page_users(self.page)
            embed = discord.Embed(
                title="🏆 Candy Leaderboard 🏆",
                description="Top users by total wealth (Candy + Bank)",
                color=discord.Color.gold()
            )
            embed.set_author(name=f"Requested by {self.user.display_name}", icon_url=self.user.display_avatar.url)
            embed.set_footer(text=f"Page {self.page + 1} of {self.max_page + 1}")
            embed.set_thumbnail(url="https://images.halloweencostumes.com.au/products/12290/1-1/light-up-traditional-pumpkin-upd.jpg")

            if not users:
                embed.description = "No users found on the leaderboard."
            else:
                leaderboard_text = ""
                for idx, (user_id, username, candy, bank, total) in enumerate(users, start=1):
                    rank = (self.page * USERS_PER_PAGE) + idx
                    
                    # Medal emojis for top 3
                    if rank == 1:
                        medal = "🥇"
                    elif rank == 2:
                        medal = "🥈"
                    elif rank == 3:
                        medal = "🥉"
                    else:
                        medal = f"`#{rank}`"
                    
                    # Try to get the member's display name (nickname) from the guild
                    display_name = username  # Default to DB username
                    if self.guild:
                        member = self.guild.get_member(user_id)
                        if member:
                            display_name = member.display_name
                    
                    leaderboard_text += f"{medal} **{display_name}**\n"
                    #leaderboard_text += f"   💰 Total: **{total:,}** (🍬 {candy:,} + 🏦 {bank:,})\n\n"
                    leaderboard_text += f"   💰 Total: **{total:,}**\n\n"
                
                embed.description = leaderboard_text

            return embed

        def update_buttons(self):
            self.previous.disabled = self.page <= 0
            self.next.disabled = self.page >= self.max_page

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
        async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("Use your own leaderboard buster.", ephemeral=True)
                return

            if self.page > 0:
                self.page -= 1
                self.update_buttons()
                await interaction.response.edit_message(embed=await self.generate_embed(), view=self)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("Use your own leaderboard buster.", ephemeral=True)
                return

            if self.page < self.max_page:
                self.page += 1
                self.update_buttons()
                await interaction.response.edit_message(embed=await self.generate_embed(), view=self)


async def setup(bot: commands.Bot):
    
    await bot.add_cog(UserCommands(bot))