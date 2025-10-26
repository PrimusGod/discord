import discord
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TradingSystem:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.active_trades = {}
    
    async def create_trade(self, initiator_id: int, recipient_id: int) -> int:
        """Create a new trade"""
        try:
            trade_id = await self.db.create_trade(initiator_id, recipient_id)
            return trade_id
        except Exception as e:
            logger.error(f"Error creating trade: {e}")
            return 0
    
    async def add_pokemon_to_trade(self, trade_id: int, pokemon_uid: int, offered_by: int) -> bool:
        """Add Pokemon to trade"""
        try:
            await self.db.add_pokemon_to_trade(trade_id, pokemon_uid, offered_by)
            return True
        except Exception as e:
            logger.error(f"Error adding Pokemon to trade: {e}")
            return False
    
    async def complete_trade(self, trade_id: int) -> Dict[str, any]:
        """Complete a trade"""
        try:
            # Get trade details
            trade = await self.db.get_trade(trade_id)
            
            if not trade or trade['status'] != 'pending':
                return {
                    'success': False,
                    'error': 'Trade not found or not pending'
                }
            
            # Get trade Pokemon
            trade_pokemon = await self.db.fetch_all(
                "SELECT * FROM trade_pokemon WHERE trade_id = ?",
                (trade_id,)
            )
            
            # Transfer Pokemon ownership
            for trade_poke in trade_pokemon:
                await self.db.execute(
                    "UPDATE player_pokemon SET user_id = ? WHERE id = ?",
                    (trade_poke['offered_by'], trade_poke['pokemon_uid'])
                )
            
            # Update trade status
            await self.db.execute(
                "UPDATE trades SET status = 'completed', completed_date = datetime('now') WHERE trade_id = ?",
                (trade_id,)
            )
            
            return {
                'success': True,
                'trade_id': trade_id,
                'pokemon_transferred': len(trade_pokemon)
            }
            
        except Exception as e:
            logger.error(f"Error completing trade: {e}")
            return {
                'success': False,
                'error': 'Database error'
            }
    
    async def cancel_trade(self, trade_id: int) -> bool:
        """Cancel a trade"""
        try:
            await self.db.execute(
                "UPDATE trades SET status = 'cancelled' WHERE trade_id = ?",
                (trade_id,)
            )
            return True
        except Exception as e:
            logger.error(f"Error cancelling trade: {e}")
            return False