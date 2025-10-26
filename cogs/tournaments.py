import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class Tournaments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Tournaments cog loaded")
    
    @app_commands.command(name="tournament", description="Tournament management commands")
    @app_commands.choices(action=[
        app_commands.Choice(name="create", value="create"),
        app_commands.Choice(name="join", value="join"),
        app_commands.Choice(name="start", value="start"),
        app_commands.Choice(name="leaderboard", value="leaderboard"),
        app_commands.Choice(name="list", value="list")
    ])
    async def tournament(self, interaction: discord.Interaction, action: str, tournament_id: int = None, name: str = None, 
                        tournament_type: str = "single_elimination", max_participants: int = 16, entry_fee: int = 0):
        """Manage tournaments"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        if action == "create":
            if not name:
                await interaction.response.send_message("Please provide a tournament name!", ephemeral=True)
                return
            
            tournament_id = await self.bot.tournament_system.create_tournament(
                name, tournament_type, max_participants, entry_fee, user['user_id']
            )
            
            if tournament_id:
                embed = discord.Embed(
                    title="✅ Tournament Created!",
                    description=f"Tournament **{name}** has been created!",
                    color=discord.Color.green()
                )
                embed.add_field(name="Tournament ID", value=str(tournament_id), inline=True)
                embed.add_field(name="Type", value=tournament_type, inline=True)
                embed.add_field(name="Max Participants", value=str(max_participants), inline=True)
                embed.add_field(name="Entry Fee", value=f"{entry_fee} credits", inline=True)
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("Failed to create tournament!", ephemeral=True)
        
        elif action == "join":
            if not tournament_id:
                await interaction.response.send_message("Please provide a tournament ID!", ephemeral=True)
                return
            
            result = await self.bot.tournament_system.join_tournament(tournament_id, user['user_id'])
            
            if result['success']:
                embed = discord.Embed(
                    title="✅ Joined Tournament!",
                    description=f"You've successfully joined the tournament!",
                    color=discord.Color.green()
                )
                
                if result['entry_fee'] > 0:
                    embed.add_field(name="Entry Fee Paid", value=f"{result['entry_fee']} credits", inline=True)
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"Failed to join tournament: {result['error']}", ephemeral=True)
        
        elif action == "start":
            if not tournament_id:
                await interaction.response.send_message("Please provide a tournament ID!", ephemeral=True)
                return
            
            # Check if user is the creator
            tournament = await self.bot.db.fetch_one(
                "SELECT created_by FROM tournaments WHERE tournament_id = ?",
                (tournament_id,)
            )
            
            if not tournament or tournament['created_by'] != user['user_id']:
                await interaction.response.send_message("Only the tournament creator can start it!", ephemeral=True)
                return
            
            result = await self.bot.tournament_system.start_tournament(tournament_id)
            
            if result['success']:
                embed = discord.Embed(
                    title="🚀 Tournament Started!",
                    description=f"Tournament has begun with {result['participants']} participants!",
                    color=discord.Color.gold()
                )
                embed.add_field(name="Prize Pool", value=f"{result['prize_pool']} credits", inline=True)
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"Failed to start tournament: {result['error']}", ephemeral=True)
        
        elif action == "leaderboard":
            if not tournament_id:
                await interaction.response.send_message("Please provide a tournament ID!", ephemeral=True)
                return
            
            result = await self.bot.tournament_system.get_tournament_leaderboard(tournament_id)
            
            if result['success']:
                embed = discord.Embed(
                    title="🏆 Tournament Leaderboard",
                    color=discord.Color.gold()
                )
                
                for i, participant in enumerate(result['participants'], 1):
                    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"][i-1] if i <= 10 else "🏅"
                    
                    embed.add_field(
                        name=f"{medal} {participant['username']}",
                        value=f"Wins: {participant['wins']} | Losses: {participant['losses']}",
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(f"Failed to get leaderboard: {result['error']}", ephemeral=True)
        
        elif action == "list":
            tournaments = await self.bot.db.fetch_all(
                "SELECT * FROM tournaments WHERE status = 'registration' ORDER BY created_date DESC LIMIT 10"
            )
            
            if tournaments:
                embed = discord.Embed(
                    title="🎮 Active Tournaments",
                    description="Join these tournaments!",
                    color=discord.Color.blue()
                )
                
                for tournament in tournaments:
                    participant_count = await self.bot.db.fetch_val(
                        "SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = ?",
                        (tournament['tournament_id'],)
                    ) or 0
                    
                    embed.add_field(
                        name=f"#{tournament['tournament_id']} - {tournament['name']}",
                        value=f"Type: {tournament['type']}\n"
                              f"Participants: {participant_count}/{tournament['max_participants']}\n"
                              f"Entry Fee: {tournament['entry_fee']} credits\n"
                              f"Prize Pool: {tournament['prize_pool']} credits",
                        inline=False
                    )
                
                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message("No active tournaments found!", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Tournaments(bot))