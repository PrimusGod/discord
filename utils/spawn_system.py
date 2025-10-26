import discord
import random
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SpawnSystem:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.spawn_rates = {
            'common': 0.7,      # 70%
            'uncommon': 0.2,    # 20%
            'rare': 0.07,       # 7%
            'legendary': 0.02,  # 2%
            'mythical': 0.008,  # 0.8%
            'ultra_beast': 0.002 # 0.2%
        }
        
        # Pokemon spawn weights by category
        self.category_weights = {
            'normal': 100,
            'legendary': 1,
            'mythical': 0.5,
            'ultra_beast': 0.3
        }
        
        # Spawn cooldowns per channel
        self.channel_cooldowns = {}
        self.cooldown_time = 300  # 5 minutes
    
    async def handle_spawn(self, channel: discord.TextChannel) -> bool:
        """Handle Pokemon spawning in a channel"""
        channel_id = 824750721990656061
        
        # Check cooldown
        if channel_id in self.channel_cooldowns:
            if datetime.now() < self.channel_cooldowns[channel_id]:
                return False
        
        # Check if channel has too many spawns
        active_spawns = await self.db.get_active_spawns(channel_id)
        if len(active_spawns) >= self.config.max_spawns_per_channel:
            return False
        
        # Determine spawn rarity
        rarity_roll = random.random()
        cumulative = 0
        selected_rarity = 'common'
        
        for rarity, rate in self.spawn_rates.items():
            cumulative += rate
            if rarity_roll < cumulative:
                selected_rarity = rarity
                break
        
        # Get Pokemon to spawn based on rarity
        pokemon_id = await self._select_pokemon_for_spawn(selected_rarity)
        
        if not pokemon_id:
            return False
        
        # Determine if shiny
        is_shiny = random.random() < self.config.shiny_rate
        
        # Create spawn
        spawn_id = await self.db.create_spawn(channel_id, pokemon_id, is_shiny)
        
        # Send spawn message
        await self._send_spawn_message(channel, spawn_id, pokemon_id, is_shiny)
        
        # Set cooldown
        self.channel_cooldowns[channel_id] = datetime.now() + timedelta(seconds=self.cooldown_time)
        
        return True
    
    async def _select_pokemon_for_spawn(self, rarity: str) -> Optional[int]:
        """Select a Pokemon to spawn based on rarity"""
        try:
            # Define rarity categories
            rarity_categories = {
                'common': ['normal'],
                'uncommon': ['normal'],
                'rare': ['normal', 'legendary'],
                'legendary': ['legendary'],
                'mythical': ['mythical'],
                'ultra_beast': ['ultra_beast']
            }
            
            categories = rarity_categories.get(rarity, ['normal'])
            
            # Build query based on categories
            placeholders = ','.join('?' * len(categories))
            query = f"""
                SELECT pokemon_id FROM pokemon_species 
                WHERE category IN ({placeholders}) 
                AND pokemon_id <= 1008
                ORDER BY RANDOM() 
                LIMIT 1
            """
            
            result = await self.db.fetch_one(query, tuple(categories))
            
            return result['pokemon_id'] if result else None
            
        except Exception as e:
            logger.error(f"Error selecting Pokemon for spawn: {e}")
            return None
    
    async def _send_spawn_message(self, channel: discord.TextChannel, spawn_id: int, pokemon_id: int, is_shiny: bool):
        """Send a spawn message to the channel"""
        try:
            # Get Pokemon details
            pokemon = await self.db.fetch_one(
                "SELECT * FROM pokemon_species WHERE pokemon_id = ?",
                (pokemon_id,)
            )
            
            if not pokemon:
                return
            
            # Create embed
            embed = discord.Embed(
                title=f"A wild Pokemon appeared!",
                description=f"Type the Pokemon's name to catch it!",
                color=discord.Color.gold() if is_shiny else discord.Color.green()
            )
            
            # Set Pokemon image
            sprite_url = pokemon['shiny_sprite_url'] if is_shiny else pokemon['sprite_url']
            if sprite_url:
                embed.set_thumbnail(url=sprite_url)
            
            # Add Pokemon details
            embed.add_field(name="Name", value="???", inline=True)
            # Corrected line: removed the backslashes from the inner f-string
            embed.add_field(name="Type", value=f"{pokemon['type1']}{'/' + pokemon['type2'] if pokemon['type2'] else ''}", inline=True)


            
            if is_shiny:
                embed.add_field(name="Special", value="✨ Shiny ✨", inline=True)
            
            # Add rarity indicator
            rarity_emoji = {
                'normal': '⚪',
                'legendary': '🟡',
                'mythical': '🟣',
                'ultra_beast': '🟠'
            }
            rarity = pokemon['category']
            embed.set_footer(text=f"{rarity_emoji.get(rarity, '⚪')} {rarity.title()}")
            
            # Send message
            message = await channel.send(embed=embed)
            
            # Store spawn message ID for updates
            await self.db.execute(
                "UPDATE active_spawns SET message_id = ? WHERE spawn_id = ?",
                (str(message.id), spawn_id)
            )
            
        except Exception as e:
            logger.error(f"Error sending spawn message: {e}")
    
    async def handle_hint_request(self, channel: discord.TextChannel, user: discord.User) -> bool:
        """Handle hint request for Pokemon spawning"""
        try:
            channel_id = str(channel.id)
            active_spawns = await self.db.get_active_spawns(channel_id)
            
            if not active_spawns:
                return False
            
            # Get the oldest active spawn
            spawn = active_spawns[0]
            
            # Get Pokemon details
            pokemon = await self.db.fetch_one(
                "SELECT * FROM pokemon_species WHERE pokemon_id = ?",
                (spawn['pokemon_id'],)
            )
            
            if not pokemon:
                return False
            
            # Generate hint
            hint = self._generate_pokemon_hint(pokemon['name'])
            
            # Create hint embed
            embed = discord.Embed(
                title=f"Pokemon Hint",
                description=f"Here's a hint for the wild Pokemon!",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Hint", value=hint, inline=False)
            embed.set_footer(text=f"Requested by {user.display_name}")
            
            await channel.send(embed=embed, delete_after=30)
            
            # Mark hint as used
            await self.db.execute(
                "UPDATE active_spawns SET hint_used = TRUE WHERE spawn_id = ?",
                (spawn['spawn_id'],)
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling hint request: {e}")
            return False
    
    def _generate_pokemon_hint(self, pokemon_name: str) -> str:
        """Generate a hint for a Pokemon name"""
        name = pokemon_name.lower()
        hint_parts = []
        
        # Different hint types
        hint_type = random.choice(['scramble', 'missing_letters', 'length', 'first_last'])
        
        if hint_type == 'scramble':
            # Scramble the letters
            scrambled = list(name)
            random.shuffle(scrambled)
            hint = f"Scrambled: {''.join(scrambled).upper()}"
            
        elif hint_type == 'missing_letters':
            # Remove some letters
            name_list = list(name)
            num_to_remove = max(1, len(name) // 3)
            
            for _ in range(num_to_remove):
                if len(name_list) > 0:
                    index = random.randint(0, len(name_list) - 1)
                    name_list[index] = '_'
            
            hint = f"Missing letters: {''.join(name_list).upper()}"
            
        elif hint_type == 'length':
            # Give length and first/last letters
            first_letter = name[0].upper()
            last_letter = name[-1].upper()
            hint = f"{len(name)} letters, starts with {first_letter}, ends with {last_letter}"
            
        else:  # first_last
            # Give first and last letters
            first_letter = name[0].upper()
            last_letter = name[-1].upper()
            hint = f"Starts with {first_letter}, ends with {last_letter}"
        
        return hint
    
    async def handle_catch_attempt(self, message: discord.Message) -> bool:
        """Handle Pokemon catching attempt"""
        try:
            channel_id = str(message.channel.id)
            active_spawns = await self.db.get_active_spawns(channel_id)
            
            if not active_spawns:
                return False
            
            # Get the oldest active spawn
            spawn = active_spawns[0]
            
            # Get Pokemon details
            pokemon = await self.db.fetch_one(
                "SELECT * FROM pokemon_species WHERE pokemon_id = ?",
                (spawn['pokemon_id'],)
            )
            
            if not pokemon:
                return False
            
            # Check if the message contains the Pokemon name
            message_content = message.content.lower()
            pokemon_name = pokemon['name'].lower()
            
            if pokemon_name not in message_content and message_content not in pokemon_name:
                return False
            
            # Get or create user
            user = await self.db.get_or_create_user(str(message.author.id), message.author.display_name)
            
            # Catch the Pokemon
            success = await self.db.catch_spawn(spawn['spawn_id'], user['user_id'])
            
            if success:
                # Add to user's collection
                pokemon_uid = await self.db.add_pokemon_to_user(
                    user['user_id'],
                    spawn['pokemon_id'],
                    is_shiny=spawn['is_shiny']
                )
                
                # Update user stats
                await self.db.update_user_credits(user['user_id'], self.config.catch_credits)
                await self.db.update_user_exp(user['user_id'], self.config.catch_exp)
                
                # Send success message
                embed = discord.Embed(
                    title="🎉 Pokemon Caught!",
                    description=f"**{message.author.display_name}** caught a{' shiny ' if spawn['is_shiny'] else ' '}{pokemon['name']}!",
                    color=discord.Color.gold() if spawn['is_shiny'] else discord.Color.green()
                )
                
                if pokemon['sprite_url']:
                    sprite_url = pokemon['shiny_sprite_url'] if spawn['is_shiny'] else pokemon['sprite_url']
                    embed.set_thumbnail(url=sprite_url)
                
                embed.add_field(name="Credits Earned", value=f"+{self.config.catch_credits}", inline=True)
                embed.add_field(name="EXP Gained", value=f"+{self.config.catch_exp}", inline=True)
                
                # Show Pokemon stats
                embed.add_field(name="Level", value="5", inline=True)
                # Corrected line: removed the backslashes from the inner f-string
                embed.add_field(name="Type", value=f"{pokemon['type1']}{'/' + pokemon['type2'] if pokemon['type2'] else ''}", inline=True)



                
                await message.channel.send(embed=embed)
                
                # Update mission progress
                # This would integrate with the mission system
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error handling catch attempt: {e}")
            return False
    
    async def cleanup_expired_spawns(self):
        """Clean up expired spawns"""
        try:
            # Get expired spawns
            expired_spawns = await self.db.fetch_all("""
                SELECT * FROM active_spawns 
                WHERE despawn_time < datetime('now') AND is_caught = FALSE
            """)
            
            for spawn in expired_spawns:
                # Try to find the original message and update it
                try:
                    if spawn.get('message_id'):
                        # This assumes self.bot exists, which isn't defined in SpawnSystem __init__
                        # but likely defined when SpawnSystem is instantiated in bot.py
                        channel = self.bot.get_channel(int(spawn['channel_id']))
                        if channel:
                            message = await channel.fetch_message(int(spawn['message_id']))
                            
                            # Create despawn embed
                            embed = discord.Embed(
                                title="The Pokemon fled!",
                                description="The wild Pokemon got away...",
                                color=discord.Color.red()
                            )
                            
                            await message.edit(embed=embed)
                            
                except Exception as e:
                    logger.error(f"Error updating despawn message: {e}")
                
                # Remove from database
                await self.db.execute(
                    "DELETE FROM active_spawns WHERE spawn_id = ?",
                    (spawn['spawn_id'],)
                )
            
            if expired_spawns:
                logger.info(f"Cleaned up {len(expired_spawns)} expired spawns")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired spawns: {e}")
    
    async def get_spawn_stats(self, channel_id: str) -> Dict[str, any]:
        """Get spawn statistics for a channel"""
        try:
            active_spawns = await self.db.get_active_spawns(channel_id)
            
            stats = {
                'active_spawns': len(active_spawns),
                'spawn_list': []
            }
            
            for spawn in active_spawns:
                pokemon = await self.db.fetch_one(
                    "SELECT * FROM pokemon_species WHERE pokemon_id = ?",
                    (spawn['pokemon_id'],)
                )
                
                if pokemon:
                    stats['spawn_list'].append({
                        'name': pokemon['name'],
                        'is_shiny': spawn['is_shiny'],
                        'type1': pokemon['type1'],
                        'type2': pokemon['type2'],
                        'category': pokemon['category'],
                        'time_remaining': (datetime.fromisoformat(spawn['despawn_time']) - datetime.now()).total_seconds()
                    })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting spawn stats: {e}")
            return {'active_spawns': 0, 'spawn_list': []}
