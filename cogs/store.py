import discord, random
from discord.ext import commands
from discord import app_commands
import sqlite3

class Store(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="add-store-item", description="Add an item to the store or add more quantity.")
    @app_commands.checks.has_permissions(administrator=True)
    async def removecandy(self, interaction: discord.Interaction , item_name: str, quantity: int, role: int):

        if role < 0 or role > 1:
            await interaction.response.send_message("Role should be 0 for not a role and 1 for a role")
            return

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()

        #Returns None if item does not exist in our DB
        cursor.execute('SELECT * FROM Store WHERE name = ?', (item_name,))
        result = cursor.fetchone()

        if result is None:
            cursor.execute('INSERT INTO Store (name, role, quantity) VALUES (?, ?, ?)',
                        (item_name, role, quantity))
        else:
            cursor.execute(f'UPDATE Store SET quantity = quantity + ? WHERE name = ?', (quantity, item_name))
            
        connection.commit()
        connection.close()

        await interaction.response.send_message(f"Item added successfully.")

    @app_commands.command(name="remove-store-item", description="Remove an item to the store or reduce the quantity (0 quantity removes it).")
    @app_commands.checks.has_permissions(administrator=True)
    async def removecandy(self, interaction: discord.Interaction , item_name: str, quantity: int):

        connection = sqlite3.connect('./database.db')
        cursor = connection.cursor()

        #Returns our items quantity
        cursor.execute('SELECT quantity FROM Store WHERE name = ?', (item_name,))
        result = cursor.fetchone()
        result = result[0]

        if result - quantity <= 0:
            cursor.execute(f'DELETE FROM Store WHERE name = ?', (item_name,))
        else:
            cursor.execute(f'UPDATE Store SET quantity = quantity - ? WHERE name = ?', (quantity, item_name))
            
        connection.commit()
        connection.close()

        await interaction.response.send_message(f"Item removed successfully.")       

async def setup(bot: commands.Bot):
    await bot.add_cog(Store(bot))