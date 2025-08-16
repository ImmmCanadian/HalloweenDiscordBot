import discord, asqlite, asyncio, json
from discord.ext import commands
from discord import app_commands
import sqlite3

ITEMS_PER_PAGE = 5

class Store(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="add-store-item", description="Add an item to the store or add more quantity.")
    @app_commands.default_permissions(administrator=True)
    @app_commands.describe(role="Either put the role name without the @ (Ex. Crackhead) or put None (Not a role)", pet = "Yes if pet No if not.")
    async def add_store_item(self, interaction: discord.Interaction, item_name: str, quantity: int, role: str, pet: str, price: int):
        # Defer the response immediately to prevent timeout
        await interaction.response.defer(ephemeral=True)
        
        print(f"Searching for role: '{role}'")
        role_id = 0

        if role.lower() != "none":
            # More flexible role searching
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
                        await cursor.execute('INSERT INTO Store (name, role, pet, quantity, role_id, price) VALUES (?, ?, ?, ?, ?, ?)',
                                    (item_name, role, pet, quantity, role_id, price))
                    else:
                        await cursor.execute('UPDATE Store SET quantity = quantity + ? WHERE name = ?', (quantity, item_name))
                        
                    await connection.commit()
        except Exception as e:
            print(f"Database error: {e}")
            await interaction.followup.send("An error occurred while updating the database.", ephemeral=True)
            return

        await interaction.followup.send(f"Item added successfully.", ephemeral=True)

    @app_commands.command(name="remove-store-item", description="Remove an item to the store or reduce the quantity (0 quantity removes it).")
    @app_commands.default_permissions(administrator=True)
    async def remove_store_item(self, interaction: discord.Interaction, item_name: str, quantity: int):
        # Defer the response immediately to prevent timeout
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
                pet = result[5]

                #Check if user trying to purchase more than 1 of a role or user already has the role
                if (quantity > 1 and role_id > 0) or interaction.user.get_role(role_id) != None: 
                    await interaction.response.send_message("You can only buy a max of 1 for a role!", ephemeral = True)
                    
                    return

                await cursor.execute('SELECT candy FROM Users WHERE id = ?', (user_id,))
                user_candy_amount = await cursor.fetchone()
                user_candy_amount = user_candy_amount[0]

                if user_candy_amount < price:
                    await interaction.response.send_message(f"{interaction.user.mention} is a brokie and can't afford his item 🤡!", ephemeral = False)
                    
                    return
                
                if stock <= 0:
                    await interaction.response.send_message("This item is out of stock!", ephemeral = True)
                    
                    return
                
                if role_id > 0: #If the item we are trying to buy is a role
                    
                    await interaction.user.add_roles(interaction.guild.get_role(role_id))
                    await cursor.execute(f'UPDATE users SET candy = candy - ? WHERE id = ?', (price, user_id))
                    await cursor.execute(f'UPDATE store SET quantity = quantity - 1 WHERE name = ?', (item_name, ))
                    
                    if pet.lower() == "yes":  
                        await cursor.execute("SELECT pets FROM Users WHERE id = ?", (user_id,))
                        row = await cursor.fetchone()
                        pets = json.loads(row[0]) if row[0] else []
                        pets.append(item_name)
                        await cursor.execute(
                            "UPDATE Users SET pets = ? WHERE id = ?",
                            (json.dumps(pets), user_id)
                        )
                    else:
                        await cursor.execute("SELECT roles FROM Users WHERE id = ?", (user_id,))
                        row = await cursor.fetchone()
                        roles = json.loads(row[0]) if row[0] else []
                        roles.append(item_name)
                        await cursor.execute(
                            "UPDATE Users SET roles = ? WHERE id = ?",
                            (json.dumps(roles), user_id)
                        )
                    
                    await connection.commit()
                    
                    await interaction.response.send_message("You have bought and gotten your item!", ephemeral=False)


    async def get_total_items(self):
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT COUNT(*) FROM Store")
                total_items = await cursor.fetchone()
                total_items = total_items[0]
                await connection.commit()
                
        return total_items

    async def get_page_items(self, page):
        offset = page * ITEMS_PER_PAGE
        async with asqlite.connect('./database.db') as connection:
            async with connection.cursor() as cursor:
                await cursor.execute("SELECT name, quantity, price FROM Store LIMIT ? OFFSET ?", (ITEMS_PER_PAGE, offset))
                data = await cursor.fetchall()
                await connection.commit()
                
        return data

    @app_commands.command(name="store", description="Browse the item store")
    async def store(self, interaction: discord.Interaction):
        view = self.StoreView(self, interaction.user)
        await view.initialize()
        embed = await view.generate_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    class StoreView(discord.ui.View):
        def __init__(self, cog, user, page=0):
            super().__init__(timeout=180)
            self.cog = cog
            self.user = user
            self.page = page
            self.total_items = 0
            self.max_page = 0
        
        async def initialize(self):
            self.total_items = await self.cog.get_total_items()
            self.max_page = (self.total_items - 1) // ITEMS_PER_PAGE if self.total_items > 0 else 0
            self.update_buttons()

        async def generate_embed(self):
            items = await self.cog.get_page_items(self.page)
            header = "Name           Quantity    Price\n"
            store_lines = []
            for name, quantity, price in items:
                trimmed_name = (name[:14 - 3] + "...") if len(name) > 12 else name
                padded_name = f"{trimmed_name:<15}" 
                store_lines.append(f"{padded_name} {str(quantity):<10} {str(price)}")
                store_lines.append("")
            embed = discord.Embed(
                title=f"🍬 Aches Candy Store 🍬\n",
                description="\u200b\n" + "```"+"\n".join([header] + store_lines)+"```"+"\u200b\n",
                color=discord.Color.purple()
            )
            embed.set_author(name=f"{self.user.name}'s Store", icon_url=self.user.display_avatar.url)
            embed.set_footer(text=f"Page {self.page + 1}")
            embed.set_thumbnail(url="https://images.halloweencostumes.com.au/products/12290/1-1/light-up-traditional-pumpkin-upd.jpg")
            return embed

        def update_buttons(self):
            self.previous.disabled = self.page <= 0
            self.next.disabled = self.page >= self.max_page

        @discord.ui.button(label="Previous", style=discord.ButtonStyle.secondary)
        async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("Use your own store buster.", ephemeral=True)
                return

            if self.page > 0: #Technically dont need this since should be disabled
                self.page -= 1
                self.update_buttons()
                await interaction.response.edit_message(embed=await self.generate_embed(), view=self)

        @discord.ui.button(label="Next", style=discord.ButtonStyle.secondary)
        async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != self.user.id:
                await interaction.response.send_message("Use your own store buster.", ephemeral=True)
                return

            if self.page < self.max_page: #Technically dont need this since should be disabled
                self.page += 1
                self.update_buttons()
                await interaction.response.edit_message(embed=await self.generate_embed(), view=self)    

async def setup(bot: commands.Bot):
    await bot.add_cog(Store(bot))