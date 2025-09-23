import discord, asqlite, asyncio, json
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

ITEMS_PER_PAGE = 5
camp_upgrades = ["Outfit Update","Extended/Retracted Curfew","Increased Lighting","Generators","Trap/Mechanisms"]
interactions = ["murder","flower","hero","accusation","interrogation","makeasacrifice","skinnydip","wedgie"]

class Store(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="add-store-item", description="Add an item to the store or add more quantity.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(
        role="Either put the role name without the @ (Ex. Crackhead) or put None (Not a role)", 
        category="Select the item category"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="Snacks", value="Snacks"),
        app_commands.Choice(name="Supplies", value="Supplies"),
        app_commands.Choice(name="Weapons", value="Weapons"),
        app_commands.Choice(name="Camp Upgrades", value="Camp Upgrades"),
        app_commands.Choice(name="Interactions", value="Interactions")
    ])
    async def add_store_item(self, interaction: discord.Interaction, item_name: str, quantity: int, role: str, category: str, price: int):
        
        await interaction.response.defer(ephemeral=True)
        
        print(f"Searching for role: '{role}'")
        role_id = 0

        if role.lower() != "none":
            role_obj = None
            
            # Try exact match first (case insensitive)
            role_obj = discord.utils.find(lambda r: r.name.lower() == role.lower(), interaction.guild.roles)
            
            if role_obj is None:
                await interaction.followup.send("This role doesn't exist in the server. Please create the role before trying to add it to the store.", ephemeral=True)
                return
            role_id = role_obj.id

        if quantity <= 0:
            await interaction.followup.send("Quantity must be greater than zero.", ephemeral=True)
            return

        if price < 0:
            await interaction.followup.send("Price can not be negative.", ephemeral=True)
            return

        try:
            async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    # Returns None if item does not exist in our DB
                    await cursor.execute('SELECT * FROM Store WHERE name = ?', (item_name,))
                    result = await cursor.fetchone()

                    if result is None:
                        await cursor.execute('INSERT INTO Store (name, role, quantity, role_id, price, category) VALUES (?, ?, ?, ?, ?, ?)',
                                    (item_name, role, quantity, role_id, price, category))
                    else:
                        # Update quantity and category if item already exists
                        await cursor.execute('UPDATE Store SET quantity = quantity + ?, category = ? WHERE name = ?', (quantity, category, item_name))
                        
                    await connection.commit()
        except Exception as e:
            print(f"Database error: {e}")
            await interaction.followup.send("An error occurred while updating the database.", ephemeral=True)
            return

        await interaction.followup.send(f"Item added successfully to {category} category.", ephemeral=True)

    @app_commands.command(name="remove-store-item", description="Remove an item to the store or reduce the quantity (0 quantity removes it).")
    @app_commands.default_permissions(administrator=True)
    async def remove_store_item(self, interaction: discord.Interaction, item_name: str, quantity: int):
        
        await interaction.response.defer(ephemeral=True)

        try:
            async with asqlite.connect('./database.db') as connection:
                async with connection.cursor() as cursor:
                    # Returns None if item does not exist in our DB
                    await cursor.execute('SELECT * FROM Store WHERE name = ?', (item_name,))
                    result = await cursor.fetchone()

                    if result is None:
                        await interaction.followup.send("Item does not exist in our database.", ephemeral=True)
                        return

                    # Returns our items quantity
                    await cursor.execute('SELECT quantity FROM Store WHERE name = ?', (item_name,))
                    result = await cursor.fetchone()
                    current_quantity = result[0]

                    if int(current_quantity) - quantity <= 0:
                        await cursor.execute('DELETE FROM Store WHERE name = ?', (item_name,))
                    else:
                        await cursor.execute('UPDATE Store SET quantity = quantity - ? WHERE name = ?', (quantity, item_name))
                        
                    await connection.commit()
        except Exception as e:
            print(f"Database error: {e}")
            await interaction.followup.send("An error occurred while updating the database.", ephemeral=True)
            return

        await interaction.followup.send(f"Item removed successfully.", ephemeral=True)
    
    @app_commands.command(name="purchase", description="Purchase an item from the store")
    @app_commands.describe(item_name="Case sensitive, enter the exact item name")
    async def purchase(self, interaction: discord.Interaction, item_name: str, quantity: int):

        if quantity == 0:
            await interaction.response.send_message(f"This brokie {interaction.user.name} just tried to buy 0 quantity of an item.", ephemeral = False)
            return


        user_id = interaction.user.id
        user_name = interaction.user.name

        utils_cog = self.bot.get_cog("Utils")

        await utils_cog.check_user_exists(user_id, user_name)

        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:

                #Returns None if item does not exist in our DB
                await cursor.execute('SELECT * FROM Store WHERE name = ?', (item_name,))
                result = await cursor.fetchone()

                if result is None:
                    await interaction.response.send_message("This item doesn't exist.", ephemeral = False)
                    
                    return
                
                price = int(result[4])
                stock = int(result[2])
                role_id = int(result[3])
                

                #Check if user trying to purchase more than 1 of a role or user already has the role
                if (quantity > 1 and role_id > 0) or interaction.user.get_role(role_id) != None: 
                    await interaction.response.send_message("You can only buy a max of 1 for a role!", ephemeral = True)
                    
                    return

                await cursor.execute('SELECT candy FROM Users WHERE id = ?', (user_id,))
                user_candy_amount = await cursor.fetchone()
                user_candy_amount = user_candy_amount[0]

                if user_candy_amount < price*quantity:
                    await interaction.response.send_message(f"{interaction.user.mention} is a brokie and can't afford his item 🤡!", ephemeral = False)
                    
                    return
                
                if stock <= 0:
                    await interaction.response.send_message("This item is out of stock!", ephemeral = True)
                    
                    return
                
                if stock < quantity:
                    await interaction.response.send_message("You are trying to buy more than the total stock!", ephemeral = True)
                    
                    return
                
                if role_id > 0: #If the item we are trying to buy is a role
                    
                    await interaction.user.add_roles(interaction.guild.get_role(role_id))
                    await cursor.execute(f'UPDATE users SET candy = candy - ? WHERE id = ? RETURNING candy', (price, user_id))
                    new_candy_amount = await cursor.fetchone()
                    new_candy_amount = new_candy_amount[0]
                    await cursor.execute(f'UPDATE store SET quantity = quantity - 1 WHERE name = ?', (item_name, ))
                    
                    await cursor.execute("SELECT roles FROM Users WHERE id = ?", (user_id,))
                    row = await cursor.fetchone()
                    roles = json.loads(row[0]) if row[0] else []
                    if item_name not in roles:
                        roles.append(item_name)
                        await cursor.execute(
                            "UPDATE Users SET roles = ? WHERE id = ?",
                            (json.dumps(roles), user_id)
                        )
                        
                    await connection.commit()
                    await interaction.response.send_message("You have bought and gotten your role!", ephemeral=False)
                    
                else:
                    
                    await cursor.execute(f'UPDATE users SET candy = candy - ? WHERE id = ? RETURNING candy', (price*quantity, user_id))
                    new_candy_amount = await cursor.fetchone()
                    new_candy_amount = new_candy_amount[0]
                    await cursor.execute(f'UPDATE store SET quantity = quantity - ? WHERE name = ?', (quantity, item_name))
                    
                    await connection.commit()
                    await interaction.response.send_message("You have bought and gotten your item!", ephemeral=False)
                    
                    if item_name in camp_upgrades:
                        channel = discord.utils.get(interaction.guild.channels, name="shop-logs")
                        await channel.send(f"{user_name} has bought camp upgrade {item_name}")
                    item_name_parse = item_name.replace(" ", "").lower()
                    if item_name_parse in interactions:
                        await cursor.execute(f'UPDATE users SET {item_name_parse}_count = {item_name_parse}_count + ? WHERE id = ?', (quantity, user_id))
                        
                    
                logger.info(f"DB_UPDATE: User: {user_name} id: {user_id} bought {quantity} {item_name} for {price} for total {price*quantity}. New total {new_candy_amount}.")


    async def get_total_items(self, category=None):
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                if category and category != "All":
                    await cursor.execute("SELECT COUNT(*) FROM Store WHERE category = ?", (category,))
                else:
                    await cursor.execute("SELECT COUNT(*) FROM Store")
                total_items = await cursor.fetchone()
                total_items = total_items[0]
                await connection.commit()
                
        return total_items

    async def get_page_items(self, page, category=None):
        offset = page * ITEMS_PER_PAGE
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                if category and category != "All":
                    await cursor.execute("SELECT name, quantity, price FROM Store WHERE category = ? LIMIT ? OFFSET ?", 
                                       (category, ITEMS_PER_PAGE, offset))
                else:
                    await cursor.execute("SELECT name, quantity, price FROM Store LIMIT ? OFFSET ?", 
                                       (ITEMS_PER_PAGE, offset))
                data = await cursor.fetchall()
                await connection.commit()
                
        return data

    @app_commands.command(name="store", description="Browse the item store")
    async def store(self, interaction: discord.Interaction):
        view = self.StoreView(self, interaction.user)
        await view.initialize()
        embed = await view.generate_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    class CategorySelect(discord.ui.Select):
        def __init__(self, parent_view):
            self.parent_view = parent_view
            options = [
                discord.SelectOption(label="All", description="Show all items", emoji="📦"),
                discord.SelectOption(label="Snacks", description="Food and consumables", emoji="🍭"),
                discord.SelectOption(label="Supplies", description="Essential camp supplies", emoji="🛠️"),
                discord.SelectOption(label="Weapons", description="Defensive equipment", emoji="⚔️"),
                discord.SelectOption(label="Camp Upgrades", description="Improve your camp", emoji="🏕️"),
                discord.SelectOption(label="Interactions", description="Purchase a command use", emoji="🏕️")
            ]
            super().__init__(placeholder="Select a category...", min_values=1, max_values=1, options=options)
        
        async def callback(self, interaction: discord.Interaction):
            if interaction.user.id != self.parent_view.user.id:
                await interaction.response.send_message("Use your own store buster.", ephemeral=True)
                return
            
            # Update the selected category
            self.parent_view.selected_category = self.values[0]
            self.parent_view.page = 0  # Reset to first page when changing category
            
            # Re-initialize with new category
            await self.parent_view.initialize()
            
            # Update the embed and view
            embed = await self.parent_view.generate_embed()
            await interaction.response.edit_message(embed=embed, view=self.parent_view)

    class StoreView(discord.ui.View):
        def __init__(self, cog, user, page=0):
            super().__init__(timeout=180)
            self.cog = cog
            self.user = user
            self.page = page
            self.total_items = 0
            self.max_page = 0
            self.selected_category = "All"
            
            # Add the category dropdown
            self.category_select = Store.CategorySelect(self)
            self.add_item(self.category_select)
        
        async def initialize(self):
            self.total_items = await self.cog.get_total_items(self.selected_category)
            self.max_page = (self.total_items - 1) // ITEMS_PER_PAGE if self.total_items > 0 else 0
            self.update_buttons()

        async def generate_embed(self):
            items = await self.cog.get_page_items(self.page, self.selected_category)
            header = "Name                   Quantity    Price\n"
            store_lines = []
            
            if not items:
                store_lines.append("No items available in this category.")
            else:
                for name, quantity, price in items:
                    trimmed_name = (name[:20] + "...") if len(name) > 20 else name
                    padded_name = f"{trimmed_name:<23}" 
                    store_lines.append(f"{padded_name} {str(quantity):<10} {str(price)}")
                    store_lines.append("")
            
            category_text = f" - {self.selected_category}" if self.selected_category != "All" else ""
            embed = discord.Embed(
                title=f"🍬 Aches Candy Store{category_text} 🍬\n",
                description="\u200b\n" + "```"+"\n".join([header] + store_lines)+"```"+"\u200b\n",
                color=discord.Color.purple()
            )
            embed.set_author(name=f"{self.user.name}'s Store", icon_url=self.user.display_avatar.url)
            embed.set_footer(text=f"Page {self.page + 1} of {self.max_page + 1} | Category: {self.selected_category}")
            embed.set_thumbnail(url="https://images.halloweencostumes.com.au/products/12290/1-1/light-up-traditional-pumpkin-upd.jpg")
            return embed

        def update_buttons(self):
            self.previous.disabled = self.page <= 0
            self.next.disabled = self.page >= self.max_page

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary, row=1)
        async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("Use your own store buster.", ephemeral=True)
                return

            if self.page > 0:
                self.page -= 1
                self.update_buttons()
                await interaction.response.edit_message(embed=await self.generate_embed(), view=self)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary, row=1)
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("Use your own store buster.", ephemeral=True)
                return

            if self.page < self.max_page:
                self.page += 1
                self.update_buttons()
                await interaction.response.edit_message(embed=await self.generate_embed(), view=self)    

async def setup(bot: commands.Bot):
    await bot.add_cog(Store(bot))