import discord, asqlite, json
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class AdminCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="give-candy", description="Gives a user candy.")
    @app_commands.default_permissions(administrator=True)
    async def givecandy(self, interaction: discord.Interaction , target: discord.Member, amount: int):
        
        target_id = target.id
        target_name = target.name

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(target_id, target_name)

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:

                await cursor.execute(f'UPDATE users SET candy = candy + ? WHERE id = ? RETURNING candy', (amount, target.id))
                new_candy_amount = await cursor.fetchone()
                await connection.commit()
                
        logger.info(f"DB_UPDATE: Added {amount} candy to user: {target_name}'s id: {target_id} total: {new_candy_amount[0]}")
        await interaction.response.send_message(f"You gave {amount} candy to {target.mention}!")
    
    @app_commands.command(name="remove-candy", description="Take a users candy.")
    @app_commands.default_permissions(administrator=True)
    async def removecandy(self, interaction: discord.Interaction , target: discord.Member, amount: int):

        target_id = target.id
        target_name = target.name
        candy_overflow = 0
        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(target_id, target_name)

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:

                await cursor.execute(f'UPDATE Users SET candy = candy - ? WHERE id = ?', (amount, target.id))
                await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (target.id,))
                current_candy = await cursor.fetchone()
                current_candy = current_candy[0]
                
                if current_candy < 0:
                    await cursor.execute(f'UPDATE Users SET candy = 0 WHERE id = ?', (target.id,))
                    candy_overflow = current_candy * -1
                    
                    await cursor.execute(f'SELECT bank FROM Users WHERE id = ?', (target.id,))
                    bank_balance = (await cursor.fetchone())[0]
                    
                    if bank_balance > candy_overflow:
                        await cursor.execute(f'UPDATE Users SET bank = bank - ? WHERE id = ?', (candy_overflow, target.id))
                        candy_overflow = 0
                    else:
                        await cursor.execute(f'UPDATE Users SET bank = 0 WHERE id = ?', (target.id,))
                        candy_overflow = candy_overflow - bank_balance
                        
                await connection.commit()
                
        logger.info(f"DB_UPDATE: Removed {amount} candy to user: {target_name}'s id: {target_id} total: {current_candy}")
        await interaction.response.send_message(f"You took {amount-candy_overflow} candy from {target.mention}!")
        
    @app_commands.command(name="reset-cooldowns", description="Resets all users cooldowns.")
    @app_commands.default_permissions(administrator=True)
    async def resetcooldowns(self, interaction: discord.Interaction):
        # Respond immediately to prevent webhook timeout
        await interaction.response.send_message("⏳ Resetting all user cooldowns...")
        
        try:
            async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    # Get count before update
                    await cursor.execute('SELECT COUNT(*) FROM users')
                    user_count = (await cursor.fetchone())[0]
                    
                    # Reset all cooldowns
                    await cursor.execute('''
                        UPDATE users 
                        SET rob_cooldown = 0,
                            robbed_cooldown = 0,
                            daily_cooldown = 0,
                            hourly_cooldown = 0,
                            weekly_cooldown = 0
                    ''')
                    
                    await connection.commit()
            
            # Edit the original response
            await interaction.edit_original_response(content=f"✅ Successfully reset cooldowns for {user_count} users!")
            
        except Exception as e:
            print(f"Error resetting cooldowns: {e}")
            try:
                await interaction.edit_original_response(content="❌ An error occurred while resetting cooldowns.")
            except:
                # If editing fails, try to send a new message
                await interaction.channel.send("❌ An error occurred while resetting cooldowns.")
    
    @app_commands.command(name="admin-help", description="Check what all of your commands do.")
    @app_commands.default_permissions(administrator=True)
    async def adminhelp(self, interaction: discord.Interaction):

        user_id = interaction.user.id
        user_name = interaction.user.name
        user = interaction.user

        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(user_id, user_name)

        embed = discord.Embed(title=f"Help!", description="These are all of the available admin commands! If a command throws an error, make sure to read what should be entered into the field or ask Noah", color=0x9B59B6)
        embed.set_author(
            name=f"{user.name}",
            icon_url=user.display_avatar.url)

        embed.add_field(name="Give Candy",value=f"Give a user candy.\n",inline=False)
        embed.add_field(name="Remove Candy",value=f"Remove a users candy, also takes from their bank if their balance is not enough\n",inline=False)
        embed.add_field(name="Reset Cooldowns",value=f"Resets all cooldowns for all users. Use with caution.\n",inline=False)
        embed.add_field(name="Add store item",value=f"Lets you add a store item. Make sure to put the role name without the @ or None if it is not a role. To add quantity follow the same instructions and simply put the quantity you want added into the quantity field. Category for filters\n",inline=False)
        embed.add_field(name="Remove store item",value=f"Lets you remove a store item. If you want a store item gone simply set the quantity to 999 (enough that the current stock goes to 0). If you want less quantity, put in the quantity you want removed.\n",inline=False)
        embed.add_field(name="Create raffle",value=f"Lets you create a raffle. Put in the details correctly.", inline=False)
        embed.add_field(name="Draw raffle",value=f"Rolls out all of the winners for a raffle. Make sure to not do it early!", inline=False)
    
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
    # @app_commands.command(name="test", description="Noah's Testing Command.")
    # @app_commands.default_permissions(administrator=True)
    # async def adminhelp(self, interaction: discord.Interaction, target: discord.Member):

    #     user_id = interaction.user.id
    #     user_name = interaction.user.name
    #     user = interaction.user
        

    #     utils_cog = self.bot.get_cog("Utils")
    #     await utils_cog.check_user_exists(user_id, user_name)
        
    #     async with asqlite.connect('./database.db') as connection:
    #             async with connection.cursor() as cursor:
    #                 await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (user_id,))
    #                 db_result = await cursor.fetchone()
    #                 db_result= db_result[0]
    #                 await cursor.execute(f'UPDATE users SET candy = ? WHERE id = ?', (int(db_result), user_id))
    #                 await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (target.id,))
    #                 db_result = await cursor.fetchone()
    #                 db_result= db_result[0]
    #                 await cursor.execute(f'UPDATE users SET candy = ? WHERE id = ?', (int(db_result), target.id))
                    
                    

async def setup(bot: commands.Bot):
    await bot.add_cog(AdminCommands(bot))