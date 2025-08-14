import discord, random, asyncio, asqlite
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
        
        user_id = interaction.user.id
        user_name = interaction.user.name

        if await self.check_user_bet(interaction, bet, user_id, user_name):
            return
        
        view = self.RPSView(interaction.user, bet, self)
        embed = view.create_initial_embed()  
        await interaction.response.send_message(embed=embed, view=view)
    
        # Store the message so we can edit on timeout
        view.message = await interaction.original_response()
        
    class RPSView(discord.ui.View):
        def __init__(self, user: discord.User, bet: int, cog):
            super().__init__(timeout=60)
            self.user = user
            self.bet = bet
            self.cog = cog
            self.user_choice = None
            self.message = None
            
        @discord.ui.button(label="🪨 Rock", style=discord.ButtonStyle.danger)
        async def rock_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            await self.process_choice(interaction, "rock")
        
        @discord.ui.button(label="📄 Paper", style=discord.ButtonStyle.danger)
        async def paper_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            await self.process_choice(interaction, "paper")
        
        @discord.ui.button(label="✂️ Scissors", style=discord.ButtonStyle.danger)
        async def scissors_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            await self.process_choice(interaction, "scissors")
        
        async def process_choice(self, interaction: discord.Interaction, choice: str):
            bot_choice = random.choice(["rock", "paper", "scissors"])
            
            # Determine winner
            if choice == bot_choice:
                # It's a tie don't stop the view, let them try again
                embed = self.create_embed(choice, bot_choice, "tie")
                await interaction.response.edit_message(embed=embed, view=self)
                return
            
            won = False
            if (choice == "rock" and bot_choice == "scissors") or \
            (choice == "paper" and bot_choice == "rock") or \
            (choice == "scissors" and bot_choice == "paper"):
                won = True
                winnings = int(self.bet * 1.9)
            else:
                winnings = 0
            
            await self.cog.user_update_candy(winnings, self.bet, self.user.id)
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            embed = self.create_embed(choice, bot_choice, "win" if won else "lose", winnings)
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
        
        def create_initial_embed(self):
            embed = discord.Embed(
                title="Rock Paper Scissors!", 
                description=f"You: {RPS_SYMBOLS['question_mark']}      Bot: {RPS_SYMBOLS['question_mark']}.", 
                color=0x9B59B6
            )
            embed.set_author(
                name=f"{self.user.name}",
                icon_url=self.user.display_avatar.url
            )
            embed.set_footer(text="Choose your move!")
            return embed
        
        def create_embed(self, user_choice, bot_choice, result, winnings=0):
            embed = discord.Embed(title=f"Rock Paper Scissors!", description=f"You: {RPS_SYMBOLS[user_choice]}      Bot: {RPS_SYMBOLS[bot_choice]}.", color=0x9B59B6)
            embed.set_author(
                name=f"{self.user.name}",
                icon_url=self.user.display_avatar.url)

            if result == "tie":
               embed.set_footer(text = "You tied! Try again!")
            elif result == "win":
                embed.set_footer(text= f"You won! You won a total of {winnings}!")
            else:
                embed.set_footer(text= "You lost! Better luck next time!")
            
            return embed
           
        async def on_timeout(self):
            # Disable all buttons when timeout occurs
            for item in self.children:
                item.disabled = True
            if self.message:
                await self.message.edit(view=self)
    
    @app_commands.command(name="coin-toss", description="Gamble on a coin toss!")
    async def cointoss(self, interaction: discord.Interaction, bet: int):
        
        user_id = interaction.user.id
        user_name = interaction.user.name
        
        if await self.check_user_bet(interaction, bet, user_id, user_name):
            return
        
        view = self.CoinTossView(interaction.user, bet, self)
        embed, gif_file = view.create_initial_embed()  
        await interaction.response.send_message(embed=embed, view=view, file=gif_file, ephemeral=False)
    
        # Store the message so we can edit on timeout
        view.message = await interaction.original_response()
        
        
    class CoinTossView(discord.ui.View):
        def __init__(self, user: discord.User, bet: int, cog):
            super().__init__(timeout=60)
            self.user = user
            self.bet = bet
            self.cog = cog
            self.user_choice = None
            self.message = None
            
        @discord.ui.button(label="Heads", style=discord.ButtonStyle.danger)
        async def heads_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            await self.process_choice(interaction, "heads")
        
        @discord.ui.button(label="Tails", style=discord.ButtonStyle.danger)
        async def tails_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            await self.process_choice(interaction, "tails")
        
        @discord.ui.button(label="Side", style=discord.ButtonStyle.danger)
        async def side_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            await self.process_choice(interaction, "side")
        
        async def process_choice(self, interaction: discord.Interaction, choice: str):
           # Defer first to acknowledge the button click
            await interaction.response.defer()
            
            bot_choice = random.choices(COIN_TOSS_CHOICES, weights=COIN_WEIGHTS, k=1)[0]
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            # Show flipping animation
            embed, gif_file = self.create_gif_embed(bot_choice)
            await interaction.edit_original_response(embed=embed, view=self, attachments=[gif_file])
            
            await asyncio.sleep(3.9 if bot_choice != "side" else 2.7)
            
            won = False
            
            # User wins side
            if choice == bot_choice and choice == "side":
                won = True
                winnings = self.bet*9
                embed, gif_file = self.create_embed(bot_choice, winnings, won)
                await interaction.edit_original_response(embed=embed, view=self, attachments=[gif_file])
                
            elif choice == bot_choice:
                won = True
                winnings = self.bet*2
                embed, gif_file = self.create_embed(bot_choice, winnings, won)
                await interaction.edit_original_response(embed=embed, view=self, attachments=[gif_file])
            else:
                winnings = 0
                embed, gif_file = self.create_embed(bot_choice, winnings, won)
                await interaction.edit_original_response(embed=embed, view=self, attachments=[gif_file])

            await self.cog.user_update_candy(winnings, self.bet, self.user.id)
            
            self.stop()
        
        def create_initial_embed(self):
            embed = discord.Embed(title=f"Coin toss!", description=f"Make your choice!.", color=0x9B59B6)
            embed.set_author(
            name=f"{self.user.name}",
            icon_url=self.user.display_avatar.url)

            embed.set_image(url=f"attachment://start.png")
            gif_file = File(f"images/start.png", filename=f"start.png")

            return embed, gif_file
        
        def create_gif_embed(self, bot_pick):
            embed = discord.Embed(title=f"Coin toss!", description=f"Flipping!", color=0x9B59B6)
            embed.set_author(
            name=f"{self.user.name}",
            icon_url=self.user.display_avatar.url)

            embed.set_image(url=f"attachment://{bot_pick}.gif")
            gif_file = File(f"images/{bot_pick}.gif", filename=f"{bot_pick}.gif")
            
            return embed, gif_file
            
        def create_embed(self, choice, winnings, won):
            
            embed = discord.Embed(title=f"Coin toss!", description=f"Result:", color=0x9B59B6)
            embed.set_author(
            name=f"{self.user.name}",
            icon_url=self.user.display_avatar.url)
            
            embed.set_image(url=f"attachment://end-{choice}.webp")
            gif_file = File(f"images/end-{choice}.webp", filename=f"end-{choice}.webp")
            
            if won:
                embed.set_footer(text = f"You won {winnings} candy!")
            else:
                embed.set_footer(text = f"You lost. Better luck next time!")
            
            return embed, gif_file
            
        async def on_timeout(self):
            # Disable all buttons when timeout occurs
            for item in self.children:
                item.disabled = True
            if self.message:
                await self.message.edit(view=self)
        
        
    async def check_user_bet(self, interaction, bet, user_id, user_name):
        
        if bet <= 0:
            await interaction.response.send_message("Earn some candy before you try to gamble...", ephemeral=False)
            return True
        
        utils_cog = self.bot.get_cog("Utils")
        await utils_cog.check_user_exists(user_id, user_name)

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:

                await cursor.execute(f'SELECT candy FROM users WHERE id = ?', (user_id,))
                user_candy_amount = await cursor.fetchone()
                user_candy_amount = user_candy_amount[0]
                

        if user_candy_amount < bet:
                await interaction.response.send_message(f"{interaction.user.mention} can't afford to place that bet b-b-b-brokie.", ephemeral=False)
                return True      
        
        return False
    
    async def user_update_candy(self, winnings, bet, user_id):
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:

                await cursor.execute(f'UPDATE users SET candy = candy + ? WHERE id = ?', ((winnings-bet), user_id))
                
                await connection.commit()
                


async def setup(bot: commands.Bot):
    await bot.add_cog(Gamble(bot))