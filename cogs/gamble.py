import discord, random, asyncio, asqlite
from discord.ext import commands
from discord import app_commands, File
from discord.ui import Button, View
from PIL import Image, ImageDraw, ImageFont
import sqlite3
import io

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
                
    @app_commands.command(name="blackjack", description="Play some blackjack!")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        
        user_id = interaction.user.id
        user_name = interaction.user.name

        if await self.check_user_bet(interaction, bet, user_id, user_name):
            return
        
        view = self.BJView(interaction.user, bet, self)
        embed = await view.create_initial_embed()
        file = view.create_blackjack_image()
        embed.set_image(url="attachment://blackjack.png")
        await interaction.response.send_message(embed=embed, view=view, file=file)
        
        # Store the message for timeout handling
        view.message = await interaction.original_response()
        
    class BJView(discord.ui.View):
        def __init__(self, user: discord.User, bet: int, cog):
            super().__init__(timeout=60)
            self.user = user
            self.bet = bet
            self.cog = cog
            self.user_choice = None
            self.message = None
            self.game_state = None
            self.game_over = False
            self.timeout_processed = False  
            
            # Initialize deck and deal cards
            self.deck = self.create_deck()
            self.user_cards = [self.draw_card(), self.draw_card()]
            self.dealer_cards = [self.draw_card(), self.draw_card()]  
            
            # Calculate totals
            self.user_total = self.calculate_hand_value(self.user_cards)
            self.dealer_total = self.calculate_hand_value([self.dealer_cards[0]])  # Only count visible card initially
            
            # Check for blackjack and disable buttons if found
            if self.user_total == 21:
                self.game_state = "Blackjack"
                self.game_over = True
                for item in self.children:
                    item.disabled = True
        
        @discord.ui.button(label="Hit", style=discord.ButtonStyle.danger)
        async def hit_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            await self.process_choice(interaction, "hit")
        
        @discord.ui.button(label="Stand", style=discord.ButtonStyle.success)
        async def stand_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            await self.process_choice(interaction, "stand")
        
        @discord.ui.button(label="Double Down", style=discord.ButtonStyle.secondary)
        async def double_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            await self.process_choice(interaction, "double")
        
        async def process_choice(self, interaction: discord.Interaction, choice: str):
            if choice == "double":
                if not await self.check_double():
                    embed = await self.create_embed()
                    embed.set_footer(text="Not enough candy to double down!")
                    await interaction.response.edit_message(embed=embed, view=self)
                    return
                
                # Double the bet and draw one card
                self.bet *= 2
                self.user_cards.append(self.draw_card())
                self.user_total = self.calculate_hand_value(self.user_cards)
                
                if self.user_total > 21:
                    self.game_state = "Bust"
                    self.game_over = True
                    for item in self.children:
                        item.disabled = True
                else:
                    # Must stand after double down
                    await self.dealer_turn()
                    self.game_over = True
                    for item in self.children:
                        item.disabled = True
            
            elif choice == "hit":
                self.user_cards.append(self.draw_card())
                for item in self.children:
                    if isinstance(item, discord.ui.Button) and item.label == "Double Down":
                        item.disabled = True
                self.user_total = self.calculate_hand_value(self.user_cards)
                
                if self.user_total > 21:
                    self.game_state = "Bust"
                    self.game_over = True
                    for item in self.children:
                        item.disabled = True
            
            elif choice == "stand":
                await self.dealer_turn()
                self.game_over = True
                for item in self.children:
                    item.disabled = True
            
            # Determine winner and update coins
            if self.game_over:
                winnings = await self.determine_winner()
                await self.cog.user_update_candy(winnings, self.bet, self.user.id)
            
            # Create updated embed and image
            embed = await self.create_embed()
            file = self.create_blackjack_image()
            embed.set_image(url="attachment://blackjack.png")
            
            await interaction.response.edit_message(embed=embed, view=self, attachments=[file])
            
            if self.game_over:
                self.stop()
        
        async def dealer_turn(self):
            """Dealer draws cards until 17 or higher"""
            # First, calculate total with both initial cards
            self.dealer_total = self.calculate_hand_value(self.dealer_cards)
            
            # Then draw additional cards if needed
            while self.dealer_total < 17:
                self.dealer_cards.append(self.draw_card())
                self.dealer_total = self.calculate_hand_value(self.dealer_cards)
        
        async def determine_winner(self):
            """Determine winner and return winnings"""
            if self.game_state == "Blackjack":
                return int(self.bet * 2.5)  # Blackjack pays 2.5x
            elif self.game_state == "Bust":
                return 0  # Player busted, loses bet
            elif self.dealer_total > 21:
                return self.bet * 2  # Dealer busted, player wins
            elif self.user_total > self.dealer_total:
                return self.bet * 2  # Player wins
            elif self.user_total == self.dealer_total:
                return self.bet  # Push, return bet
            else:
                return 0  # Dealer wins
        
        def create_blackjack_image(self):
            """Create a visual representation of the blackjack game using Pillow"""
            # Create image
            width, height = 800, 600
            img = Image.new('RGB', (width, height), color=(0, 100, 0))  # Green background
            draw = ImageDraw.Draw(img)
            
            try:
                # Try to use a better font
                title_font = ImageFont.truetype("arial.ttf", 36)
                card_font = ImageFont.truetype("arial.ttf", 24)
                text_font = ImageFont.truetype("arial.ttf", 20)
            except:
                # Fallback to default font
                title_font = ImageFont.load_default()
                card_font = ImageFont.load_default()
                text_font = ImageFont.load_default()
            
            # Title
            draw.text((width//2 - 100, 30), "BLACKJACK", fill='white', font=title_font)
            
            # Dealer section
            dealer_y = 120
            draw.text((50, dealer_y), f"DEALER - {self.dealer_total}", fill='white', font=text_font)
            
            # Draw dealer cards
            card_x = 50
            for i, card in enumerate(self.dealer_cards):
                if not self.game_over and i == 1:
                    # Hide second dealer card if game not over
                    # Draw face-down card
                    draw.rectangle([card_x, dealer_y + 30, card_x + 100, dealer_y + 170], 
                                fill='darkred', outline='black', width=2)
                    draw.text((card_x + 35, dealer_y + 80), "?", fill='white', font=card_font)
                else:
                    self.draw_card_face(draw, card, card_x, dealer_y + 30, card_font)
                card_x += 120
            
            # Player section
            player_y = 320
            draw.text((50, player_y), f"{self.user.name.upper()} - {self.user_total}", fill='white', font=text_font)
            
            # Draw player cards
            card_x = 50
            for card in self.user_cards:
                self.draw_card_face(draw, card, card_x, player_y + 30, card_font)
                card_x += 120
            
            # Game status
            status_y = 520
            if self.game_state == "Blackjack":
                draw.text((width//2 - 80, status_y), "BLACKJACK!", fill='gold', font=text_font)
            elif self.game_state == "Bust":
                draw.text((width//2 - 50, status_y), "BUST!", fill='red', font=text_font)
            elif self.game_state == "Timeout":
                draw.text((width//2 - 100, status_y), "TIMEOUT - YOU LOSE!", fill='red', font=text_font)
            elif self.game_over:
                if self.dealer_total > 21:
                    draw.text((width//2 - 80, status_y), "DEALER BUST!", fill='gold', font=text_font)
                elif self.user_total > self.dealer_total:
                    draw.text((width//2 - 50, status_y), "YOU WIN!", fill='gold', font=text_font)
                elif self.user_total == self.dealer_total:
                    draw.text((width//2 - 30, status_y), "PUSH", fill='yellow', font=text_font)
                else:
                    draw.text((width//2 - 60, status_y), "DEALER WINS", fill='red', font=text_font)
            
            # Bet amount
            draw.text((width - 200, 50), f"Bet: {self.bet}", fill='white', font=text_font)
            
            # Convert to Discord file
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return discord.File(buffer, filename='blackjack.png')
        
        def draw_card_face(self, draw, card, x, y, font):
            """Draw a face-up card"""
            # Card background
            draw.rectangle([x, y, x + 100, y + 140], fill='white', outline='black', width=2)
            
            # Card text
            rank = card[:-1]
            suit = card[-1]
            
            # Color based on suit
            color = 'red' if suit in ['♥', '♦'] else 'black'
            
            # Get text size for centering
            try:
                # Get bounding box for proper centering
                rank_bbox = draw.textbbox((0, 0), rank, font=font)
                suit_bbox = draw.textbbox((0, 0), suit, font=font)
                
                rank_width = rank_bbox[2] - rank_bbox[0]
                rank_height = rank_bbox[3] - rank_bbox[1]
                suit_width = suit_bbox[2] - suit_bbox[0]
                suit_height = suit_bbox[3] - suit_bbox[1]
            except:
                # Fallback for older PIL versions
                rank_width, rank_height = font.getsize(rank)
                suit_width, suit_height = font.getsize(suit)
            
            # Draw rank in top-left corner
            draw.text((x + 10, y + 10), rank, fill=color, font=font)
            
            # Draw large centered suit symbol
            suit_x = x + (100 - suit_width) // 2
            suit_y = y + (140 - suit_height) // 2
            draw.text((suit_x, suit_y), suit, fill=color, font=font)
            
            # Draw rank in bottom-right corner (upside down style)
            rank_x = x + 100 - rank_width - 10
            rank_y = y + 140 - rank_height - 10
            draw.text((rank_x, rank_y), rank, fill=color, font=font)
        
        async def create_embed(self):
            embed = discord.Embed(
                title="🃏 Blackjack", 
                color=0x00ff00 if self.game_over and self.game_state not in ["Bust", "Timeout"] else 0x9B59B6
            )
            embed.set_author(
                name=f"{self.user.name}",
                icon_url=self.user.display_avatar.url
            )
            
            # Game status footer
            if self.game_state == "Blackjack":
                winnings = int(self.bet * 2.5)
                embed.set_footer(text=f"🎉 Blackjack! You won {winnings} candy! 🎉")
            elif self.game_state == "Bust":
                embed.set_footer(text=f"💥 Bust! You lost {self.bet} candy 💥")
            elif self.game_state == "Timeout":
                embed.set_footer(text=f"⏰ Timeout! You lost {self.bet} candy ⏰")
            elif self.game_over:
                winnings = await self.determine_winner()
                if winnings > self.bet:
                    embed.set_footer(text=f"🎉 You won {winnings - self.bet} candy! 🎉")
                elif winnings == self.bet:
                    embed.set_footer(text="🤝 Push! Your bet is returned 🤝")
                else:
                    embed.set_footer(text=f"😞 You lost {self.bet} candy 😞")
            else:
                embed.set_footer(text="Choose your move!")
            
            return embed
        
        async def create_initial_embed(self):
            # Check for initial blackjack
            if self.user_total == 21:
                # Process the blackjack win immediately
                winnings = int(self.bet * 2.5)
                await self.cog.user_update_candy(winnings, self.bet, self.user.id)
            
            embed = await self.create_embed()
            return embed
            
        async def on_timeout(self):
            # Prevent double processing
            if self.timeout_processed or self.game_over:
                return
            
            self.timeout_processed = True
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            # Process timeout as a loss if game wasn't already over
            if not self.game_over:
                self.game_state = "Timeout"
                self.game_over = True
                
                # Player loses the bet on timeout (dealer automatically wins)
                await self.cog.user_update_candy(0, self.bet, self.user.id)
                
                # Update the message to show timeout
                if self.message:
                    try:
                        embed = await self.create_embed()
                        file = self.create_blackjack_image()
                        embed.set_image(url="attachment://blackjack.png")
                        await self.message.edit(embed=embed, view=self, attachments=[file])
                    except:
                        # If we can't update the message, at least the money was deducted
                        pass
                
        async def check_double(self):
            async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (self.user.id,))
                    db_result = await cursor.fetchone()
                    
                    if self.bet * 2 > db_result[0]:
                        return False
                    else:
                        return True
        
        def create_deck(self):
            suits = ['♠', '♥', '♦', '♣']
            ranks = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K']
            deck = []
            for suit in suits:
                for rank in ranks:
                    deck.append(f"{rank}{suit}")
            random.shuffle(deck)
            return deck

        def draw_card(self):
            return self.deck.pop()
        
        def calculate_hand_value(self, cards):
            total = 0
            aces = 0
            
            for card in cards:
                rank = card[:-1]  # Remove suit
                if rank in ['J', 'Q', 'K']:
                    total += 10
                elif rank == 'A':
                    aces += 1
                    total += 11
                else:
                    total += int(rank)
            
            # Handle aces
            while total > 21 and aces > 0:
                total -= 10
                aces -= 1
            
            return total
        
        
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