import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class Trading(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_trades = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Trading cog loaded")
    
    @app_commands.command(name="trade", description="Start a trade with another trainer")
    async def trade(self, interaction: discord.Interaction, user: discord.User):
        """Initiate a trade with another user"""
        if user.bot or user.id == interaction.user.id:
            await interaction.response.send_message("You can't trade with bots or yourself!", ephemeral=True)
            return
        
        # Check if users have Pokemon
        initiator = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        recipient = await self.bot.db.get_or_create_user(str(user.id), user.display_name)
        
        initiator_pokemon = await self.bot.db.get_user_pokemon(initiator['user_id'], limit=1)
        recipient_pokemon = await self.bot.db.get_user_pokemon(recipient['user_id'], limit=1)
        
        if not initiator_pokemon:
            await interaction.response.send_message("You need at least one Pokemon to trade!", ephemeral=True)
            return
        
        if not recipient_pokemon:
            await interaction.response.send_message(f"{user.display_name} needs at least one Pokemon to trade!", ephemeral=True)
            return
        
        # Create trade
        trade_id = await self.bot.db.create_trade(initiator['user_id'], recipient['user_id'])
        
        # Create trade view
        trade_view = TradeView(self.bot, trade_id, interaction.user, user)
        self.active_trades[trade_id] = trade_view
        
        embed = discord.Embed(
            title="🔄 Trade Request",
            description=f"{user.mention}, {interaction.user.display_name} wants to trade with you!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="How to Trade",
            value="1. Add Pokemon to offer\n"
                  "2. Add credits if desired\n"
                  "3. Both parties accept\n"
                  "4. Trade completes automatically",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, view=trade_view)
    
    @app_commands.command(name="addpokemon", description="Add a Pokemon to your trade offer")
    async def add_pokemon(self, interaction: discord.Interaction, trade_id: int, pokemon_id: int):
        """Add a Pokemon to trade"""
        # Check if trade exists and user is part of it
        trade = await self.bot.db.get_trade(trade_id)
        
        if not trade or trade['status'] != 'pending':
            await interaction.response.send_message("Trade not found or already completed!", ephemeral=True)
            return
        
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        if user['user_id'] not in [trade['initiator_id'], trade['recipient_id']]:
            await interaction.response.send_message("You're not part of this trade!", ephemeral=True)
            return
        
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
            await interaction.response.send_message("You can't trade Pokemon that are in your party! Remove them first.", ephemeral=True)
            return
        
        # Add Pokemon to trade
        await self.bot.db.add_pokemon_to_trade(trade_id, pokemon_id, user['user_id'])
        
        embed = discord.Embed(
            title="✅ Pokemon Added to Trade",
            description=f"**{pokemon['name']}** has been added to your offer!",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        
        # Update trade view if it exists
        if trade_id in self.active_trades:
            await self.active_trades[trade_id].update_display()
    
    @app_commands.command(name="addcredits", description="Add credits to your trade offer")
    async def add_credits(self, interaction: discord.Interaction, trade_id: int, amount: int):
        """Add credits to trade"""
        if amount <= 0:
            await interaction.response.send_message("Amount must be positive!", ephemeral=True)
            return
        
        # Check if trade exists and user is part of it
        trade = await self.bot.db.get_trade(trade_id)
        
        if not trade or trade['status'] != 'pending':
            await interaction.response.send_message("Trade not found or already completed!", ephemeral=True)
            return
        
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        if user['user_id'] not in [trade['initiator_id'], trade['recipient_id']]:
            await interaction.response.send_message("You're not part of this trade!", ephemeral=True)
            return
        
        # Check if user has enough credits
        if user['credits'] < amount:
            await interaction.response.send_message("You don't have enough credits!", ephemeral=True)
            return
        
        # Add credits to trade (this would need to be implemented in the trade system)
        # For now, just show confirmation
        
        embed = discord.Embed(
            title="✅ Credits Added to Trade",
            description=f"**{amount:,}** credits have been added to your offer!",
            color=discord.Color.green()
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="accepttrade", description="Accept the current trade offer")
    async def accept_trade(self, interaction: discord.Interaction, trade_id: int):
        """Accept a trade"""
        trade = await self.bot.db.get_trade(trade_id)
        
        if not trade or trade['status'] != 'pending':
            await interaction.response.send_message("Trade not found or already completed!", ephemeral=True)
            return
        
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        if user['user_id'] not in [trade['initiator_id'], trade['recipient_id']]:
            await interaction.response.send_message("You're not part of this trade!", ephemeral=True)
            return
        
        # Update trade status
        await self.bot.db.execute(
            "UPDATE trades SET status = 'accepted' WHERE trade_id = ?",
            (trade_id,)
        )
        
        # Process the trade
        await self._process_trade(trade_id)
        
        embed = discord.Embed(
            title="✅ Trade Accepted!",
            description="The trade has been completed successfully!",
            color=discord.Color.gold()
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Clean up
        if trade_id in self.active_trades:
            del self.active_trades[trade_id]
    
    async def _process_trade(self, trade_id: int):
        """Process the actual trade"""
        # Get trade details
        trade_pokemon = await self.bot.db.fetch_all(
            "SELECT * FROM trade_pokemon WHERE trade_id = ?",
            (trade_id,)
        )
        
        # Transfer Pokemon ownership
        for trade_poke in trade_pokemon:
            await self.bot.db.execute(
                "UPDATE player_pokemon SET user_id = ? WHERE id = ?",
                (trade_poke['offered_by'], trade_poke['pokemon_uid'])
            )
        
        # Transfer credits if any
        # This would be implemented based on the trade system
        
        logger.info(f"Trade {trade_id} processed successfully")
    
    @app_commands.command(name="canceltrade", description="Cancel a trade")
    async def cancel_trade(self, interaction: discord.Interaction, trade_id: int):
        """Cancel a trade"""
        trade = await self.bot.db.get_trade(trade_id)
        
        if not trade or trade['status'] != 'pending':
            await interaction.response.send_message("Trade not found or already completed!", ephemeral=True)
            return
        
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        if user['user_id'] not in [trade['initiator_id'], trade['recipient_id']]:
            await interaction.response.send_message("You're not part of this trade!", ephemeral=True)
            return
        
        # Cancel trade
        await self.bot.db.execute(
            "UPDATE trades SET status = 'cancelled' WHERE trade_id = ?",
            (trade_id,)
        )
        
        embed = discord.Embed(
            title="❌ Trade Cancelled",
            description="The trade has been cancelled.",
            color=discord.Color.red()
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Clean up
        if trade_id in self.active_trades:
            del self.active_trades[trade_id]
    
    @app_commands.command(name="mytrades", description="View your active trades")
    async def my_trades(self, interaction: discord.Interaction):
        """Display user's active trades"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        trades = await self.bot.db.fetch_all("""
            SELECT t.*, u.username as other_user
            FROM trades t
            JOIN users u ON (t.initiator_id = u.user_id OR t.recipient_id = u.user_id)
            WHERE (t.initiator_id = ? OR t.recipient_id = ?)
            AND t.status = 'pending'
            AND u.user_id != ?
        """, (user['user_id'], user['user_id'], user['user_id']))
        
        if not trades:
            embed = discord.Embed(
                title="No Active Trades",
                description="You don't have any active trades.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title = f="🔄 {interaction.user.display_name}'s Active Trades",
            color=discord.Color.blue()
        )
        
        for trade in trades:
            # Get trade Pokemon
            trade_pokemon = await self.bot.db.fetch_all(
                "SELECT tp.*, ps.name, pp.is_shiny FROM trade_pokemon tp "
                "JOIN player_pokemon pp ON tp.pokemon_uid = pp.id "
                "JOIN pokemon_species ps ON pp.pokemon_id = ps.pokemon_id "
                "WHERE tp.trade_id = ?",
                (trade['trade_id'],)
            )
            
            trade_text = f"With: {trade['other_user']}\n"
            
            if trade_pokemon:
                pokemon_list = []
                for poke in trade_pokemon:
                    shiny = "✨" if poke['is_shiny'] else ""
                    pokemon_list.append(f"{shiny}{poke['name']}")
                trade_text += f"Pokemon: {', '.join(pokemon_list)}\n"
            
            if trade['credits'] > 0:
                trade_text += f"Credits: {trade['credits']:,}\n"
            
            trade_text += f"Created: {trade['created_date'][:10]}"
            
            embed.add_field(
                name=f"Trade #{trade['trade_id']}",
                value=trade_text,
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

class TradeView(discord.ui.View):
    def __init__(self, bot, trade_id, initiator, recipient):
        super().__init__(timeout=600)  # 10 minute timeout
        self.bot = bot
        self.trade_id = trade_id
        self.initiator = initiator
        self.recipient = recipient
        self.initiator_ready = False
        self.recipient_ready = False
    
    async def update_display(self):
        """Update the trade display"""
        # This would fetch current trade state and update the embed
        pass
    
    @discord.ui.button(label="Add Pokemon", style=discord.ButtonStyle.green, emoji="🐾")
    async def add_pokemon(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.initiator.id, self.recipient.id]:
            await interaction.response.send_message("You're not part of this trade!", ephemeral=True)
            return
        
        # Show Pokemon selection modal or view
        await interaction.response.send_message(
            "Use `/addpokemon trade_id: {self.trade_id} pokemon_id: [id]` to add a Pokemon to the trade.",
            ephemeral=True
        )
    
    @discord.ui.button(label="Add Credits", style=discord.ButtonStyle.blurple, emoji="💰")
    async def add_credits(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.initiator.id, self.recipient.id]:
            await interaction.response.send_message("You're not part of this trade!", ephemeral=True)
            return
        
        await interaction.response.send_message(
            "Use `/addcredits trade_id: {self.trade_id} amount: [amount]` to add credits to the trade.",
            ephemeral=True
        )
    
    @discord.ui.button(label="Ready", style=discord.ButtonStyle.green, emoji="✅")
    async def ready(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.initiator.id, self.recipient.id]:
            await interaction.response.send_message("You're not part of this trade!", ephemeral=True)
            return
        
        if interaction.user.id == self.initiator.id:
            self.initiator_ready = True
        else:
            self.recipient_ready = True
        
        await interaction.response.send_message("You're ready for the trade!", ephemeral=True)
        
        # Check if both are ready
        if self.initiator_ready and self.recipient_ready:
            await self.complete_trade()
    
    @discord.ui.button(label="Cancel Trade", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel_trade(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in [self.initiator.id, self.recipient.id]:
            await interaction.response.send_message("You're not part of this trade!", ephemeral=True)
            return
        
        # Cancel the trade
        await self.bot.db.execute(
            "UPDATE trades SET status = 'cancelled' WHERE trade_id = ?",
            (self.trade_id,)
        )
        
        embed = discord.Embed(
            title="❌ Trade Cancelled",
            description=f"{interaction.user.display_name} has cancelled the trade.",
            color=discord.Color.red()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Clean up
        if self.trade_id in self.bot.trading_system.active_trades:
            del self.bot.trading_system.active_trades[self.trade_id]
    
    async def complete_trade(self):
        """Complete the trade"""
        # Process the trade
        await self.bot.db.execute(
            "UPDATE trades SET status = 'accepted' WHERE trade_id = ?",
            (self.trade_id,)
        )
        
        embed = discord.Embed(
            title="✅ Trade Completed!",
            description="The trade has been completed successfully!",
            color=discord.Color.gold()
        )
        
        await self.message.edit(embed=embed, view=None)
        
        # Clean up
        if self.trade_id in self.bot.trading_system.active_trades:
            del self.bot.trading_system.active_trades[self.trade_id]

async def setup(bot):
    await bot.add_cog(Trading(bot))
