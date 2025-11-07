import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class Market(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Market cog loaded")
    
    @app_commands.command(name="shop", description="View the item shop")
    async def shop(self, interaction: discord.Interaction, category: str = None):
        """Display the item shop"""
        shop_data = await self.bot.economy_system.get_shop_items()
        
        if not shop_data['success']:
            await interaction.response.send_message("Error loading shop!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏪 Pokemon Bot Shop",
            description="Buy items to enhance your Pokemon journey!",
            color=discord.Color.blue()
        )
        
        categories = shop_data['items']
        
        if category and category in categories:
            # Show specific category
            items = categories[category]
            item_text = ""
            
            for item in items[:10]:  # Limit to 10 items
                item_text += f"**{item['name']}** - {item['cost']} credits\n"
                if item['description']:
                    item_text += f"*{item['description']}*\n"
                item_text += "\n"
            
            if len(items) > 10:
                item_text += f"... and {len(items) - 10} more items"
            
            embed.add_field(name=f"{category.title()} Items", value=item_text, inline=False)
        else:
            # Show all categories
            for cat, items in categories.items():
                if items:
                    item_names = [item['name'] for item in items[:5]]
                    embed.add_field(
                        name=f"{cat.title()} ({len(items)} items)",
                        value=", ".join(item_names) + ("..." if len(items) > 5 else ""),
                        inline=True
                    )
        
        embed.set_footer(text="Use /buy <item> to purchase items")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="buy", description="Buy an item from the shop")
    async def buy(self, interaction: discord.Interaction, item_name: str, quantity: int = 1):
        """Buy an item"""
        if quantity <= 0:
            await interaction.response.send_message("Quantity must be positive!", ephemeral=True)
            return
        
        # Find item by name
        item = await self.bot.db.fetch_one(
            "SELECT * FROM items WHERE LOWER(name) = LOWER(?)",
            (item_name,)
        )
        
        if not item:
            await interaction.response.send_message(f"Item '{item_name}' not found!", ephemeral=True)
            return
        
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        result = await self.bot.economy_system.buy_item(user['user_id'], item['item_id'], quantity)
        
        if result['success']:
            embed = discord.Embed(
                title="✅ Purchase Successful!",
                description=f"You bought **{result['quantity']}x {result['item_name']}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Total Cost", value=f"{result['total_cost']} credits", inline=True)
            embed.add_field(name="New Balance", value=f"{result['new_balance']} credits", inline=True)
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Purchase failed: {result['error']}", ephemeral=True)
    
    @app_commands.command(name="sell", description="Sell an item to the shop")
    async def sell(self, interaction: discord.Interaction, item_name: str, quantity: int = 1):
        """Sell an item"""
        if quantity <= 0:
            await interaction.response.send_message("Quantity must be positive!", ephemeral=True)
            return
        
        # Find item by name
        item = await self.bot.db.fetch_one(
            "SELECT * FROM items WHERE LOWER(name) = LOWER(?)",
            (item_name,)
        )
        
        if not item:
            await interaction.response.send_message(f"Item '{item_name}' not found!", ephemeral=True)
            return
        
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        result = await self.bot.economy_system.sell_item(user['user_id'], item['item_id'], quantity)
        
        if result['success']:
            embed = discord.Embed(
                title="✅ Sale Successful!",
                description=f"You sold **{result['quantity']}x {result['item_name']}**!",
                color=discord.Color.green()
            )
            embed.add_field(name="Total Earnings", value=f"{result['sell_price']} credits", inline=True)
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Sale failed: {result['error']}", ephemeral=True)
    
    @app_commands.command(name="inventory", description="View your inventory")
    async def inventory(self, interaction: discord.Interaction):
        """Display user's inventory"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        inventory = await self.bot.db.get_user_inventory(user['user_id'])
        
        if not inventory:
            embed = discord.Embed(
                title="Empty Inventory",
                description="You don't have any items! Buy some from the shop.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title = f="🎒 {interaction.user.display_name}'s Inventory",
            color=discord.Color.blue()
        )
        
        # Group items by category
        items_by_category = {}
        total_value = 0
        
        for item in inventory:
            category = item['category']
            if category not in items_by_category:
                items_by_category[category] = []
            items_by_category[category].append(item)
            total_value += item['cost'] * item['quantity']
        
        for category, items in items_by_category.items():
            category_text = ""
            for item in items[:5]:  # Limit to 5 items per category
                category_text += f"**{item['name']}**: {item['quantity']}x\n"
                if item['description']:
                    category_text += f"*{item['description']}*\n"
            
            if len(items) > 5:
                category_text += f"... and {len(items) - 5} more\n"
            
            embed.add_field(name=f"{category.title()} ({len(items)} items)", value=category_text, inline=True)
        
        embed.add_field(name="💰 Total Value", value=f"{total_value} credits", inline=False)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="market", description="View the Pokemon marketplace")
    async def market(self, interaction: discord.Interaction, page: int = 1, search: str = None):
        """Display Pokemon market listings"""
        per_page = 10
        offset = (page - 1) * per_page
        
        listings = await self.bot.db.get_market_listings(per_page, offset)
        
        if not listings:
            embed = discord.Embed(
                title="No Listings Found",
                description="There are no Pokemon currently for sale.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"🏪 Pokemon Market - Page {page}",
            description="Buy Pokemon from other trainers!",
            color=discord.Color.blue()
        )
        
        for i, listing in enumerate(listings, 1):
            pokemon_name = listing['name']
            price = listing['price']
            seller = listing['seller_name']
            
            # Pokemon details
            is_shiny = "✨" if listing['is_shiny'] else ""
            level = listing['level']
            
            listing_text = f"**{is_shiny}{pokemon_name}** (Lv.{level})\n"
            listing_text += f"Price: **{price:,}** credits\n"
            listing_text += f"Seller: {seller}\n"
            listing_text += f"Listed: {listing['listed_date'][:10]}\n"
            
            embed.add_field(
                name=f"#{offset + i} - {pokemon_name}",
                value=listing_text,
                inline=False
            )
        
        embed.set_footer(text="Use /buy <listing_id> to purchase a Pokemon")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="sellpokemon", description="List a Pokemon for sale on the market")
    async def sellpokemon(self, interaction: discord.Interaction, pokemon_id: int, price: int):
        """List a Pokemon for sale"""
        if price <= 0:
            await interaction.response.send_message("Price must be positive!", ephemeral=True)
            return
        
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        # Verify Pokemon belongs to user
        pokemon = await self.bot.db.fetch_one(
            "SELECT pp.*, ps.name FROM player_pokemon pp "
            "JOIN pokemon_species ps ON pp.pokemon_id = ps.pokemon_id "
            "WHERE pp.id = ? AND pp.user_id = ?",
            (pokemon_id, user['user_id'])
        )
        
        if not pokemon:
            await interaction.response.send_message("Pokemon not found or doesn't belong to you!", ephemeral=True)
            return
        
        # Check if Pokemon is in party
        party = await self.bot.db.get_user_party(user['user_id'])
        party_pokemon_ids = [p['id'] for p in party]
        
        if pokemon_id in party_pokemon_ids:
            await interaction.response.send_message("You can't sell Pokemon that are in your party! Remove them first.", ephemeral=True)
            return
        
        # Create market listing
        listing_id = await self.bot.db.create_market_listing(user['user_id'], pokemon_id, price)
        
        embed = discord.Embed(
            title="✅ Pokemon Listed for Sale",
            description=f"Your **{pokemon['name']}** has been listed for **{price:,}** credits!",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Listing ID", value=f"#{listing_id}", inline=True)
        embed.add_field(name="Price", value=f"{price:,} credits", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="buypokemon", description="Buy a Pokemon from the market")
    async def buypokemon(self, interaction: discord.Interaction, listing_id: int):
        """Buy a Pokemon from the market"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        # Get listing details
        listing = await self.bot.db.fetch_one(
            "SELECT * FROM market_listings WHERE listing_id = ? AND is_sold = FALSE",
            (listing_id,)
        )
        
        if not listing:
            await interaction.response.send_message("Listing not found or already sold!", ephemeral=True)
            return
        
        # Check if user has enough credits
        if user['credits'] < listing['price']:
            await interaction.response.send_message("You don't have enough credits!", ephemeral=True)
            return
        
        # Check if user is trying to buy their own Pokemon
        if listing['seller_id'] == user['user_id']:
            await interaction.response.send_message("You can't buy your own Pokemon!", ephemeral=True)
            return
        
        # Process purchase
        await self.bot.db.execute(
            "UPDATE market_listings SET is_sold = TRUE, buyer_id = ?, sale_date = datetime('now') WHERE listing_id = ?",
            (user['user_id'], listing_id)
        )
        
        # Transfer credits (with tax)
        tax = int(listing['price'] * self.bot.config.market_tax)
        seller_amount = listing['price'] - tax
        
        await self.bot.db.update_user_credits(user['user_id'], -listing['price'])
        await self.bot.db.update_user_credits(listing['seller_id'], seller_amount)
        
        # Transfer Pokemon ownership
        await self.bot.db.execute(
            "UPDATE player_pokemon SET user_id = ? WHERE id = ?",
            (user['user_id'], listing['pokemon_uid'])
        )
        
        # Get Pokemon details
        pokemon = await self.bot.db.fetch_one(
            "SELECT ps.name FROM player_pokemon pp "
            "JOIN pokemon_species ps ON pp.pokemon_id = ps.pokemon_id "
            "WHERE pp.id = ?",
            (listing['pokemon_uid'],)
        )
        
        embed = discord.Embed(
            title="✅ Pokemon Purchased!",
            description=f"You bought **{pokemon['name']}** for **{listing['price']:,}** credits!",
            color=discord.Color.green()
        )
        
        embed.add_field(name="Tax Paid", value=f"{tax} credits", inline=True)
        embed.add_field(name="Seller Received", value=f"{seller_amount} credits", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="auction", description="View active auctions")
    async def auction(self, interaction: discord.Interaction):
        """Display active auctions"""
        embed = discord.Embed(
            title="🔨 Pokemon Auctions",
            description="Bid on rare Pokemon in live auctions!",
            color=discord.Color.gold()
        )
        
        # This would show active auctions
        embed.add_field(
            name="No Active Auctions",
            value="Check back later for new auctions!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="redeem", description="Use your upvote points for special rewards")
    async def redeem(self, interaction: discord.Interaction, points: int):
        """Convert upvote points to redeems"""
        if points <= 0:
            await interaction.response.send_message("Points must be positive!", ephemeral=True)
            return
        
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        result = await self.bot.economy_system.convert_upvote_points(user['user_id'], points)
        
        if result['success']:
            embed = discord.Embed(
                title="✅ Points Converted!",
                description=f"You converted **{result['points_used']}** upvote points into **{result['redeems_earned']}** redeems!",
                color=discord.Color.green()
            )
            embed.add_field(name="Remaining Points", value=f"{result['remaining_points']}", inline=True)
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"Conversion failed: {result['error']}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Market(bot))
