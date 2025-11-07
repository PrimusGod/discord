import discord
from discord.ext import commands, tasks
import asyncio
import logging
logger = logging.getLogger(__name__)
import os
from datetime import datetime, timedelta
import random
import json

from config import Config
from database.db_manager import DatabaseManager
from pokemon.pokeapi_client import PokeAPIClient
from utils.battle_system import BattleSystem
from utils.spawn_system import SpawnSystem
from utils.economy_system import EconomySystem
from utils.mission_system import MissionSystem
from utils.fishing_system import FishingSystem
from utils.market_system import MarketSystem
from utils.trading_system import TradingSystem
from utils.tournament_system import TournamentSystem

# Set up logging (initial setup is done in run_bot.py, but this ensures it's available)
# Keeping this block here ensures the file itself has logger configured if run directly (though we won't run it directly now)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pokemon_bot.log'),
        logging.StreamHandler()
    ]
)

# Re-define logger to use the correct module name if needed
logger = logging.getLogger(__name__)

class PokemonBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix=';',
            intents=intents,
            help_command=None,
            case_insensitive=True
        )
        
        self.config = Config()
        self.db = DatabaseManager(self.config.database_path)
        self.pokeapi = None
        self.battle_system = None
        self.spawn_system = None
        self.economy_system = None
        self.mission_system = None
        self.fishing_system = None
        self.market_system = None
        self.trading_system = None
        self.tournament_system = None
        
        # Active sessions
        self.active_battles = {}
        self.active_trades = {}
        self.active_spawns = {}
        self.user_sessions = {}
    
    async def setup_hook(self):
        """Initialize bot systems and load cogs"""
        logger.info("Setting up Pokemon Bot...")
        
        # Initialize database
        await self.db.initialize()
        
        # Initialize PokeAPI client
        self.pokeapi = PokeAPIClient(self.db)
        await self.pokeapi.initialize()
        
        # Initialize systems
        self.battle_system = BattleSystem(self.db, self.config)
        self.spawn_system = SpawnSystem(self.db, self.config)
        self.economy_system = EconomySystem(self.db, self.config)
        self.mission_system = MissionSystem(self.db, self.config)
        self.fishing_system = FishingSystem(self.db, self.config)
        self.market_system = MarketSystem(self.db, self.config)
        self.trading_system = TradingSystem(self.db, self.config)
        self.tournament_system = TournamentSystem(self.db, self.config)
        
        # --- COG LOADING CONSOLIDATED HERE ---
        logger.info("Loading Cogs...")
        await self.load_extension('cogs.general')
        await self.load_extension('cogs.pokemon')
        await self.load_extension('cogs.battle')
        await self.load_extension('cogs.market')
     #   await self.load_extension('cogs.trading')
        await self.load_extension('cogs.missions')
        await self.load_extension('cogs.fishing')
        await self.load_extension('cogs.tournaments')
        await self.load_extension('cogs.admin')
        logger.info("All cogs loaded successfully")
        # -------------------------------------
        
        # Start background tasks
        self.cleanup_task.start()
        self.spawn_task.start()
        
        logger.info("Pokemon Bot setup completed")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Bot is in {len(self.guilds)} guilds')
        
        # Sync slash commands
        try:
            # We use self.tree (AppCommandTree) to sync slash commands
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")
    
    async def on_message(self, message):
        """Handle incoming messages"""
        # Ignore bot messages
        if message.author.bot:
            return
        
        # Process commands
        await self.process_commands(message)
        
        # Handle Pokemon catching (name-based)
        if message.content and not message.content.startswith(self.command_prefix):
            await self.handle_pokemon_catching(message)
        
        # Random Pokemon spawning
        if random.random() < self.config.spawn_rate:
            await self.spawn_system.handle_spawn(message.channel)
    
    async def handle_pokemon_catching(self, message):
        """Handle Pokemon catching by name"""
        # Check if there's an active spawn in this channel
        active_spawns = await self.db.get_active_spawns(str(message.channel.id))
        
        if active_spawns:
            for spawn in active_spawns:
                # Note: The original logic here assumes 'name' and 'sprite_url' are directly in the spawn dictionary,
                # which may not be true if the `get_active_spawns` only returns IDs. This is left as-is for now.
                pokemon_name = spawn['name'].lower()
                message_content = message.content.lower()
                
                # Check if the message contains the Pokemon name
                if pokemon_name in message_content or message_content in pokemon_name:
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
                            description=f"**{message.author.display_name}** caught a{' shiny ' if spawn['is_shiny'] else ' '}{spawn['name']}!",
                            color=discord.Color.gold() if spawn['is_shiny'] else discord.Color.green()
                        )
                        
                        if spawn['sprite_url']:
                            embed.set_thumbnail(url=spawn['sprite_url'])
                        
                        embed.add_field(name="Credits Earned", value=f"+{self.config.catch_credits}", inline=True)
                        embed.add_field(name="EXP Gained", value=f"+{self.config.catch_exp}", inline=True)
                        
                        await message.channel.send(embed=embed)
                        
                        # Update mission progress
                        await self.mission_system.update_progress(user['user_id'], 'catch', 1)
                        
                        break
    
    @tasks.loop(minutes=10)
    async def cleanup_task(self):
        """Periodic cleanup task"""
        try:
            await self.db.cleanup_expired_spawns()
            await self.db.cleanup_expired_market_listings()
            await self.db.cleanup_old_battles()
            await self.fishing_system.cleanup_cooldowns()
            logger.info("Cleanup task completed")
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
    
    @tasks.loop(minutes=1)
    async def spawn_task(self):
        """Periodic spawn task (placeholder since message-based is used)"""
        pass
    
    async def close(self):
        """Clean shutdown"""
        logger.info("Shutting down Pokemon Bot...")
        
        # Cancel tasks
        self.cleanup_task.cancel()
        self.spawn_task.cancel()
        
        # Close systems
        if self.pokeapi:
            await self.pokeapi.close()
        
        await self.db.close()
        
        await super().close()

# The if __name__ == "__main__": block is REMOVED, as run_bot.py handles execution.

