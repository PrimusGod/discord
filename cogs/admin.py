import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Admin cog loaded")
    
    @app_commands.command(name="admin", description="Admin commands")
    @app_commands.default_permissions(administrator=True)
    async def admin(self, interaction: discord.Interaction, action: str, target: discord.User = None, amount: int = None):
        """Admin management commands"""
        # Check if user has admin permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You don't have permission to use admin commands!", ephemeral=True)
            return
        
        if action == "give_credits":
            if not target or amount is None or amount <= 0:
                await interaction.response.send_message("Please specify a user and positive amount!", ephemeral=True)
                return
            
            user = await self.bot.db.get_or_create_user(str(target.id), target.display_name)
            await self.bot.db.update_user_credits(user['user_id'], amount)
            
            embed = discord.Embed(
                title="✅ Credits Given",
                description=f"Gave **{amount}** credits to {target.display_name}!",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed)
        
        elif action == "remove_credits":
            if not target or amount is None or amount <= 0:
                await interaction.response.send_message("Please specify a user and positive amount!", ephemeral=True)
                return
            
            user = await self.bot.db.get_or_create_user(str(target.id), target.display_name)
            await self.bot.db.update_user_credits(user['user_id'], -amount)
            
            embed = discord.Embed(
                title="✅ Credits Removed",
                description=f"Removed **{amount}** credits from {target.display_name}!",
                color=discord.Color.orange()
            )
            
            await interaction.response.send_message(embed=embed)
        
        elif action == "reset_cooldown":
            if not target:
                await interaction.response.send_message("Please specify a user!", ephemeral=True)
                return
            
            # Reset fishing cooldown
            if hasattr(self.bot.fishing_system, 'user_cooldowns') and target.id in self.bot.fishing_system.user_cooldowns:
                del self.bot.fishing_system.user_cooldowns[target.id]
            
            embed = discord.Embed(
                title="✅ Cooldown Reset",
                description=f"Reset cooldowns for {target.display_name}!",
                color=discord.Color.blue()
            )
            
            await interaction.response.send_message(embed=embed)
        
        elif action == "spawn_pokemon":
            if not target:
                await interaction.response.send_message("Please specify a channel!", ephemeral=True)
                return
            
            # Create a Pokemon spawn in the user's current channel
            success = await self.bot.spawn_system.handle_spawn(interaction.channel)
            
            if success:
                embed = discord.Embed(
                    title="✅ Pokemon Spawned",
                    description="A wild Pokemon has appeared!",
                    color=discord.Color.green()
                )
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Failed to spawn Pokemon!", ephemeral=True)
        
        elif action == "bot_stats":
            # Get bot statistics
            total_users = await self.bot.db.fetch_val("SELECT COUNT(*) FROM users") or 0
            total_pokemon = await self.bot.db.fetch_val("SELECT COUNT(*) FROM player_pokemon") or 0
            active_battles = await self.bot.db.fetch_val("SELECT COUNT(*) FROM active_battles WHERE status = 'active'") or 0
            
            embed = discord.Embed(
                title="📊 Bot Statistics",
                color=discord.Color.purple()
            )
            
            embed.add_field(name="Total Users", value=str(total_users), inline=True)
            embed.add_field(name="Total Pokemon", value=str(total_pokemon), inline=True)
            embed.add_field(name="Active Battles", value=str(active_battles), inline=True)
            embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)
            
            await interaction.response.send_message(embed=embed)
        
        else:
            await interaction.response.send_message("Invalid admin action! Available: give_credits, remove_credits, reset_cooldown, spawn_pokemon, bot_stats", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Admin(bot))