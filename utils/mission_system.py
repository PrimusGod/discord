import discord
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class MissionSystem:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.mission_types = {
            'catch': {
                'name': 'Pokemon Catcher',
                'description': 'Catch wild Pokemon',
                'base_requirement': 10,
                'reward_credits': 10000,
                'reward_items': []
            },
            'battle': {
                'name': 'Battle Master',
                'description': 'Win battles against other trainers',
                'base_requirement': 5,
                'reward_credits': 10000,
                'reward_items': []
            },
            'fish': {
                'name': 'Fishing Expert',
                'description': 'Catch Pokemon while fishing',
                'base_requirement': 5,
                'reward_credits': 10000,
                'reward_items': []
            },
            'evolve': {
                'name': 'Evolution Specialist',
                'description': 'Evolve your Pokemon',
                'base_requirement': 3,
                'reward_credits': 15000,
                'reward_items': []
            },
            'legendary': {
                'name': 'Legendary Hunter',
                'description': 'Catch legendary Pokemon',
                'base_requirement': 1,
                'reward_credits': 25000,
                'reward_items': []
            }
        }
    
    async def get_or_create_daily_mission(self, user_id: int) -> Dict[str, any]:
        """Get or create a daily mission for user"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Check for existing mission
            existing_mission = await self.db.fetch_one(
                "SELECT * FROM daily_missions WHERE user_id = ? AND mission_date = ?",
                (user_id, today)
            )
            
            if existing_mission:
                return {
                    'success': True,
                    'mission': existing_mission
                }
            
            # Create new mission
            mission_type = random.choice(list(self.mission_types.keys()))
            mission_config = self.mission_types[mission_type]
            
            # Calculate requirement based on user level
            user = await self.db.fetch_one(
                "SELECT total_exp FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            user_level = max(1, user['total_exp'] // 1000) if user else 1
            requirement = max(1, int(mission_config['base_requirement'] * (1 + user_level * 0.1)))
            
            mission_id = await self.db.insert_and_get_id("""
                INSERT INTO daily_missions (
                    user_id, mission_type, requirement, reward_credits, mission_date
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                user_id, mission_type, requirement, mission_config['reward_credits'], today
            ))
            
            new_mission = await self.db.fetch_one(
                "SELECT * FROM daily_missions WHERE mission_id = ?",
                (mission_id,)
            )
            
            return {
                'success': True,
                'mission': new_mission
            }
            
        except Exception as e:
            logger.error(f"Error creating daily mission: {e}")
            return {
                'success': False,
                'error': 'Database error'
            }
    
    async def update_progress(self, user_id: int, mission_type: str, amount: int = 1):
        """Update mission progress"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get current mission
            mission = await self.db.fetch_one(
                "SELECT * FROM daily_missions WHERE user_id = ? AND mission_type = ? AND mission_date = ?",
                (user_id, mission_type, today)
            )
            
            if not mission:
                return
            
            # Update progress
            new_progress = mission['progress'] + amount
            
            await self.db.execute(
                "UPDATE daily_missions SET progress = ? WHERE mission_id = ?",
                (new_progress, mission['mission_id'])
            )
            
            # Check if mission is completed
            if new_progress >= mission['requirement'] and not mission['completed']:
                await self.db.execute(
                    "UPDATE daily_missions SET completed = TRUE WHERE mission_id = ?",
                    (mission['mission_id'],)
                )
                
                # Send completion notification
                await self._send_completion_notification(user_id, mission)
            
        except Exception as e:
            logger.error(f"Error updating mission progress: {e}")
    
    async def _send_completion_notification(self, user_id: int, mission: Dict[str, any]):
        """Send mission completion notification"""
        try:
            # Get user Discord ID
            user = await self.db.fetch_one(
                "SELECT discord_id FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if not user:
                return
            
            # Find user in Discord
            discord_user = None
            for guild in self.bot.guilds:
                discord_user = guild.get_member(int(user['discord_id']))
                if discord_user:
                    break
            
            if not discord_user:
                return
            
            # Create completion embed
            embed = discord.Embed(
                title="🎉 Daily Mission Completed!",
                description=f"Congratulations! You've completed your daily mission!",
                color=discord.Color.gold()
            )
            
            mission_config = self.mission_types[mission['mission_type']]
            
            embed.add_field(
                name="Mission",
                value=f"**{mission_config['name']}**\n{mission_config['description']}",
                inline=False
            )
            
            embed.add_field(
                name="Progress",
                value=f"{mission['progress']}/{mission['requirement']}",
                inline=True
            )
            
            embed.add_field(
                name="Reward",
                value=f"{mission['reward_credits']} credits",
                inline=True
            )
            
            embed.set_footer(text="Use /claim to collect your reward!")
            
            try:
                await discord_user.send(embed=embed)
            except:
                pass  # User might have DMs disabled
                
        except Exception as e:
            logger.error(f"Error sending completion notification: {e}")
    
    async def claim_mission_reward(self, user_id: int) -> Dict[str, any]:
        """Claim completed mission reward"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get completed but unclaimed mission
            mission = await self.db.fetch_one(
                "SELECT * FROM daily_missions WHERE user_id = ? AND mission_date = ? AND completed = TRUE AND claimed = FALSE",
                (user_id, today)
            )
            
            if not mission:
                return {
                    'success': False,
                    'error': 'No completed missions to claim'
                }
            
            # Give reward
            await self.db.update_user_credits(user_id, mission['reward_credits'])
            
            # Mark as claimed
            await self.db.execute(
                "UPDATE daily_missions SET claimed = TRUE WHERE mission_id = ?",
                (mission['mission_id'],)
            )
            
            return {
                'success': True,
                'mission_type': mission['mission_type'],
                'reward_credits': mission['reward_credits']
            }
            
        except Exception as e:
            logger.error(f"Error claiming mission reward: {e}")
            return {
                'success': False,
                'error': 'Database error'
            }
    
    async def get_user_missions(self, user_id: int) -> Dict[str, any]:
        """Get all missions for a user"""
        try:
            today = datetime.now().strftime('%Y-%m-%d')
            
            missions = await self.db.fetch_all(
                "SELECT * FROM daily_missions WHERE user_id = ? AND mission_date = ?",
                (user_id, today)
            )
            
            if not missions:
                # Create a new mission
                result = await self.get_or_create_daily_mission(user_id)
                if result['success']:
                    missions = [result['mission']]
                else:
                    return {
                        'success': False,
                        'error': result.get('error', 'Unknown error')
                    }
            
            # Enhance mission data
            enhanced_missions = []
            for mission in missions:
                mission_config = self.mission_types[mission['mission_type']]
                enhanced_mission = {
                    **mission,
                    'name': mission_config['name'],
                    'description': mission_config['description']
                }
                enhanced_missions.append(enhanced_mission)
            
            return {
                'success': True,
                'missions': enhanced_missions
            }
            
        except Exception as e:
            logger.error(f"Error getting user missions: {e}")
            return {
                'success': False,
                'error': 'Database error'
            }
    
    async def get_mission_leaderboard(self, limit: int = 10) -> Dict[str, any]:
        """Get mission completion leaderboard"""
        try:
            leaderboard = await self.db.fetch_all("""
                SELECT u.username, COUNT(*) as missions_completed,
                       SUM(dm.reward_credits) as total_rewards
                FROM daily_missions dm
                JOIN users u ON dm.user_id = u.user_id
                WHERE dm.completed = TRUE AND dm.claimed = TRUE
                GROUP BY u.user_id
                ORDER BY missions_completed DESC
                LIMIT ?
            """, (limit,))
            
            return {
                'success': True,
                'leaderboard': leaderboard
            }
            
        except Exception as e:
            logger.error(f"Error getting mission leaderboard: {e}")
            return {
                'success': False,
                'error': 'Database error'
            }
    
    async def cleanup_old_missions(self):
        """Clean up old completed missions"""
        try:
            cutoff_date = datetime.now() - timedelta(days=7)
            
            await self.db.execute(
                "DELETE FROM daily_missions WHERE mission_date < ? AND claimed = TRUE",
                (cutoff_date.strftime('%Y-%m-%d'),)
            )
            
            logger.info("Cleaned up old missions")
            
        except Exception as e:
            logger.error(f"Error cleaning up old missions: {e}")

