#!/usr/bin/env python3
"""
Pokemon Discord Bot Runner
This script sets up and runs the comprehensive Pokemon Discord bot.
"""

import asyncio
import logging
logger = logging.getLogger(__name__)
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bot import PokemonBot

async def setup_and_run():
    """Setup and run the Pokemon bot"""
    
    # Create necessary directories
    Path("data").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)
    
    # Initialize bot
    bot = PokemonBot()
    
    try:
        # Start the bot
        await bot.start(bot.config.token)
        
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        await bot.close()

def main():
    """Main entry point"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/pokemon_bot.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    
    # Check for Discord token
    if not os.getenv('DISCORD_TOKEN'):
        logger.error("DISCORD_TOKEN environment variable not found!")
        logger.error("Please set your Discord bot token in the DISCORD_TOKEN environment variable")
        sys.exit(1)
    
    logger.info("Starting Pokemon Discord Bot...")
    logger.info("This bot includes:")
    logger.info("- Complete Pokemon database (1000+ Pokemon)")
    logger.info("- Turn-based battle system with status effects")
    logger.info("- Pokemon catching from chat conversations")
    logger.info("- Trading and marketplace system")
    logger.info("- Daily missions ad rewards")
    logger.info("- Fishing mini-game")
    logger.info("- Economy system with credits and items")
    logger.info("- And much more!")
    
    try:
        asyncio.run(setup_and_run())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
