import discord, random, asyncio
from discord.ext import commands
from discord import app_commands, File
from discord.ui import Button, View
import sqlite3

RPS_BOT_CHOICES=["rock","paper","scissors"]
RPS_SYMBOLS={"rock": "🪨",
        "paper": "📄",
        "scissors":"✂️",
        "question_mark":"❓"}

COIN_TOSS_CHOICES = ["heads","tails","side"]
COIN_WEIGHTS = [0.45,0.45,0.1]

class Gamble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="rps", description="Gamble on rock paper scissors!")
    async def rps(self, interaction: discord.Interaction, bet: int):

        winnings = 0
        won = False
        user_id = interaction.user.id
        user_name = interaction.user.name

        if await self.check_user_bet(interaction, bet, user_id, user_name):
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
        user_id = interaction.user.id
        user_name = interaction.user.name
        
        if await self.check_user_bet(interaction, bet, user_id, user_name):
            return
         
        embed = discord.Embed(title=f"Coin toss!", description=f"Make your choice!.", color=0x9B59B6)
        embed.set_author(
            name=f"{user_name}",
            icon_url=interaction.user.display_avatar.url)

        buttons = View()
        heads_button = Button(label="Heads", style=discord.ButtonStyle.danger, custom_id="heads")
        tails_button = Button(label="Tails", style=discord.ButtonStyle.danger, custom_id="tails")
        side_button = Button(label="Side", style=discord.ButtonStyle.danger, custom_id="side")

        buttons.add_item(heads_button)
        buttons.add_item(tails_button)
        buttons.add_item(side_button)
        
        embed.set_image(url=f"attachment://start.png")
        gif_file = File(f"images/start.png", filename=f"start.png")

        await interaction.response.send_message(embed=embed,view=buttons, file=gif_file, ephemeral=False)

        message = await interaction.original_response()

        def check(inter):
            return inter.user.id == interaction.user.id and inter.message.id == message.id

        try:
            inter = await self.bot.wait_for('interaction', timeout=60.0, check=check)
            await inter.response.defer()
        except Exception as e:
            print(f"Interaction failed with error: {e}")
            return
        
        bot_pick = random.choices(COIN_TOSS_CHOICES, weights=COIN_WEIGHTS, k=1)[0]
        embed.description= (f"Flipping.")
        
        
        buttons.clear_items()
        
        embed.set_image(url=f"attachment://{bot_pick}.gif")
        gif_file = File(f"images/{bot_pick}.gif", filename=f"{bot_pick}.gif")
        await message.edit(embed=embed,view=buttons, attachments=[gif_file])
        
        await asyncio.sleep(3.9 if bot_pick != "side" else 2.7)
        
        embed.set_image(url=f"attachment://end-{bot_pick}.webp")
        gif_file = File(f"images/end-{bot_pick}.webp", filename=f"end-{bot_pick}.webp")
        await message.edit(embed=embed,view=buttons, attachments=[gif_file])
            
        #Player Wins, Dont need to check losing conditions
        if inter.data['custom_id'] == bot_pick and inter.data['custom_id'] == "side":
            winnings = bet * 9
            won=True
        elif inter.data['custom_id'] == bot_pick:
            winnings = bet * 2
            won=True
        

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()

        cursor.execute(f'UPDATE users SET candy = candy - ? WHERE id = ?', (bet, user_id))
        cursor.execute(f'UPDATE users SET candy = candy + ? WHERE id = ?', (winnings, user_id))
            
        connection.commit()
        connection.close()
        
        embed.description= (f"Results:")
        
        if won:
            embed.set_footer(text = f"You won {winnings} candy!")
        else:
            embed.set_footer(text = f"You lost. Better luck next time!")
               
        await message.edit(embed=embed, view=buttons)
        
    async def check_user_bet(self, interaction, bet, user_id, user_name):
        
        if bet <= 0:
            await interaction.response.send_message("Earn some candy before you try to gamble...", ephemeral=False)
            return True
        
        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(user_id, user_name)

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()

        cursor.execute(f'SELECT candy FROM users WHERE id = ?', (user_id,))
        user_candy_amount = cursor.fetchone()[0]
            
        connection.commit()
        connection.close()

        if user_candy_amount < bet:
            await interaction.response.send_message(f"{interaction.user.mention} can't afford to place that bet b-b-b-brokie.", ephemeral=False)
            return True
        
        return False


async def setup(bot: commands.Bot):
    await bot.add_cog(Gamble(bot))