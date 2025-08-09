import discord, random, asyncio
from discord.ext import commands
from discord import app_commands
from discord.ui import Button, View
import sqlite3

RPS_BOT_CHOICES=["rock","paper","scissors"]
RPS_SYMBOLS={"rock": "🪨",
        "paper": "📄",
        "scissors":"✂️",
        "question_mark":"❓"}

COIN_TOSS_CHOICES = []
COIN_SYMBOLS = []

class Gamble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="rps", description="Gamble on rock paper scissors!")
    async def rps(self, interaction: discord.Interaction, bet: int):

        winnings = 0
        won = False

        if bet <= 0:
            await interaction.response.send_message("Earn some candy before you try to gamble...", ephemeral=False)
            return

        user_id = interaction.user.id
        user_name = interaction.user.name

        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(user_id, user_name)

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()

        cursor.execute(f'SELECT candy FROM users WHERE id = ?', (user_id,))
        user_candy_amount = cursor.fetchone()[0]
            
        connection.commit()
        connection.close()

        if user_candy_amount < bet:
            await interaction.response.send_message(f"{interaction.user.mention} can't afford to place that bet b-b-b-brokie.", ephemeral=True)
            return
        
        embed = discord.Embed(title=f"Rock Paper Scissors!", description=f"You: {RPS_SYMBOLS['question_mark']}      Bot: {RPS_SYMBOLS['question_mark']}.", color=0x9B59B6)
        embed.set_author(
            name=f"{user_name}",
            icon_url=interaction.user.display_avatar.url)

        buttons = View()
        rock_button = Button(label="🪨 Rock", style=discord.ButtonStyle.danger, custom_id="rock")
        paper_button = Button(label="📄 Paper", style=discord.ButtonStyle.danger, custom_id="paper")
        scissors_button = Button(label="✂️ Scissors", style=discord.ButtonStyle.danger, custom_id="scissors")

        buttons.add_item(rock_button)
        buttons.add_item(paper_button)
        buttons.add_item(scissors_button)

        await interaction.response.send_message(embed=embed,view=buttons, ephemeral=False)

        message = await interaction.original_response()

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        while True:
            try:
                inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
                await inter.response.defer()
                bot_pick = random.choice(RPS_BOT_CHOICES)
                embed.description= (f"You: {RPS_SYMBOLS[inter.data['custom_id']]}      Bot: {RPS_SYMBOLS[bot_pick]}.")

                #Player draws with bot
                if inter.data['custom_id'] == bot_pick:
                    embed.set_footer(text = "You tied! Try again!")
                    await message.edit(embed=embed, view=buttons)

                #Player winning conditions
                elif inter.data['custom_id'] == "rock" and bot_pick == "scissors":
                    won=True
                    winnings= int(bet * 1.9)
                    break
                elif inter.data['custom_id'] == "paper" and bot_pick == "rock":
                    won=True
                    winnings= int(bet * 1.9)
                    break
                elif inter.data['custom_id'] == "scissors" and bot_pick == "paper":
                    won=True
                    winnings= int(bet * 1.9)
                    break

                #Player losing conditions
                elif inter.data['custom_id'] == "scissors" and bot_pick == "rock":
                    break
                elif inter.data['custom_id'] == "rock" and bot_pick == "paper":
                    break
                elif inter.data['custom_id'] == "paper" and bot_pick == "scissors":
                    break 

            except Exception as e:
                print(f"Interaction failed with error: {e}")
                await message.delete()

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()

        cursor.execute(f'UPDATE users SET candy = candy - ? WHERE id = ?', (bet, user_id))
        cursor.execute(f'UPDATE users SET candy = candy + ? WHERE id = ?', (winnings, user_id))
            
        connection.commit()
        connection.close()

        buttons.clear_items()
        
        if won:
            embed.set_footer(text= f"You won! You won a total of {winnings}!")
        else:
            embed.set_footer(text= "You lost! Better luck next time!")
            
        await message.edit(embed=embed, view=buttons)
    
    @app_commands.command(name="coin-toss", description="Gamble on a coin toss!")
    async def cointoss(self, interaction: discord.Interaction, bet: int):

        winnings = 0
        won = False

        if bet <= 0:
            await interaction.response.send_message("Earn some candy before you try to gamble...", ephemeral=False)
            return

        user_id = interaction.user.id
        user_name = interaction.user.name

        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(user_id, user_name)

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()

        cursor.execute(f'SELECT candy FROM users WHERE id = ?', (user_id,))
        user_candy_amount = cursor.fetchone()[0]
            
        connection.commit()
        connection.close()

        if user_candy_amount < bet:
            await interaction.response.send_message(f"{interaction.user.mention} can't afford to place that bet b-b-b-brokie.", ephemeral=True)
            return
        
        embed = discord.Embed(title=f"Rock Paper Scissors!", description=f"You: {SYMBOLS['question_mark']}      Bot: {SYMBOLS['question_mark']}.", color=0x9B59B6)
        embed.set_author(
            name=f"{user_name}",
            icon_url=interaction.user.display_avatar.url)

        buttons = View()
        rock_button = Button(label="🪨 Rock", style=discord.ButtonStyle.danger, custom_id="rock")
        paper_button = Button(label="📄 Paper", style=discord.ButtonStyle.danger, custom_id="paper")
        scissors_button = Button(label="✂️ Scissors", style=discord.ButtonStyle.danger, custom_id="scissors")

        buttons.add_item(rock_button)
        buttons.add_item(paper_button)
        buttons.add_item(scissors_button)

        await interaction.response.send_message(embed=embed,view=buttons, ephemeral=False)

        message = await interaction.original_response()

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()
        except Exception as e:
            print(f"Interaction failed with error: {e}")
            return
        
        bot_pick = random.choice(RPS_BOT_CHOICES)
        embed.description= (f"You: {RPS_SYMBOLS[inter.data['custom_id']]}      Bot: {RPS_SYMBOLS[bot_pick]}.")

        #Player Wins
        if inter.data['custom_id'] == bot_pick:
            winnings = bet * 2
            embed.set_footer(text = f"You won {winnings} candy!")
            await message.edit(embed=embed, view=buttons)

        #Player losing conditions
        else:
            pass

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()

        cursor.execute(f'UPDATE users SET candy = candy - ? WHERE id = ?', (bet, user_id))
        cursor.execute(f'UPDATE users SET candy = candy + ? WHERE id = ?', (winnings, user_id))
            
        connection.commit()
        connection.close()

        buttons.clear_items()
        
        if won:
            embed.set_footer(text= f"You won! You won a total of {winnings}!")
        else:
            embed.set_footer(text= "You lost! Better luck next time!")
            
        await message.edit(embed=embed, view=buttons)
    


async def setup(bot: commands.Bot):
    await bot.add_cog(Gamble(bot))