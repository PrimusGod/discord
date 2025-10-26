import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class Missions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Missions cog loaded")
    
    @app_commands.command(name="missions", description="View your daily missions")
    async def missions(self, interaction: discord.Interaction):
        """Display daily missions"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        missions_data = await self.bot.mission_system.get_user_missions(user['user_id'])
        
        if not missions_data['success']:
            await interaction.response.send_message("Error loading missions!", ephemeral=True)
            return
        
        view = MissionView(self.bot, str(interaction.user.id))
        embed = await view.create_mission_embed(missions_data['missions'])
        
        await interaction.response.send_message(embed=embed, view=view)
    
    @app_commands.command(name="claim", description="Claim your completed mission rewards")
    async def claim(self, interaction: discord.Interaction):
        """Claim mission rewards"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        result = await self.bot.mission_system.claim_mission_reward(user['user_id'])
        
        if result['success']:
            embed = discord.Embed(
                title="🎉 Mission Reward Claimed!",
                description=f"You received **{result['reward_credits']}** credits for completing your mission!",
                color=discord.Color.gold()
            )
            
            await interaction.response.send_message(embed=embed)
        else:
            embed = discord.Embed(
                title="❌ No Rewards to Claim",
                description=result['error'],
                color=discord.Color.red()
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @app_commands.command(name="missionleaderboard", description="View mission completion leaderboard")
    async def mission_leaderboard(self, interaction: discord.Interaction):
        """Show mission completion leaderboard"""
        result = await self.bot.mission_system.get_mission_leaderboard(10)
        
        if not result['success']:
            await interaction.response.send_message("Error loading leaderboard!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="🏆 Mission Completion Leaderboard",
            description="Top mission completers!",
            color=discord.Color.gold()
        )
        
        for i, leader in enumerate(result['leaderboard'], 1):
            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][i-1]
            
            embed.add_field(
                name=f"{medal} {leader['username']}",
                value=f"Missions: {leader['missions_completed']}\n"
                      f"Total Rewards: {leader['total_rewards']:,} credits",
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Missions(bot))