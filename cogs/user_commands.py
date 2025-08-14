import discord, random, asqlite
from discord.ext import commands
from discord import app_commands

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
            else:
                reward = random.randint(100, 200)

            async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(f'UPDATE users SET candy = candy + ?, {cooldown_name} = ? WHERE id = ?', (reward, executed_time, user_id))
                    await connection.commit()

            await interaction.response.send_message(f"You got {reward} candy!")
        else:
            await interaction.response.send_message(f"This command is still on cooldown for another {utils_cog.convert_seconds_to_string(user_time_left)} hours.")

    @app_commands.command(name="daily-candy", description="Claim your daily candy!")
    async def dailycandy(self, interaction: discord.Interaction):
        await self.candy_cooldown(interaction)
    
    @app_commands.command(name="hourly-candy", description="Claim your hourly candy!")
    async def hourlycandy(self, interaction: discord.Interaction):
        await self.candy_cooldown(interaction)

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

                await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (target_id,))
                user_candy_amount = await cursor.fetchone()
                user_candy_amount= user_candy_amount[0]

                if user_candy_amount >= amount:
                    await cursor.execute(f'UPDATE users SET candy = candy - ? WHERE id = ?', (amount, user_id))
                    await cursor.execute(f'UPDATE users SET candy = candy + ? WHERE id = ?', (amount, target_id))
                    await interaction.response.send_message(f"You gave {amount} candy to {target.mention}!")
                
                await connection.commit()

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

                await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (user_id,))
                user_candy_amount = await cursor.fetchone()
                
                await connection.commit()

        user_candy_amount= user_candy_amount[0]

        await interaction.response.send_message(f"You have {user_candy_amount} pieces of candy.")

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

        embed.add_field(name="Balance",value=f"Shows you your total candy balance.\n")
        embed.add_field(name="Send Candy",value=f"Lets you send candy to another user",inline=False)
        embed.add_field(name="Hourly Candy",value=f"Claim 100-200 candy every single hour!\n",inline=False)
        embed.add_field(name="Daily Candy",value=f"Claim a larger daily candy reward.\n",inline=False)
        embed.add_field(name="Rob",value=f"Lets you rob another user. Be warned, you can also be robbed!\n",inline=False)
        embed.add_field(name="Cooldowns",value=f"Shows you the time left for every command and when you can be robbed next.",inline=False)
        embed.add_field(name="Store",value=f"Shows you all of the available items in the candy store/",inline=False)
        embed.add_field(name="Purchase",value=f"Buy an item from the store! Name is case sensitive.",inline=False)

        await interaction.response.send_message(embed=embed)

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
                        steal = random.randint(0, 200)

                    await cursor.execute(f'UPDATE users SET candy = candy + ?, {cooldown_name} = ? WHERE id = ?', (steal, executed_time, user_id))
                    await cursor.execute(f'UPDATE users SET candy = candy - ?, robbed_cooldown = ? WHERE id = ?', (steal, executed_time, target_id))
                    await connection.commit()

            await interaction.response.send_message(f"{interaction.user.mention} stole {steal} candy from {target.mention}!")
        
        elif not cooldown_data['user_on_cooldown'] and cooldown_data['target_on_cooldown']: #Target cant be robbed
            await interaction.response.send_message(f"This user can't be robbed for another {utils_cog.convert_seconds_to_string(target_time_left)} hours.")
        elif cooldown_data['user_on_cooldown'] and cooldown_data['target_on_cooldown']: #Target cant be robbed and user on cooldown
            await interaction.response.send_message(f"This command is still on cooldown for another {utils_cog.convert_seconds_to_string(user_time_left)} hours and the user can't be robbed for {utils_cog.convert_seconds_to_string(target_time_left)} seconds.")
        else:
            await interaction.response.send_message(f"This command is still on cooldown for another {utils_cog.convert_seconds_to_string(user_time_left)} seconds.")

async def setup(bot: commands.Bot):
    
    await bot.add_cog(UserCommands(bot))