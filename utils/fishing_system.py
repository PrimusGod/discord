import discord
import random
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class FishingSystem:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        
        # Fishing rods and their effectiveness
        self.rods = {
            'old_rod': {
                'name': 'Old Rod',
                'cost': 0,
                'catch_rate': 0.3,
                'rarity_weights': {'common': 0.8, 'uncommon': 0.2, 'rare': 0.0}
            },
            'good_rod': {
                'name': 'Good Rod',
                'cost': 3500,
                'catch_rate': 0.5,
                'rarity_weights': {'common': 0.6, 'uncommon': 0.3, 'rare': 0.1}
            },
            'super_rod': {
                'name': 'Super Rod',
                'cost': 7500,
                'catch_rate': 0.7,
                'rarity_weights': {'common': 0.4, 'uncommon': 0.4, 'rare': 0.2}
            }
        }
        
        # Water Pokemon by rarity (simplified - would be populated from database)
        self.water_pokemon = {
            'common': [7, 54, 60, 90, 98, 116, 118, 129, 158, 183],  # Squirtle, Psyduck, etc.
            'uncommon': [8, 55, 61, 73, 99, 117, 119, 130, 184, 211],  # Wartortle, Golduck, etc.
            'rare': [9, 65, 73, 134, 148, 149, 230, 245, 249, 382]  # Blastoise, Gyarados, etc.
        }
        
        # Fishing cooldowns
        self.user_cooldowns = {}
    
    async def can_fish(self, user_id: int) -> bool:
        """Check if user can fish (cooldown check)"""
        if user_id in self.user_cooldowns:
            if datetime.now() < self.user_cooldowns[user_id]:
                return False
        return True
    
    async def get_fishing_cooldown_remaining(self, user_id: int) -> int:
        """Get remaining cooldown time in seconds"""
        if user_id in self.user_cooldowns:
            remaining = (self.user_cooldowns[user_id] - datetime.now()).total_seconds()
            return max(0, int(remaining))
        return 0
    
    async def get_user_rod(self, user_id: int) -> str:
        """Get the best fishing rod a user owns"""
        # Check inventory for fishing rods
        inventory = await self.db.get_user_inventory(user_id)
        
        best_rod = 'old_rod'  # Default rod
        
        for item in inventory:
            if item['name'] in ['Good Rod', 'Super Rod']:
                if item['name'] == 'Super Rod':
                    return 'super_rod'
                elif item['name'] == 'Good Rod' and best_rod == 'old_rod':
                    best_rod = 'good_rod'
        
        return best_rod
    
    async def go_fishing(self, user_id: int, channel: discord.TextChannel) -> Dict[str, any]:
        """Handle fishing attempt"""
        try:
            # Check cooldown
            if not await self.can_fish(user_id):
                remaining = await self.get_fishing_cooldown_remaining(user_id)
                return {
                    'success': False,
                    'error': f'Fishing on cooldown! Wait {remaining} seconds.',
                    'cooldown_remaining': remaining
                }
            
            # Get user's fishing rod
            rod_type = await self.get_user_rod(user_id)
            rod = self.rods[rod_type]
            
            # Check if fishing is successful
            if random.random() > rod['catch_rate']:
                # Set cooldown for failed attempt (shorter)
                self.user_cooldowns[user_id] = datetime.now() + timedelta(minutes=1)
                
                return {
                    'success': False,
                    'error': 'Nothing bit! Try again later.',
                    'cooldown_remaining': 60
                }
            
            # Determine Pokemon rarity
            rarity_roll = random.random()
            cumulative = 0
            selected_rarity = 'common'
            
            for rarity, weight in rod['rarity_weights'].items():
                cumulative += weight
                if rarity_roll < cumulative:
                    selected_rarity = rarity
                    break
            
            # Select random Pokemon from rarity tier
            if selected_rarity in self.water_pokemon and self.water_pokemon[selected_rarity]:
                pokemon_id = random.choice(self.water_pokemon[selected_rarity])
            else:
                pokemon_id = random.choice(self.water_pokemon['common'])
            
            # Check if shiny (very rare for fishing)
            is_shiny = random.random() < (self.config.shiny_rate * 0.5)
            
            # Add Pokemon to user's collection
            pokemon_uid = await self.db.add_pokemon_to_user(
                user_id, pokemon_id, level=random.randint(5, 15), is_shiny=is_shiny,
                caught_location='Fishing'
            )
            
            # Add fishing record
            await self.db.add_fishing_record(user_id, pokemon_id, rod['name'])
            
            # Update fishing experience
            await self.db.execute(
                "UPDATE users SET fishing_exp = fishing_exp + ? WHERE user_id = ?",
                (10, user_id)
            )
            
            # Check for fishing level up
            user = await self.db.fetch_one(
                "SELECT fishing_exp, fishing_level FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            current_exp = user['fishing_exp']
            current_level = user['fishing_level']
            exp_needed = current_level * 100
            
            leveled_up = False
            if current_exp >= exp_needed:
                new_level = current_level + 1
                await self.db.execute(
                    "UPDATE users SET fishing_level = ?, fishing_exp = ? WHERE user_id = ?",
                    (new_level, current_exp - exp_needed, user_id)
                )
                leveled_up = True
            
            # Set cooldown
            self.user_cooldowns[user_id] = datetime.now() + timedelta(seconds=self.config.fish_cooldown)
            
            # Get Pokemon details
            pokemon = await self.db.fetch_one(
                "SELECT name FROM pokemon_species WHERE pokemon_id = ?",
                (pokemon_id,)
            )
            
            return {
                'success': True,
                'pokemon_name': pokemon['name'],
                'pokemon_id': pokemon_id,
                'is_shiny': is_shiny,
                'rarity': selected_rarity,
                'level': 10,  # Average level
                'fishing_exp_gained': 10,
                'leveled_up': leveled_up,
                'new_fishing_level': new_level if leveled_up else current_level,
                'rod_used': rod['name']
            }
            
        except Exception as e:
            logger.error(f"Error in fishing system: {e}")
            return {
                'success': False,
                'error': 'An error occurred while fishing.'
            }
    
    async def get_fishing_stats(self, user_id: int) -> Dict[str, any]:
        """Get user's fishing statistics"""
        try:
            user = await self.db.fetch_one(
                "SELECT fishing_level, fishing_exp FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Get fishing records count
            total_catches = await self.db.fetch_val(
                "SELECT COUNT(*) FROM fishing_records WHERE user_id = ?",
                (user_id,)
            ) or 0
            
            # Get shiny catches from fishing records
            shiny_catches = 0  # Simplified for now - would need more complex query
            # For now, we'll use a simpler approach and track shiny catches separately
            
            cooldown_remaining = await self.get_fishing_cooldown_remaining(user_id)
            
            return {
                'success': True,
                'fishing_level': user['fishing_level'],
                'fishing_exp': user['fishing_exp'],
                'exp_to_next_level': (user['fishing_level'] * 100) - user['fishing_exp'],
                'total_catches': total_catches,
                'shiny_catches': shiny_catches,
                'cooldown_remaining': cooldown_remaining,
                'can_fish': cooldown_remaining == 0
            }
            
        except Exception as e:
            logger.error(f"Error getting fishing stats: {e}")
            return {
                'success': False,
                'error': 'Database error'
            }
    
    async def cleanup_cooldowns(self):
        """Clean up expired cooldowns"""
        try:
            current_time = datetime.now()
            expired_users = []
            
            for user_id, cooldown_time in self.user_cooldowns.items():
                if current_time >= cooldown_time:
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                del self.user_cooldowns[user_id]
                
        except Exception as e:
            logger.error(f"Error cleaning up cooldowns: {e}")

class FishingView(discord.ui.View):
    def __init__(self, bot, user_id):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
    
    @discord.ui.button(label="Cast Line", style=discord.ButtonStyle.green, emoji="🎣")
    async def cast_line(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This isn't your fishing spot!", ephemeral=True)
            return
        
        # Check cooldown
        can_fish = await self.bot.fishing_system.can_fish(int(self.user_id))
        if not can_fish:
            remaining = await self.bot.fishing_system.get_fishing_cooldown_remaining(int(self.user_id))
            await interaction.response.send_message(f"Your line is still in the water! Wait {remaining} seconds.", ephemeral=True)
            return
        
        # Go fishing
        result = await self.bot.fishing_system.go_fishing(int(self.user_id), interaction.channel)
        
        if result['success']:
            # Create success embed
            embed = discord.Embed(
                title="🎣 You caught something!",
                description=f"You caught a {'✨ Shiny ' if result['is_shiny'] else ''}**{result['pokemon_name']}**!",
                color=discord.Color.gold() if result['is_shiny'] else discord.Color.blue()
            )
            
            embed.add_field(name="Level", value=str(result['level']), inline=True)
            embed.add_field(name="Rarity", value=result['rarity'].title(), inline=True)
            embed.add_field(name="Rod Used", value=result['rod_used'], inline=True)
            
            if result['leveled_up']:
                embed.add_field(name="🎉 Level Up!", value=f"Fishing level increased to {result['new_fishing_level']}!", inline=False)
            
            embed.set_footer(text="Fishing EXP +10")
            
            await interaction.response.send_message(embed=embed)
            
            # Update the view
            stats = await self.bot.fishing_system.get_fishing_stats(int(self.user_id))
            new_embed = await self.create_fishing_embed(stats)
            await interaction.message.edit(embed=new_embed)
            
        else:
            await interaction.response.send_message(result['error'], ephemeral=True)
    
    @discord.ui.button(label="Check Rod", style=discord.ButtonStyle.blurple, emoji="🎒")
    async def check_rod(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != int(self.user_id):
            await interaction.response.send_message("This isn't your fishing spot!", ephemeral=True)
            return
        
        rod_type = await self.bot.fishing_system.get_user_rod(int(self.user_id))
        rod = self.bot.fishing_system.rods[rod_type]
        
        embed = discord.Embed(
            title="🎒 Your Fishing Rod",
            description=f"**{rod['name']}**",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Catch Rate", value=f"{rod['catch_rate']*100}%", inline=True)
        embed.add_field(name="Cost", value=f"{rod['cost']} credits" if rod['cost'] > 0 else "Free", inline=True)
        
        rarity_text = "\n".join([f"{k.title()}: {v*100}%" for k, v in rod['rarity_weights'].items()])
        embed.add_field(name="Catch Distribution", value=rarity_text, inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    async def create_fishing_embed(self, stats):
        """Create fishing interface embed"""
        embed = discord.Embed(
            title="🎣 Fishing Spot",
            description="Cast your line to catch water Pokemon!",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📊 Your Stats",
            value=f"Fishing Level: **{stats['fishing_level']}**\n"
                  f"Experience: **{stats['fishing_exp']}/{stats['fishing_level']*100}**\n"
                  f"Total Catches: **{stats['total_catches']}**\n"
                  f"Shiny Catches: **{stats['shiny_catches']}**",
            inline=True
        )
        
        if stats['cooldown_remaining'] > 0:
            embed.add_field(
                name="⏰ Cooldown",
                value=f"Wait **{stats['cooldown_remaining']}** seconds",
                inline=True
            )
        else:
            embed.add_field(
                name="🎣 Ready to Fish!",
                value="Your line is ready!",
                inline=True
            )
        
        embed.set_footer(text="Different rods have different catch rates and rarity distributions")
        
        return embed