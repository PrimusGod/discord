from .views import FishingView
import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class Fishing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Fishing cog loaded")
    
    @app_commands.command(name="fish", description="Go fishing for water Pokemon")
    async def fish(self, interaction: discord.Interaction):
        """Start fishing mini-game"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        # Get fishing stats
        stats = await self.bot.fishing_system.get_fishing_stats(user['user_id'])
        
        if not stats['success']:
            await interaction.response.send_message("Error loading fishing data!", ephemeral=True)
            return
        
        # Create fishing view
        view = FishingView(self.bot, str(interaction.user.id))
        embed = await view.create_fishing_embed(stats)
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="fishstats", description="View your fishing statistics")
    async def fishstats(self, interaction: discord.Interaction):
        """Display fishing statistics"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        stats = await self.bot.fishing_system.get_fishing_stats(user['user_id'])
        
        if not stats['success']:
            await interaction.response.send_message("Error loading fishing stats!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"🎣 {interaction.user.display_name}'s Fishing Stats",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Level & Experience",
            value=f"Level: **{stats['fishing_level']}**\n"
                  f"Experience: **{stats['fishing_exp']}/{stats['fishing_level']*100}**\n"
                  f"To Next Level: **{stats['exp_to_next_level']}** EXP",
            inline=True
        )
        
        embed.add_field(
            name="🏆 Catches",
            value=f"Total Catches: **{stats['total_catches']}**\n"
                  f"Shiny Catches: **{stats['shiny_catches']}**\n"
                  f"Shiny Rate: **{(stats['shiny_catches']/max(stats['total_catches'], 1)*100):.2f}%**",
            inline=True
        )
        
        rod_type = await self.bot.fishing_system.get_user_rod(user['user_id'])
        rod = self.bot.fishing_system.rods[rod_type]
        
        embed.add_field(
            name="🎒 Current Rod",
            value=f"**{rod['name']}**\n"
                  f"Catch Rate: **{rod['catch_rate']*100}%**",
            inline=True
        )
        
        if stats['cooldown_remaining'] > 0:
            embed.add_field(
                name="⏰ Cooldown",
                value=f"**{stats['cooldown_remaining']}** seconds remaining",
                inline=False
            )
        else:
            embed.add_field(
                name="🎣 Ready to Fish!",
                value="Your fishing line is ready!",
                inline=False
            )
        
        # Get recent catches
        recent_catches = await self.bot.db.fetch_all("""
            SELECT fr.fish_time, ps.name, pp.is_shiny 
            FROM fishing_records fr
            JOIN player_pokemon pp ON fr.pokemon_id = pp.pokemon_id AND fr.user_id = pp.user_id
            JOIN pokemon_species ps ON pp.pokemon_id = ps.pokemon_id
            WHERE fr.user_id = ?
            ORDER BY fr.fish_time DESC
            LIMIT 5
        """, (user['user_id'],))
        
        if recent_catches:
            recent_text = ""
            for catch in recent_catches:
                shiny = "✨ " if catch['is_shiny'] else ""
                time_str = catch['fish_time'][:16] if len(catch['fish_time']) > 16 else catch['fish_time']
                recent_text += f"{shiny}**{catch['name']}** - {time_str}\n"
            
            embed.add_field(name="🐟 Recent Catches", value=recent_text, inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Fishing(bot))
