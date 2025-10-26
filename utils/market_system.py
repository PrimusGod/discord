import discord
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class MarketSystem:
    def __init__(self, db, config):
        self.db = db
        self.config = config
    
    async def create_listing(self, seller_id: int, pokemon_uid: int, price: int) -> int:
        """Create a market listing"""
        try:
            listing_id = await self.db.create_market_listing(seller_id, pokemon_uid, price)
            return listing_id
        except Exception as e:
            logger.error(f"Error creating market listing: {e}")
            return 0
    
    async def purchase_pokemon(self, buyer_id: int, listing_id: int) -> Dict[str, any]:
        """Purchase a Pokemon from the market"""
        try:
            # Get listing details
            listing = await self.db.fetch_one(
                "SELECT * FROM market_listings WHERE listing_id = ? AND is_sold = FALSE",
                (listing_id,)
            )
            
            if not listing:
                return {
                    'success': False,
                    'error': 'Listing not found or already sold'
                }
            
            # Check if buyer has enough credits
            buyer = await self.db.fetch_one(
                "SELECT credits FROM users WHERE user_id = ?",
                (buyer_id,)
            )
            
            if not buyer or buyer['credits'] < listing['price']:
                return {
                    'success': False,
                    'error': 'Insufficient credits'
                }
            
            # Calculate tax and amounts
            tax = int(listing['price'] * self.config.market_tax)
            seller_amount = listing['price'] - tax
            
            # Transfer credits
            await self.db.update_user_credits(buyer_id, -listing['price'])
            await self.db.update_user_credits(listing['seller_id'], seller_amount)
            
            # Transfer Pokemon ownership
            await self.db.execute(
                "UPDATE player_pokemon SET user_id = ? WHERE id = ?",
                (buyer_id, listing['pokemon_uid'])
            )
            
            # Mark listing as sold
            await self.db.execute(
                "UPDATE market_listings SET is_sold = TRUE, buyer_id = ?, sale_date = datetime('now') WHERE listing_id = ?",
                (buyer_id, listing_id)
            )
            
            return {
                'success': True,
                'pokemon_uid': listing['pokemon_uid'],
                'price': listing['price'],
                'tax': tax,
                'seller_amount': seller_amount
            }
            
        except Exception as e:
            logger.error(f"Error purchasing Pokemon: {e}")
            return {
                'success': False,
                'error': 'Database error'
            }