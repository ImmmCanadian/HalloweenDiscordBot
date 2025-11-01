import discord, random, asyncio, asqlite
from discord.ext import commands
from discord import app_commands, File
from discord.ui import Button, View
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import aiohttp
from io import BytesIO
import logging

logger = logging.getLogger(__name__)


class Raffle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name="create-raffle", description="Create a raffle.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(
        item_name="The name of the raffle prize", 
        winner_count="How many winners",
        ticket_price="Price per ticket",
        time = "Enter the date format DD/MM/YYYY which it should end." 
    )
    async def createraffle(self, interaction: discord.Interaction, item_name: str, winner_count: int, ticket_price: int, time: str):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        if winner_count <= 0 or ticket_price <= 0:
            await interaction.response.send_message("Values must be positive!", ephemeral=True)
            return
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                # Check if raffle already exists
                await cursor.execute('SELECT item FROM Raffle WHERE item = ?', (item_name,))
                if await cursor.fetchone():
                    await interaction.response.send_message(f"A raffle for '{item_name}' already exists!", ephemeral=True)
                    return
                
                # Create the raffle
                await cursor.execute(
                    'INSERT INTO Raffle (item, winner_count, ticket_cost, time) VALUES (?, ?, ?, ?)',
                    (item_name, winner_count, ticket_price, time)
                )
                await connection.commit()
        
        embed = discord.Embed(
            title="🎟️ New Raffle Created!",
            description=f"**Prize:** {item_name}\n**Winners:** {winner_count}\n**Ticket Price:** {ticket_price} candy",
            color=0xFFD700
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy-raffle-tickets", description="Buy raffle tickets!")
    @app_commands.describe(
        item_name="The name of the raffle prize, case sensitive"
    )
    async def buytickets(self, interaction: discord.Interaction, item_name: str, amount: int):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        if amount <= 0:
            await interaction.response.send_message("Amount must be positive!", ephemeral=True)
            return
        
        user_id = interaction.user.id
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                # Get raffle info
                await cursor.execute('SELECT ticket_cost, been_raffled FROM Raffle WHERE item = ?', (item_name,))
                raffle = await cursor.fetchone()
                
                if not raffle:
                    await interaction.response.send_message(f"No raffle exists for '{item_name}'!", ephemeral=True)
                    return
                
                if raffle[1]:  # been_raffled is not NULL
                    await interaction.response.send_message("This raffle has already ended!", ephemeral=True)
                    return
                
                cost = amount * raffle[0]
                
                # Check user balance
                await cursor.execute('SELECT candy FROM Users WHERE id = ?', (user_id,))
                result = await cursor.fetchone()
                
                if not result or result[0] < cost:
                    await interaction.response.send_message(f"You need {cost} candy!", ephemeral=True)
                    return
                
                # Deduct candy
                await cursor.execute('UPDATE Users SET candy = candy - ? WHERE id = ?', (cost, user_id))
                
                # Add or update tickets in RaffleTickets table
                await cursor.execute('''
                    INSERT INTO RaffleTickets (user_id, raffle_item, ticket_count) 
                    VALUES (?, ?, ?)
                    ON CONFLICT(user_id, raffle_item) 
                    DO UPDATE SET ticket_count = ticket_count + ?
                ''', (user_id, item_name, amount, amount))
                
                # Get total tickets for this user
                await cursor.execute(
                    'SELECT ticket_count FROM RaffleTickets WHERE user_id = ? AND raffle_item = ?',
                    (user_id, item_name)
                )
                total_tickets = (await cursor.fetchone())[0]
                
                await connection.commit()
                logger.info(f"DB_UPDATE: Added {amount} tickets to id: {user_id} for raffle {item_name}")
        
        embed = discord.Embed(
            title="🎟️ Tickets Purchased!",
            description=f"Bought **{amount}** tickets for **{item_name}**\nCost: {cost} candy",
            color=0x2ECC71
        )
        embed.add_field(name="Your Total Tickets", value=total_tickets, inline=True)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="draw-raffle", description="Draw raffle winners!")
    @app_commands.checks.has_permissions(administrator=True)
    async def drawraffle(self, interaction: discord.Interaction, item_name: str):
        from cogs.utils import Utils
        if Utils.is_pst_blocked():
            await interaction.response.send_message("Commands are now blocked after the event cutoff.", ephemeral=True)
            return
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                # Get raffle info
                await cursor.execute(
                    'SELECT winner_count, been_raffled FROM Raffle WHERE item = ?', 
                    (item_name,)
                )
                raffle = await cursor.fetchone()
                
                if not raffle:
                    await interaction.response.send_message(f"No raffle for '{item_name}'!", ephemeral=True)
                    return
                
                if raffle[1]:  # Already raffled
                    await interaction.response.send_message("This raffle was already drawn!", ephemeral=True)
                    return
                
                winner_count = raffle[0]
                
                # Get all participants and their tickets
                await cursor.execute(
                    'SELECT user_id, ticket_count FROM RaffleTickets WHERE raffle_item = ? AND ticket_count > 0',
                    (item_name,)
                )
                participants = await cursor.fetchall()
                
                if not participants:
                    await interaction.response.send_message("No one bought tickets!", ephemeral=True)
                    return
                
                # Store original tickets for display
                original_tickets = dict(participants)
                total_tickets = sum(tickets for _, tickets in participants)
                
                # Convert to mutable lists for drawing
                user_ids = [user_id for user_id, _ in participants]
                ticket_counts = [tickets for _, tickets in participants]
                
                # Draw winners one by one
                winner_list = []  # List of (user_id, win_number) tuples
                
                for win_number in range(1, winner_count + 1):
                    if not user_ids or sum(ticket_counts) == 0:
                        break  # No more tickets
                    
                    # Draw one winner
                    winner_id = random.choices(user_ids, weights=ticket_counts, k=1)[0]
                    winner_list.append((winner_id, win_number))
                    
                    logger.info(f"RAFFLE: Winner Drawn id: {winner_id}")
                    
                    # Reduce winner's tickets by 1
                    winner_idx = user_ids.index(winner_id)
                    ticket_counts[winner_idx] -= 1
                    
                    if ticket_counts[winner_idx] == 0:
                        user_ids.pop(winner_idx)
                        ticket_counts.pop(winner_idx)
                
                # Mark raffle as complete
                await cursor.execute(
                    'UPDATE Raffle SET been_raffled = ? WHERE item = ?',
                    (datetime.now().isoformat(), item_name)
                )
                
                # Clean up tickets
                #await cursor.execute('DELETE FROM RaffleTickets WHERE raffle_item = ?', (item_name,))
                
                await connection.commit()
                
                logger.info(f"DB_UPDATE: {interaction.user.name} initiated the raffle draw for {item_name}")
        
        
        winner_image = await self.create_winner_image(
            item_name, 
            winner_list, 
            original_tickets, 
            total_tickets
        )

        file = discord.File(winner_image, filename=f"raffle_winners_{item_name}.png")

        await interaction.response.send_message(file=file)
    
    async def download_avatars(self, win_counts: dict):
        # Fetch avatar bytes for each winner so the result image can include profile pictures
        avatars = {}
        
        async with aiohttp.ClientSession() as session:
            for user_id in win_counts.keys():
                user = self.bot.get_user(user_id)
                if not user:
                    avatars[user_id] = None
                    continue
                
                try:
                    async with session.get(str(user.display_avatar.url)) as response:
                        avatar_data = await response.read()
                        avatars[user_id] = avatar_data
                except Exception as e:
                    logger.error(f"Failed to download avatar for user {user_id}: {e}")
                    avatars[user_id] = None
        
        return avatars
    
    def create_winner_image_sync(self, item_name: str, winner_list: list, original_tickets: dict, 
                                  total_tickets: int, avatars: dict, user_info: dict):
        """Synchronous function for PIL operations - to be run in thread"""
        
        # Count wins per user
        win_counts = {}
        for winner_id, _ in winner_list:
            win_counts[winner_id] = win_counts.get(winner_id, 0) + 1
        
        # Image settings
        width = 600
        row_height = 80
        header_height = 100
        padding = 20
        avatar_size = 60
        
        # Calculate image height
        height = header_height + (len(win_counts) * row_height) + (padding * 2)
        
        # Create image with green background
        img = Image.new('RGB', (width, height), color='#2ECC71')
        draw = ImageDraw.Draw(img)
        
        # Try to load fonts (fallback to default if not available)
        try:
            title_font = ImageFont.truetype("arial.ttf", 36)
            name_font = ImageFont.truetype("arial.ttf", 24)
            info_font = ImageFont.truetype("arial.ttf", 18)
        except:
            title_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            info_font = ImageFont.load_default()
        
        # Draw title
        title = f" {item_name} Winners "
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        draw.text(((width - title_width) // 2, 20), title, fill='white', font=title_font)
        
        # Draw subtitle
        subtitle = f"Total Tickets Sold: {total_tickets}"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=info_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        draw.text(((width - subtitle_width) // 2, 65), subtitle, fill='#ECEFF1', font=info_font)
        
        # Draw winners
        y_position = header_height + padding
        
        for idx, (user_id, wins) in enumerate(win_counts.items()):
            # Get user info from pre-fetched data
            username = user_info.get(user_id, {}).get('name', f'User {user_id}')
            avatar_data = avatars.get(user_id)
            
            tickets = original_tickets[user_id]
            win_chance = (tickets / total_tickets) * 100
            
            # Draw background bar for each winner (alternating shades)
            bar_color = '#27AE60' if idx % 2 == 0 else '#229954'
            draw.rectangle(
                [(padding, y_position - 5), (width - padding, y_position + avatar_size + 5)],
                fill=bar_color,
                outline='#1E8449',
                width=2
            )
            
            # Process and paste avatar
            if avatar_data:
                try:
                    avatar = Image.open(BytesIO(avatar_data))
                    
                    # Resize avatar
                    avatar = avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
                    
                    # Make avatar circular
                    mask = Image.new('L', (avatar_size, avatar_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    
                    # Create circular avatar
                    output = Image.new('RGBA', (avatar_size, avatar_size), (0, 0, 0, 0))
                    output.paste(avatar, (0, 0))
                    output.putalpha(mask)
                    
                    # Paste on main image
                    img.paste(output, (padding + 10, y_position), output)
                except Exception as e:
                    logger.error(f"Failed to process avatar for user {user_id}: {e}")
                    # Draw placeholder
                    draw.ellipse(
                        [(padding + 10, y_position), 
                        (padding + 10 + avatar_size, y_position + avatar_size)],
                        fill='#95A5A6',
                        outline='white',
                        width=2
                    )
            else:
                # Draw placeholder circle if no avatar data
                draw.ellipse(
                    [(padding + 10, y_position), 
                    (padding + 10 + avatar_size, y_position + avatar_size)],
                    fill='#95A5A6',
                    outline='white',
                    width=2
                )
            
            # Draw user name
            name_x = padding + avatar_size + 25
            name_y = y_position + 5
            draw.text((name_x, name_y), username, fill='white', font=name_font)
            
            # Draw win info
            if wins > 1:
                win_text = f"Won {wins} times! • {tickets} tickets ({win_chance:.1f}%)"
            else:
                win_text = f"Winner! • {tickets} tickets ({win_chance:.1f}%)"
            
            draw.text((name_x, name_y + 30), win_text, fill='#E8F5E9', font=info_font)
            
            y_position += row_height
        
        # Save to BytesIO
        img_buffer = BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        
        return img_buffer
    
    async def create_winner_image(self, item_name: str, winner_list: list, original_tickets: dict, total_tickets: int):
        """Async wrapper that downloads avatars then runs PIL in thread"""
        
        # Count wins per user for avatar downloading
        win_counts = {}
        for winner_id, _ in winner_list:
            win_counts[winner_id] = win_counts.get(winner_id, 0) + 1
        
        # Prepare user info dictionary
        user_info = {}
        for user_id in win_counts.keys():
            user = self.bot.get_user(user_id)
            if user:
                user_info[user_id] = {
                    'name': user.name,
                    'display_name': user.display_name
                }
        
        # Download all avatars asynchronously
        avatars = await self.download_avatars(win_counts)
        
        # Run PIL operations in thread to avoid blocking
        img_buffer = await asyncio.to_thread(
            self.create_winner_image_sync,
            item_name,
            winner_list,
            original_tickets,
            total_tickets,
            avatars,
            user_info
        )
        
        return img_buffer
    
    @app_commands.command(name="raffles", description="Display all active raffles")
    async def showraffles(self, interaction: discord.Interaction):
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                # Get all active raffles
                await cursor.execute('''
                    SELECT 
                        r.item,
                        r.ticket_cost,
                        r.winner_count,
                        r.time,
                        COALESCE(SUM(rt.ticket_count), 0) as total_tickets
                    FROM Raffle r
                    LEFT JOIN RaffleTickets rt ON r.item = rt.raffle_item
                    WHERE r.been_raffled IS NULL
                    GROUP BY r.item, r.ticket_cost, r.winner_count
                    ORDER BY total_tickets DESC
                ''')
                
                raffles = await cursor.fetchall()
        
        if not raffles:
            embed = discord.Embed(
                title="📋 Active Raffles",
                description="No active raffles at the moment!",
                color=0x95A5A6
            )
            await interaction.response.send_message(embed=embed)
            return
        
        # Create embed
        embed = discord.Embed(
            title="🎟️ Active Raffles 🎟️",
            description="All currently running raffles:",
            color=0x3498DB,
            timestamp=datetime.now()
        )
        
        # Add each raffle as a field
        for item, ticket_cost, winner_count, time, total_tickets in raffles:
            
            # Create field value with details
            field_value = (
                f"💰 **Ticket Price:** {ticket_cost} candy\n"
                f"🎫 **Tickets Sold:** {total_tickets}\n"
                f"🏆 **Winners:** {winner_count}\n"
                f"   **Finish date:** {time}\n"
            )
            
            # Add emoji based on popularity
            if total_tickets > 100:
                emoji = "🔥"
            elif total_tickets > 50:
                emoji = "⭐"
            elif total_tickets > 0:
                emoji = "✨"
            else:
                emoji = "🆕"
            
            embed.add_field(
                name=f"{emoji}   {item}",
                value=field_value,
                inline=False
            )
        
        # Add footer with total stats
        total_pot = 0
        total_tickets_sold = 0

        for item, ticket_cost, winner_count, time, total_tickets in raffles:
            total_pot += total_tickets * ticket_cost
            total_tickets_sold += total_tickets
        
        embed.set_footer(
            text=f"Total Tickets Sold: {total_tickets_sold} | Total Pot Value: {total_pot} candy",
            icon_url=interaction.guild.icon.url if interaction.guild.icon else None
        )
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="my-tickets", description="Check your raffle tickets")
    async def mytickets(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                # Get all active raffles and user's tickets
                await cursor.execute('''
                    SELECT r.item, rt.ticket_count, r.ticket_cost
                    FROM Raffle r
                    LEFT JOIN RaffleTickets rt ON r.item = rt.raffle_item AND rt.user_id = ?
                    WHERE r.been_raffled IS NULL
                ''', (user_id,))
                
                raffles = await cursor.fetchall()
        
        if not raffles:
            await interaction.response.send_message("No active raffles!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🎟️ Your Raffle Tickets",
            color=0x3498DB
        )
        
        for item, tickets, price in raffles:
            tickets = tickets or 0  # Handle NULL as 0
            embed.add_field(
                name=item,
                value=f"Tickets: {tickets}\nPrice: {price} candy/ticket",
                inline=True
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Raffle(bot))