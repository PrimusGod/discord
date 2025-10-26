import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class General(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"General cog loaded")
    
    @app_commands.command(name="help", description="Get help with Pokemon Bot commands")
    async def help(self, interaction: discord.Interaction):
        """Show help information"""
        embed = discord.Embed(
            title="🎮 Pokemon Bot Help",
            description="Welcome to the ultimate Pokemon Discord bot! Here's how to play:",
            color=discord.Color.blue()
        )
        
        # Basic Commands
        embed.add_field(
            name="🌟 Basic Commands",
            value="`;start` - Start your Pokemon journey\n"
                  "`;profile` - View your profile\n"
                  "`;stats` - Check your stats and balance\n"
                  "`;daily` - Claim your daily bonus\n"
                  "`;vote` - Get voting rewards",
            inline=False
        )
        
        # Pokemon Commands
        embed.add_field(
            name="🐾 Pokemon Commands",
            value="`;pokemon` - View your Pokemon\n"
                  "`;party` - Check your current party\n"
                  "`;dex <pokemon>` - View Pokemon info\n"
                  "`;hint` - Get a hint for current spawn\n"
                  "`;catch <name>` - Catch a Pokemon",
            inline=False
        )
        
        # Battle Commands
        embed.add_field(
            name="⚔️ Battle Commands",
            value="`;battle <@user>` - Challenge someone to battle\n"
                  "`;npcbattle` - Battle against NPC\n"
                  "`;moves` - View Pokemon moves\n"
                  "`;learn <move>` - Teach Pokemon a move",
            inline=False
        )
        
        # Economy Commands
        embed.add_field(
            name="💰 Economy Commands",
            value="`;shop` - View the item shop\n"
                  "`;buy <item>` - Buy an item\n"
                  "`;sell <item>` - Sell an item\n"
                  "`;market` - View Pokemon market\n"
                  "`;auction` - View active auctions",
            inline=False
        )
        
        # Trading Commands
        embed.add_field(
            name="🔄 Trading Commands",
            value="`;trade <@user>` - Start a trade\n"
                  "`;add <pokemon>` - Add Pokemon to trade\n"
                  "`;accept` - Accept trade offer\n"
                  "`;cancel` - Cancel trade",
            inline=False
        )
        
        # Mini-games
        embed.add_field(
            name="🎮 Mini-games",
            value="`;fish` - Go fishing\n"
                  "`;slots` - Play slot machine\n"
                  "`;missions` - View daily missions\n"
                  "`;tournament` - Join tournaments",
            inline=False
        )
        
        embed.set_footer(text="Pokemon spawn from normal chat conversations! No need for special commands.")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="start", description="Start your Pokemon journey")
    async def start(self, interaction: discord.Interaction):
        """Start the Pokemon journey"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        embed = discord.Embed(
            title="🌟 Welcome to Pokemon Bot!",
            description=f"Welcome, {interaction.user.display_name}! Your Pokemon journey begins now.",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Your Starter Kit",
            value=f"💰 {self.bot.config.daily_credits} credits\n"
                  f"🎒 Basic Pokeballs\n"
                  f"📱 Pokedex access\n"
                  f"⚔️ Battle ready",
            inline=False
        )
        
        embed.add_field(
            name="Getting Started",
            value="1. Chat in channels to make Pokemon spawn\n"
                  "2. Type the Pokemon's name to catch it\n"
                  "3. Use `;hint` for help with spawns\n"
                  "4. Build your team and battle others!",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="profile", description="View your Pokemon trainer profile")
    async def profile(self, interaction: discord.Interaction, user: discord.User = None):
        """View user profile"""
        target_user = user or interaction.user
        
        user_data = await self.bot.economy_system.get_user_balance(
            (await self.bot.db.get_or_create_user(str(target_user.id), target_user.display_name))['user_id']
        )
        
        if not user_data['success']:
            await interaction.response.send_message("User not found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🏆 {target_user.display_name}'s Profile",
            color=discord.Color.purple()
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        embed.add_field(
            name="💰 Economy",
            value=f"Credits: {user_data['credits']:,}\n"
                  f"Upvote Points: {user_data['upvote_points']}\n"
                  f"Inventory Value: {user_data['inventory_value']:,}",
            inline=True
        )
        
        embed.add_field(
            name="📊 Stats",
            value=f"Total EXP: {user_data['total_exp']:,}\n"
                  f"Pokemon Owned: {user_data['pokemon_count']}\n"
                  f"Fishing Level: {user_data['fishing_level']}",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Progress",
            value=f"Luck: {user_data['luck']}\n"
                  f"Fishing EXP: {user_data['fishing_exp']}",
            inline=True
        )
        
        embed.set_footer(text=f"Profile requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="stats", description="Check your stats and balance")
    async def stats(self, interaction: discord.Interaction):
        """Show user stats"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        balance = await self.bot.economy_system.get_user_balance(user['user_id'])
        
        embed = discord.Embed(
            title=f"📊 {interaction.user.display_name}'s Stats",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="💰 Wallet",
            value=f"Credits: **{balance['credits']:,}**\n"
                  f"Upvote Points: **{balance['upvote_points']}**",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Achievements",
            value=f"Total EXP: **{balance['total_exp']:,}**\n"
                  f"Pokemon Owned: **{balance['pokemon_count']}**",
            inline=True
        )
        
        embed.add_field(
            name="🎮 Skills",
            value=f"Fishing Level: **{balance['fishing_level']}**\n"
                  f"Luck: **{balance['luck']}**",
            inline=True
        )
        
        # Check daily bonus availability
        last_daily = user.get('last_daily')
        daily_available = True
        
        if last_daily:
            from datetime import datetime
            last_date = datetime.fromisoformat(last_daily).date()
            if last_date >= datetime.now().date():
                daily_available = False
        
        embed.set_footer(
            text=f"Daily bonus: {'Available' if daily_available else 'Claimed'}"
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="daily", description="Claim your daily bonus")
    async def daily(self, interaction: discord.Interaction):
        """Claim daily bonus"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        result = await self.bot.economy_system.give_daily_bonus(user['user_id'])
        
        if result['success']:
            embed = discord.Embed(
                title="🎁 Daily Bonus Claimed!",
                description=f"You received **{result['amount']}** credits!",
                color=discord.Color.gold()
            )
            embed.add_field(name="New Balance", value=f"**{result['new_balance']:,}** credits", inline=False)
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ Daily Bonus",
                description=result['error'],
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="vote", description="Get voting rewards")
    async def vote(self, interaction: discord.Interaction):
        """Show voting information and rewards"""
        embed = discord.Embed(
            title="🗳️ Vote for Pokemon Bot",
            description="Support the bot and earn rewards!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="Voting Rewards",
            value=f"💰 **{self.bot.config.daily_credits}** credits per vote\n"
                  f"⭐ **1** upvote point per vote\n"
                  f"🎁 Bonus rewards for streaks",
            inline=False
        )
        
        embed.add_field(
            name="Upvote Points",
            value=f"Convert **{self.bot.economy_system.upvote_point_value}** points for special rewards\n"
                  f"Use `;redeem` to spend your points",
            inline=False
        )
        
        embed.add_field(
            name="How to Vote",
            value="1. Visit our voting page\n"
                  "2. Vote on top.gg\n"
                  "3. Use `;claim` to get rewards",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="leaderboard", description="View the leaderboard")
    @app_commands.choices(category=[
        app_commands.Choice(name="Credits", value="credits"),
        app_commands.Choice(name="Experience", value="total_exp"),
        app_commands.Choice(name="Pokemon Count", value="pokemon_count"),
        app_commands.Choice(name="Upvote Points", value="upvote_points")
    ])
    async def leaderboard(self, interaction: discord.Interaction, category: str = "credits"):
        """Show leaderboard"""
        result = await self.bot.economy_system.get_leaderboard(category, 10)
        
        if not result['success']:
            await interaction.response.send_message("Error getting leaderboard!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🏆 {category.replace('_', ' ').title()} Leaderboard",
            color=discord.Color.gold()
        )
        
        for i, leader in enumerate(result['leaders'], 1):
            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][i-1]
            
            if category == "pokemon_count":
                value = leader['pokemon_count']
            else:
                value = leader[category]
            
            embed.add_field(
                name=f"{medal} {leader['username']}",
                value=f"{value:,}",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="hint", description="Get a hint for the current Pokemon spawn")
    async def hint(self, interaction: discord.Interaction):
        """Get a hint for current spawn"""
        success = await self.bot.spawn_system.handle_hint_request(interaction.channel, interaction.user)
        
        if not success:
            await interaction.response.send_message("No active Pokemon spawn in this channel!", ephemeral=True)
        else:
            await interaction.response.send_message("Hint sent!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(General(bot))