class MissionView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
    
    @discord.ui.button(label="Refresh", style=discord.ButtonStyle.green, emoji="🔄")
    async def refresh(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This isn't your mission board!", ephemeral=True)
            return
        
        # Refresh mission data
        missions = await self.bot.mission_system.get_user_missions(self.user_id)
        
        if missions['success']:
            embed = await self.create_mission_embed(missions['missions'])
            await interaction.response.edit_message(embed=embed)
        else:
            await interaction.response.send_message("Error refreshing missions!", ephemeral=True)
    
    @discord.ui.button(label="Claim Reward", style=discord.ButtonStyle.green, emoji="💰")
    async def claim_reward(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This isn't your mission board!", ephemeral=True)
            return
        
        result = await self.bot.mission_system.claim_mission_reward(self.user_id)
        
        if result['success']:
            embed = discord.Embed(
                title="🎉 Reward Claimed!",
                description=f"You received **{result['reward_credits']}** credits for completing your mission!",
                color=discord.Color.gold()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
            # Refresh the display
            missions = await self.bot.mission_system.get_user_missions(self.user_id)
            if missions['success']:
                new_embed = await self.create_mission_embed(missions['missions'])
                await interaction.message.edit(embed=new_embed)
        else:
            await interaction.response.send_message(f"Couldn't claim reward: {result['error']}", ephemeral=True)
    
    async def create_mission_embed(self, missions):
        """Create mission embed"""
        embed = discord.Embed(
            title="🎯 Daily Missions",
            description="Complete missions to earn rewards!",
            color=discord.Color.blue()
        )
        
        for mission in missions:
            status_emoji = "✅" if mission['completed'] else "⏳"
            
            mission_text = f"**{mission['name']}**\n"
            mission_text += f"*{mission['description']}*\n"
            mission_text += f"Progress: {mission['progress']}/{mission['requirement']}\n"
            mission_text += f"Reward: {mission['reward_credits']} credits\n"
            
            if mission['completed'] and not mission['claimed']:
                mission_text += "🎁 **Reward Ready to Claim!**\n"
            
            embed.add_field(
                name=f"{status_emoji} {mission['mission_type'].title()}",
                value=mission_text,
                inline=False
            )
        
        embed.set_footer(text="Missions reset daily at midnight UTC")
        
        return embed

async def setup(bot):
    bot.mission_system = MissionSystem(bot.db, bot.config)
    await bot.add_cog(Missions(bot))