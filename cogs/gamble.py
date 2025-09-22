import discord, random, asyncio, asqlite
from discord.ext import commands
from discord import app_commands, File
from discord.ui import Button, View
from PIL import Image, ImageDraw, ImageFont
import io
import logging

logger = logging.getLogger(__name__)

RPS_BOT_CHOICES=["rock","paper","scissors"]
RPS_SYMBOLS={"rock": "🪨",
        "paper": "📄",
        "scissors":"✂️",
        "question_mark":"❓"}

COIN_TOSS_CHOICES = ["heads","tails","side"]
COIN_WEIGHTS = [0.45,0.45,0.1]

# American Roulette number colors
RED_NUMBERS = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
BLACK_NUMBERS = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}
GREEN_NUMBERS = {0, 37}  # 0 and 00 (represented as 37)

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
            gif_file = File(io.BytesIO(self.cog.bot.image_cache["start.png"]), filename="start.png")

            return embed, gif_file
        
        def create_gif_embed(self, bot_pick):
            embed = discord.Embed(title=f"Coin toss!", description=f"Flipping!", color=0x9B59B6)
            embed.set_author(
            name=f"{self.user.name}",
            icon_url=self.user.display_avatar.url)

            embed.set_image(url=f"attachment://{bot_pick}.gif")
            gif_file = File(io.BytesIO(self.cog.bot.image_cache[f"{bot_pick}.gif"]), filename=f"{bot_pick}.gif")
            
            return embed, gif_file
            
        def create_embed(self, choice, winnings, won):
            
            embed = discord.Embed(title=f"Coin toss!", description=f"Result:", color=0x9B59B6)
            embed.set_author(
            name=f"{self.user.name}",
            icon_url=self.user.display_avatar.url)
            
            embed.set_image(url=f"attachment://end-{choice}.webp")
            gif_file = File(io.BytesIO(self.cog.bot.image_cache[f"end-{choice}.webp"]), filename=f"end-{choice}.webp")
            
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

    @app_commands.command(name="slot-machine", description="Use the slot machine!")
    async def slotmachine(self, interaction: discord.Interaction, bet: int):
        
        user_id = interaction.user.id
        user_name = interaction.user.name

        if await self.check_user_bet(interaction, bet, user_id, user_name):
            return
        
        view = self.SlotMachineView(interaction.user, bet, self)
        embed = view.create_initial_embed()  
        await interaction.response.send_message(embed=embed, view=view)

        # Store the message so we can edit on timeout
        view.message = await interaction.original_response()

    class SlotMachineView(discord.ui.View):
        def __init__(self, user: discord.User, bet: int, cog):
            super().__init__(timeout=45)
            self.user = user
            self.bet = bet
            self.cog = cog
            self.message = None
            self.is_spinning = False
            self.game_completed = False
            
            # Slot machine symbols and their weights/payouts
            self.symbols = ["🍒", "🍋", "🍊", "🍇", "🔔", "💎"]
            self.symbol_weights = [35, 30, 20, 10, 4, 1]  # Higher = more common
            
            self.payout_table = {
                # --- Three of a kind (main wins) ---
                "💎💎💎": 300,   # Jackpot (super rare)
                "🔔🔔🔔": 30,    # Very rare
                "🍇🍇🍇": 12,    # Rare
                "🍊🍊🍊": 5,     # Uncommon
                "🍋🍋🍋": 2.5,   # Common
                "🍒🍒🍒": 1.5,   # Most common

                # --- Mixed combos (toned down) ---
                "🍒🍒🍊": 1.2,   # Used to be 3x → now just above break-even
                "🍒🍋🍊": 0.5,   # Small consolation
                "💎💎🍋": 8,     # Two diamonds + common
                "💎💎🍊": 8,
                "💎💎🍒": 8,
                "🔔🔔🍒": 3,     # Reduced
                "🔔🔔🍋": 3,

                # --- Two of a kind (mostly losses disguised as wins) ---
                "💎💎": 3,       # Still decent
                "🔔🔔": 1,       # Break-even
                "🍇🍇": 0.7,     # Small loss
                "🍊🍊": 0.5,     # Half back
                "🍋🍋": 0.3,     # Bigger loss
                "🍒🍒": 0.1,     # Token return only
                }
            
        @discord.ui.button(label="🎰 SPIN!", style=discord.ButtonStyle.success, custom_id="spin_button")
        async def spin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            
            if self.is_spinning:
                await interaction.response.send_message("Wait for the current spin to finish!", ephemeral=True)
                return
            
            # Check if user still has enough chips for another bet
            user_id = interaction.user.id
            async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute(f'SELECT candy FROM Users WHERE id = ?', (self.user.id,))
                    result = await cursor.fetchone()
                    
            if result is None or result[0] < self.bet:
                await interaction.response.send_message("You don't have enough chips for another spin!", ephemeral=True)
                return
                
            self.game_completed = False
            
            await self.start_spinning(interaction)
        
        async def start_spinning(self, interaction: discord.Interaction):
            self.is_spinning = True
            self.children[0].disabled = True  # Disable spin button during spin
            
            await interaction.response.defer()
            
            # Pre-determine the final 3x3 grid
            final_grid = []
            for row in range(3):
                row_symbols = []
                for col in range(3):
                    symbol = random.choices(self.symbols, weights=self.symbol_weights, k=1)[0]
                    row_symbols.append(symbol)
                final_grid.append(row_symbols)
            
            # Spinning animation - all reels spin together
            for spin_count in range(10):
                # Create random spinning grid
                spinning_grid = []
                for row in range(3):
                    row_symbols = []
                    for col in range(3):
                        symbol = random.choice(self.symbols)
                        row_symbols.append(symbol)
                    spinning_grid.append(row_symbols)
                
                embed = discord.Embed(
                    title="🎰 **SLOT MACHINE** 🎰",
                    description=self.create_slot_display(spinning_grid),
                    color=0xFFD700
                )
                embed.set_author(
                    name=f"{self.user.name}'s Slot Machine",
                    icon_url=self.user.display_avatar.url
                )
                embed.add_field(name="Bet Amount", value=f"{self.bet} chips", inline=True)
                embed.set_footer(text="🎰 Spinning... 🎰")
                
                await self.message.edit(embed=embed, view=self)
                await asyncio.sleep(0.05)
            
            # Final result
            self.is_spinning = False
            await self.finalize_result(final_grid)
        
        async def finalize_result(self, grid):
            # Check all 3 horizontal lines for wins using new payout system
            winning_lines = []
            total_winnings = 0
            
            for row_index, row in enumerate(grid):
                line_winnings = self.calculate_line_payout(row)
                if line_winnings > 0:
                    actual_winnings = int(self.bet * line_winnings)
                    total_winnings += actual_winnings
                    winning_lines.append({
                        'line': row_index,
                        'symbols': row,
                        'winnings': actual_winnings,
                        'multiplier': line_winnings
                    })
            
            # Determine win type
            if total_winnings > 0:
                # Check if any line has jackpot (💎💎💎)
                has_jackpot = any("💎💎💎" == "".join(line['symbols']) for line in winning_lines)
                win_type = "jackpot" if has_jackpot else "win"
            else:
                win_type = "lose"
            
            # Update user's chips
            await self.cog.user_update_candy(total_winnings, self.bet, self.user.id)
            
            # Create final embed
            embed = self.create_final_embed(grid, win_type, total_winnings, winning_lines)
            
           
            self.children[0].disabled = False
            
            self.game_completed = True
            
            await self.message.edit(embed=embed, view=self)
        
        def calculate_line_payout(self, line):
            """Calculate payout for a single line based on symbol combinations"""
            line_str = "".join(line)
            
            # Check for exact matches in payout table first
            if line_str in self.payout_table:
                return self.payout_table[line_str]
            
            # Check for reverse of mixed combinations (order shouldn't matter for some)
            reverse_line = line_str[::-1]
            if reverse_line in self.payout_table:
                return self.payout_table[reverse_line]
            
            # Check for two of a kind (any two matching symbols in the line)
            symbol_counts = {}
            for symbol in line:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            # Find pairs and return the highest payout
            best_payout = 0
            for symbol, count in symbol_counts.items():
                if count == 2:
                    pair_key = f"{symbol}{symbol}"
                    if pair_key in self.payout_table:
                        payout = self.payout_table[pair_key]
                        if payout > best_payout:
                            best_payout = payout
            
            return best_payout
        
        def create_initial_embed(self):
            initial_grid = [
                ["❓", "❓", "❓"],
                ["❓", "❓", "❓"], 
                ["❓", "❓", "❓"]
            ]
            
            embed = discord.Embed(
                title="🎰 **SLOT MACHINE** 🎰",
                description=self.create_slot_display(initial_grid),
                color=0x9B59B6
            )
            embed.set_author(
                name=f"{self.user.name}'s Slot Machine",
                icon_url=self.user.display_avatar.url
            )
            embed.add_field(name="Bet Amount", value=f"{self.bet} chips", inline=True)
            embed.add_field(name="Win Condition", value="**3 matching OR 2 pairs OR mixed combos**", inline=True)
            embed.add_field(name="Potential Payouts", value=self.get_payout_info(), inline=False)
            embed.set_footer(text="Click SPIN to start!")
            return embed
        
        def create_slot_display(self, symbols_grid, winning_lines=None):
            line_indicators = ["", "", ""]
            if winning_lines:
                for line_info in winning_lines:
                    line_num = line_info['line']
                    line_indicators[line_num] = " ← WIN!"

            def format_cell(symbol):
                # Add spaces around symbol to keep each cell visually same width
                return f" {symbol} "

            display = "```\n"
            display += "┌───────────────┐\n"
            for i in range(3):
                row = f"│{format_cell(symbols_grid[i][0])}│{format_cell(symbols_grid[i][1])}│{format_cell(symbols_grid[i][2])}│"
                display += f"{row}{line_indicators[i]}\n"
            display += "└───────────────┘\n"
            display += "```"
            return display
        
        def create_final_embed(self, grid, win_type, total_winnings, winning_lines):
            if win_type == "jackpot":
                color = 0xFFD700  # Gold
                title = "🎰 **JACKPOT!** 🎰"
                footer_text = f"🎉 INCREDIBLE! You won {total_winnings} chips! 🎉"
            elif win_type == "win":
                color = 0x00FF00  # Green
                title = "🎰 **WINNER!** 🎰"
                footer_text = f"🎊 Awesome! You won {total_winnings} chips! 🎊"
            else:
                color = 0xFF0000  # Red
                title = "🎰 **SLOT MACHINE** 🎰"
                footer_text = f"😢 No luck this time! You lost {self.bet} chips."
            
            embed = discord.Embed(
                title=title,
                description=self.create_slot_display(grid, winning_lines),
                color=color
            )
            embed.set_author(
                name=f"{self.user.name}'s Slot Machine",
                icon_url=self.user.display_avatar.url
            )
            
            if winning_lines:
                lines_text = ""
                for line_info in winning_lines:
                    line_names = ["Top", "Middle", "Bottom"]
                    line_name = line_names[line_info['line']]
                    symbols = " ".join(line_info['symbols'])
                    lines_text += f"**{line_name}:** {symbols} (+{line_info['winnings']})\n"
                embed.add_field(name="Winning Lines", value=lines_text, inline=True)
                embed.add_field(name="Total Winnings", value=f"+{total_winnings} chips", inline=True)
            else:
                embed.add_field(name="No Wins", value="No matching lines", inline=True)
                embed.add_field(name="Loss", value=f"-{self.bet} chips", inline=True)
            
            embed.set_footer(text=footer_text)
            return embed
        
        def get_payout_info(self):
            lines = []

            # --- Major Wins (3 of a kind) ---
            majors = {
                "💎💎💎": "JACKPOT!",
                "🔔🔔🔔": "Very Rare",
                "🍇🍇🍇": "Rare",
                "🍊🍊🍊": "Uncommon",
                "🍋🍋🍋": "Common",
                "🍒🍒🍒": "Most Common"
            }
            lines.append("**🎯 Major Wins:**")
            for combo, label in majors.items():
                if combo in self.payout_table:
                    lines.append(f"{combo} = {self.payout_table[combo]}x ({label})")

            # --- Mixed Combos ---
            mixed = ["🍒🍒🍊", "🍒🍋🍊", "💎💎🍋", "💎💎🍊", "💎💎🍒", "🔔🔔🍒", "🔔🔔🍋"]
            lines.append("\n**🎲 Mixed Combos:**")
            for combo in mixed:
                if combo in self.payout_table:
                    lines.append(f"{combo} = {self.payout_table[combo]}x")

            # --- Two of a Kind ---
            pairs = ["💎💎", "🔔🔔", "🍇🍇", "🍊🍊", "🍋🍋", "🍒🍒"]
            lines.append("\n**🎪 Two of a Kind:**")
            for combo in pairs:
                if combo in self.payout_table:
                    lines.append(f"{combo} = {self.payout_table[combo]}x")

            return "\n".join(lines)
        
        async def on_timeout(self):
            # Disable all buttons when timeout occurs
            for item in self.children:
                item.disabled = True
            if self.message:
                embed = discord.Embed(
                    title="🎰 Slot Machine Expired",
                    description="This slot machine session has expired.",
                    color=0x808080
                )
                await self.message.edit(embed=embed, view=self)


    @app_commands.command(name="roulette", description="Play American Roulette! Bet on red, black, or green!")
    @app_commands.describe(
        bet="Amount of candy to bet",
        color="Choose a color: red, black, or green"
    )
    @app_commands.choices(color=[
        app_commands.Choice(name="🔴 Red", value="red"),
        app_commands.Choice(name="⚫ Black", value="black"),
        app_commands.Choice(name="🟢 Green", value="green")
    ])
    async def roulette(self, interaction: discord.Interaction, bet: int, color: str):
        user_id = interaction.user.id
        user_name = interaction.user.name

        if await self.check_user_bet(interaction, bet, user_id, user_name):
            return
        
        view = self.RouletteView(interaction.user, bet, color, self)
        embed = view.create_initial_embed()
        await interaction.response.send_message(embed=embed, view=view)
        
        # Store the message so we can edit on timeout
        view.message = await interaction.original_response()

    class RouletteView(discord.ui.View):
        def __init__(self, user: discord.User, bet: int, color: str, cog):
            super().__init__(timeout=45)
            self.user = user
            self.bet = bet
            self.color = color
            self.cog = cog
            self.message = None
            self.is_spinning = False
            self.total_winnings = 0
            self.total_losses = 0
            self.spin_count = 0
            self.win_count = 0
            self.loss_count = 0
            self.final_wheel_display = None  # Store the wheel position
            
        @discord.ui.button(label="🎰 SPIN!", style=discord.ButtonStyle.success, custom_id="spin_button")
        async def spin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            
            if self.is_spinning:
                await interaction.response.send_message("Wait for the current spin to finish!", ephemeral=True)
                return
            
            # Check if user still has enough candy for another bet
            async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    await cursor.execute('SELECT candy FROM Users WHERE id = ?', (self.user.id,))
                    result = await cursor.fetchone()
                    
            if result is None or result[0] < self.bet:
                await interaction.response.send_message("You don't have enough candy for another spin!", ephemeral=True)
                return
            
            await self.start_spinning(interaction)
        
        @discord.ui.button(label="💰 Cash Out", style=discord.ButtonStyle.danger, custom_id="cashout_button")
        async def cashout_button(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("This isn't your game!", ephemeral=True)
                return
            
            if self.is_spinning:
                await interaction.response.send_message("Wait for the spin to finish!", ephemeral=True)
                return
            
            # Disable all buttons
            for item in self.children:
                item.disabled = True
            
            embed = self.create_final_embed()
            await interaction.response.edit_message(embed=embed, view=self)
            self.stop()
        
        async def start_spinning(self, interaction: discord.Interaction):
            self.is_spinning = True
            self.spin_count += 1
            
            # Generate result first (0-37, where 37 represents 00)
            result_number = random.randint(0, 37)
            display_number = "00" if result_number == 37 else str(result_number)
            result_color = self.get_number_color(result_number)
            
            # Create spinning sequences
            spin_sequence = []
            for _ in range(11):
                spin_sequence.append(random.choice(["red", "black", "black", "red", "red", "black"]))
            
            # Insert some greens occasionally in random positions (but not the middle)
            green_pos = random.choice([0, 1, 2, 3, 4, 6, 7, 8, 9, 10])
            spin_sequence[green_pos] = "green"
            
            # Create final sequence with the actual result in the middle (position 5)
            final_sequence = spin_sequence.copy()
            final_sequence[5] = result_color
            
            # Animation - spin the wheel
            pointer = "⬇️"
            spins = 20  # Number of animation frames
            
            # First response to the interaction
            first_embed = discord.Embed(
                title="🎰 Roulette Wheel Spinning... 🎰",
                description="Starting the wheel...",
                color=0xFFD700
            )
            first_embed.set_author(
                name=f"{self.user.name}",
                icon_url=self.user.display_avatar.url
            )
            await interaction.response.edit_message(embed=first_embed, view=self)
            
            # Get the message for editing during animation
            message = await interaction.original_response()
            
            for i in range(spins):
                # Rotate the sequence during spin
                if i < spins - 5:  # Keep spinning fast
                    spin_sequence = spin_sequence[-1:] + spin_sequence[:-1]
                elif i == spins - 1:  # Last frame - use final sequence
                    spin_sequence = final_sequence
                else:  # Slowing down
                    # Gradually transition to final sequence
                    if i == spins - 3:
                        spin_sequence[5] = result_color  # Lock in the result
                
                # Convert colors to emoji squares
                wheel_display = ""
                for j, color in enumerate(spin_sequence):
                    if color == "red":
                        wheel_display += "🟥"
                    elif color == "black":
                        wheel_display += "⬛"
                    else:  # green
                        wheel_display += "🟩"
                    
                    if j < len(spin_sequence) - 1:
                        wheel_display += " "
                
                # Create the spinning embed with centered arrows
                embed = discord.Embed(
                    title="🎰 Roulette Wheel Spinning... 🎰",
                    description=f"```\n                {pointer}\n{wheel_display}\n                ⬆️\n```",
                    color=0xFFD700
                )
                embed.set_author(
                    name=f"{self.user.name}",
                    icon_url=self.user.display_avatar.url
                )
                embed.add_field(name="Your Bet", value=f"{self.bet} candy on {self.get_color_emoji(self.color)} {self.color.upper()}", inline=False)
                
                if i < spins - 8:
                    embed.set_footer(text="The wheel is spinning fast...")
                elif i < spins - 3:
                    embed.set_footer(text="The wheel is slowing down...")
                else:
                    embed.set_footer(text="Almost there...")
                
                # Edit the message directly, not through interaction
                await message.edit(embed=embed, view=self)
                
                # Variable speed - faster at start, slower at end
                if i < 10:
                    await asyncio.sleep(0.05)
                elif i < 15:
                    await asyncio.sleep(0.05)
                else:
                    await asyncio.sleep(0.05)
            
            # Store the final wheel position for display in result embeds
            self.final_wheel_display = ""
            for j, color in enumerate(final_sequence):
                if color == "red":
                    self.final_wheel_display += "🟥"
                elif color == "black":
                    self.final_wheel_display += "⬛"
                else:  # green
                    self.final_wheel_display += "🟩"
                
                if j < len(final_sequence) - 1:
                    self.final_wheel_display += " "
            
            # Check if won
            won = (self.color == result_color)
            
            if won:
                if self.color == "green":
                    # Green pays 35:1 in American roulette (for 0 or 00)
                    winnings = int(self.bet * 35)
                else:
                    # Red/Black pays 1:1
                    winnings = int(self.bet * 2)
                
                self.total_winnings += winnings
                self.win_count += 1
                await self.cog.user_update_candy(winnings, self.bet, self.user.id)
                embed = self.create_win_embed(display_number, result_color, winnings)
            else:
                self.total_losses += self.bet
                self.loss_count += 1
                await self.cog.user_update_candy(0, self.bet, self.user.id)
                embed = self.create_lose_embed(display_number, result_color)
            
            self.is_spinning = False
            await message.edit(embed=embed, view=self)
        
        def get_number_color(self, number):
            """Get the color of a number in American roulette"""
            if number in GREEN_NUMBERS:
                return "green"
            elif number in RED_NUMBERS:
                return "red"
            else:
                return "black"
        
        def get_color_emoji(self, color):
            """Get emoji for a color"""
            emojis = {
                "red": "🔴",
                "black": "⚫",
                "green": "🟢"
            }
            return emojis.get(color, "⚪")
        
        def create_initial_embed(self):
            # Create a default wheel display
            default_wheel = "🟥 ⬛ 🟥 ⬛ 🟥 🟩 ⬛ 🟥 ⬛ 🟥 ⬛"
            
            embed = discord.Embed(
                title="🎰 American Roulette 🎰",
                description=f"```\n                ⬇️\n{default_wheel}\n                ⬆️\n```\nPress **SPIN** to start the wheel!",
                color=self.get_embed_color(self.color)
            )
            embed.set_author(
                name=f"{self.user.name}",
                icon_url=self.user.display_avatar.url
            )
            embed.add_field(name="Your Bet", value=f"{self.bet} candy", inline=True)
            embed.add_field(name="Betting On", value=f"{self.get_color_emoji(self.color)} {self.color.upper()}", inline=True)
            
            if self.color == "green":
                embed.add_field(name="Payout", value="35:1", inline=True)
            else:
                embed.add_field(name="Payout", value="1:1", inline=True)
                
            embed.set_footer(text="45 second timeout • Keep spinning or cash out anytime!")
            return embed
        
        def create_win_embed(self, number, color, winnings):
            wheel_section = ""
            if self.final_wheel_display:
                wheel_section = f"```\n                ⬇️\n{self.final_wheel_display}\n                ⬆️\n```\n"
            
            embed = discord.Embed(
                title="🎉 WINNER! 🎉",
                description=f"{wheel_section}The ball landed on **{number}** {self.get_color_emoji(color)} {color.upper()}",
                color=0x2ECC71
            )
            embed.set_author(
                name=f"{self.user.name}",
                icon_url=self.user.display_avatar.url
            )
            embed.add_field(name="You Bet", value=f"{self.get_color_emoji(self.color)} {self.color.upper()}", inline=True)
            embed.add_field(name="Winnings", value=f"+{winnings} candy!", inline=True)
            embed.add_field(name="Net Profit", value=f"{self.total_winnings - self.total_losses} candy", inline=True)
            
            embed.add_field(name="Session Stats", value=f"Spins: {self.spin_count} | Wins: {self.win_count} | Losses: {self.loss_count}", inline=False)
            embed.set_footer(text="Spin again with the same bet or Cash Out!")
            return embed
        
        def create_lose_embed(self, number, color):
            wheel_section = ""
            if self.final_wheel_display:
                wheel_section = f"```\n                ⬇️\n{self.final_wheel_display}\n                ⬆️\n```\n"
            
            embed = discord.Embed(
                title="❌ You Lost",
                description=f"{wheel_section}The ball landed on **{number}** {self.get_color_emoji(color)} {color.upper()}",
                color=0xE74C3C
            )
            embed.set_author(
                name=f"{self.user.name}",
                icon_url=self.user.display_avatar.url
            )
            embed.add_field(name="You Bet", value=f"{self.get_color_emoji(self.color)} {self.color.upper()}", inline=True)
            embed.add_field(name="Lost", value=f"-{self.bet} candy", inline=True)
            embed.add_field(name="Net Profit", value=f"{self.total_winnings - self.total_losses} candy", inline=True)
            
            embed.add_field(name="Session Stats", value=f"Spins: {self.spin_count} | Wins: {self.win_count} | Losses: {self.loss_count}", inline=False)
            embed.set_footer(text="Try again with the same bet or Cash Out!")
            return embed
        
        def create_final_embed(self):
            net_profit = self.total_winnings - self.total_losses
            if net_profit > 0:
                title = "💰 Cashed Out with Profit! 💰"
                color = 0x2ECC71
                description = f"Congratulations! You made **{net_profit}** candy!"
            elif net_profit < 0:
                title = "💸 Cashed Out 💸"
                color = 0xE74C3C
                description = f"You lost **{abs(net_profit)}** candy. Better luck next time!"
            else:
                title = "💵 Cashed Out - Break Even 💵"
                color = 0x3498DB
                description = "You broke even!"
                
            embed = discord.Embed(
                title=title,
                description=description,
                color=color
            )
            embed.set_author(
                name=f"{self.user.name}",
                icon_url=self.user.display_avatar.url
            )
            
            # Win rate calculation
            win_rate = (self.win_count / self.spin_count * 100) if self.spin_count > 0 else 0
            
            embed.add_field(name="Total Spins", value=self.spin_count, inline=True)
            embed.add_field(name="Wins/Losses", value=f"{self.win_count}W / {self.loss_count}L", inline=True)
            embed.add_field(name="Win Rate", value=f"{win_rate:.1f}%", inline=True)
            embed.add_field(name="Total Won", value=f"{self.total_winnings} candy", inline=True)
            embed.add_field(name="Total Lost", value=f"{self.total_losses} candy", inline=True)
            embed.add_field(name="Net Profit", value=f"**{net_profit}** candy", inline=True)
            
            embed.set_footer(text="Thanks for playing American Roulette!")
            return embed
        
        def get_embed_color(self, color):
            """Get embed color based on bet color"""
            colors = {
                "red": 0xE74C3C,
                "black": 0x2C3E50,
                "green": 0x27AE60
            }
            return colors.get(color, 0x3498DB)
        
        async def on_timeout(self):
            # Disable all buttons when timeout occurs
            for item in self.children:
                item.disabled = True
            if self.message:
                embed = self.create_final_embed()
                await self.message.edit(embed=embed, view=self)
        
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
        try:
            async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:

                    await cursor.execute(f'UPDATE users SET candy = candy + ? WHERE id = ? RETURNING candy', ((winnings-bet), user_id))
                    new_candy_amount = await cursor.fetchone()
                    await connection.commit()
            
            logger.info(f"DB_UPDATE: User gambled {bet} candy.  id: {user_id} Net: {winnings-bet} total: {new_candy_amount[0]}")
            
        except Exception as e:
            logger.error(f"DB_UPDATE ERROR: Failed to update candy for user (ID: {user_id}). Error: {e}")
            raise
                
                
async def setup(bot: commands.Bot):
    await bot.add_cog(Gamble(bot))