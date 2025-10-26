import discord
import random
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class EconomySystem:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.daily_bonus_amount = 100
        self.vote_bonus_amount = 1500
        self.upvote_point_value = 10
    
    async def give_daily_bonus(self, user_id: int) -> Dict[str, any]:
        """Give daily bonus to user"""
        try:
            user = await self.db.fetch_one(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Check if daily bonus already claimed
            last_daily = user.get('last_daily')
            if last_daily:
                last_date = datetime.fromisoformat(last_daily).date()
                if last_date >= datetime.now().date():
                    return {'success': False, 'error': 'Daily bonus already claimed today'}
            
            # Give daily bonus
            await self.db.update_user_credits(user_id, self.daily_bonus_amount)
            
            # Update last daily claim
            await self.db.execute(
                "UPDATE users SET last_daily = datetime('now') WHERE user_id = ?",
                (user_id,)
            )
            
            return {
                'success': True,
                'amount': self.daily_bonus_amount,
                'new_balance': user['credits'] + self.daily_bonus_amount
            }
            
        except Exception as e:
            logger.error(f"Error giving daily bonus: {e}")
            return {'success': False, 'error': 'Database error'}
    
    async def process_vote(self, user_id: int) -> Dict[str, any]:
        """Process user vote reward"""
        try:
            user = await self.db.fetch_one(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Give vote bonus
            await self.db.update_user_credits(user_id, self.vote_bonus_amount)
            
            # Add upvote point
            await self.db.execute(
                "UPDATE users SET upvote_points = upvote_points + 1 WHERE user_id = ?",
                (user_id,)
            )
            
            return {
                'success': True,
                'credits_earned': self.vote_bonus_amount,
                'upvote_points_earned': 1,
                'new_balance': user['credits'] + self.vote_bonus_amount,
                'new_upvote_points': user['upvote_points'] + 1
            }
            
        except Exception as e:
            logger.error(f"Error processing vote: {e}")
            return {'success': False, 'error': 'Database error'}
    
    async def convert_upvote_points(self, user_id: int, points: int) -> Dict[str, any]:
        """Convert upvote points to redeems"""
        try:
            user = await self.db.fetch_one(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            current_points = user.get('upvote_points', 0)
            
            if current_points < points:
                return {'success': False, 'error': 'Not enough upvote points'}
            
            if points % self.upvote_point_value != 0:
                return {'success': False, 'error': f'Points must be in multiples of {self.upvote_point_value}'}
            
            redeems_earned = points // self.upvote_point_value
            
            # Deduct points and add redeems
            await self.db.execute(
                "UPDATE users SET upvote_points = upvote_points - ? WHERE user_id = ?",
                (points, user_id)
            )
            
            # Add redeems to inventory (assuming redeem is item ID 1)
            await self.db.add_item_to_inventory(user_id, 1, redeems_earned)
            
            return {
                'success': True,
                'points_used': points,
                'redeems_earned': redeems_earned,
                'remaining_points': current_points - points
            }
            
        except Exception as e:
            logger.error(f"Error converting upvote points: {e}")
            return {'success': False, 'error': 'Database error'}
    
    async def get_user_balance(self, user_id: int) -> Dict[str, any]:
        """Get user balance and economy stats"""
        try:
            user = await self.db.fetch_one(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Get Pokemon count
            pokemon_count = await self.db.get_user_pokemon_count(user_id)
            
            # Get inventory value (simplified)
            inventory = await self.db.get_user_inventory(user_id)
            inventory_value = sum(item['cost'] * item['quantity'] for item in inventory if item['cost'])
            
            return {
                'success': True,
                'credits': user['credits'],
                'upvote_points': user.get('upvote_points', 0),
                'total_exp': user['total_exp'],
                'pokemon_count': pokemon_count,
                'inventory_value': inventory_value,
                'luck': user.get('luck', 0),
                'fishing_level': user.get('fishing_level', 1),
                'fishing_exp': user.get('fishing_exp', 0)
            }
            
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            return {'success': False, 'error': 'Database error'}
    
    async def transfer_credits(self, from_user_id: int, to_user_id: int, amount: int) -> Dict[str, any]:
        """Transfer credits between users"""
        try:
            # Check sender has enough credits
            sender = await self.db.fetch_one(
                "SELECT credits FROM users WHERE user_id = ?",
                (from_user_id,)
            )
            
            if not sender:
                return {'success': False, 'error': 'Sender not found'}
            
            if sender['credits'] < amount:
                return {'success': False, 'error': 'Insufficient credits'}
            
            # Check recipient exists
            recipient = await self.db.fetch_one(
                "SELECT user_id FROM users WHERE user_id = ?",
                (to_user_id,)
            )
            
            if not recipient:
                return {'success': False, 'error': 'Recipient not found'}
            
            # Perform transfer
            await self.db.update_user_credits(from_user_id, -amount)
            await self.db.update_user_credits(to_user_id, amount)
            
            return {
                'success': True,
                'amount': amount,
                'sender_new_balance': sender['credits'] - amount,
                'recipient_new_balance': recipient.get('credits', 0) + amount
            }
            
        except Exception as e:
            logger.error(f"Error transferring credits: {e}")
            return {'success': False, 'error': 'Database error'}
    
    async def get_leaderboard(self, category: str = 'credits', limit: int = 10) -> Dict[str, any]:
        """Get economy leaderboard"""
        try:
            valid_categories = ['credits', 'total_exp', 'pokemon_count', 'upvote_points']
            
            if category not in valid_categories:
                category = 'credits'
            
            # Get leaderboard data
            if category == 'pokemon_count':
                query = """
                    SELECT u.user_id, u.discord_id, u.username, 
                           COUNT(pp.id) as pokemon_count
                    FROM users u
                    LEFT JOIN player_pokemon pp ON u.user_id = pp.user_id
                    GROUP BY u.user_id
                    ORDER BY pokemon_count DESC
                    LIMIT ?
                """
            else:
                query = f"""
                    SELECT user_id, discord_id, username, {category}
                    FROM users
                    ORDER BY {category} DESC
                    LIMIT ?
                """
            
            results = await self.db.fetch_all(query, (limit,))
            
            return {
                'success': True,
                'category': category,
                'leaders': results
            }
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return {'success': False, 'error': 'Database error'}
    
    async def get_shop_items(self) -> Dict[str, any]:
        """Get available shop items"""
        try:
            items = await self.db.fetch_all("""
                SELECT * FROM items 
                WHERE category IN ('pokeballs', 'medicine', 'battle-items', 'key')
                AND cost > 0
                ORDER BY category, cost
            """)
            
            # Group items by category
            categorized_items = {}
            for item in items:
                category = item['category']
                if category not in categorized_items:
                    categorized_items[category] = []
                categorized_items[category].append(item)
            
            return {
                'success': True,
                'items': categorized_items
            }
            
        except Exception as e:
            logger.error(f"Error getting shop items: {e}")
            return {'success': False, 'error': 'Database error'}
    
    async def buy_item(self, user_id: int, item_id: int, quantity: int = 1) -> Dict[str, any]:
        """Buy an item from the shop"""
        try:
            # Get item details
            item = await self.db.fetch_one(
                "SELECT * FROM items WHERE item_id = ?",
                (item_id,)
            )
            
            if not item:
                return {'success': False, 'error': 'Item not found'}
            
            if item['cost'] <= 0:
                return {'success': False, 'error': 'Item not for sale'}
            
            # Calculate total cost
            total_cost = item['cost'] * quantity
            
            # Check user has enough credits
            user = await self.db.fetch_one(
                "SELECT credits FROM users WHERE user_id = ?",
                (user_id,)
            )
            
            if not user or user['credits'] < total_cost:
                return {'success': False, 'error': 'Insufficient credits'}
            
            # Deduct credits and add item
            await self.db.update_user_credits(user_id, -total_cost)
            await self.db.add_item_to_inventory(user_id, item_id, quantity)
            
            return {
                'success': True,
                'item_name': item['name'],
                'quantity': quantity,
                'total_cost': total_cost,
                'new_balance': user['credits'] - total_cost
            }
            
        except Exception as e:
            logger.error(f"Error buying item: {e}")
            return {'success': False, 'error': 'Database error'}
    
    async def sell_item(self, user_id: int, item_id: int, quantity: int = 1) -> Dict[str, any]:
        """Sell an item to the shop"""
        try:
            # Get item details
            item = await self.db.fetch_one(
                "SELECT * FROM items WHERE item_id = ?",
                (item_id,)
            )
            
            if not item:
                return {'success': False, 'error': 'Item not found'}
            
            # Check user has the item
            current_qty = await self.db.fetch_val(
                "SELECT quantity FROM player_inventory WHERE user_id = ? AND item_id = ?",
                (user_id, item_id)
            ) or 0
            
            if current_qty < quantity:
                return {'success': False, 'error': 'Not enough items to sell'}
            
            # Calculate sell price (50% of buy price)
            sell_price = int(item['cost'] * 0.5 * quantity)
            
            # Remove item and add credits
            await self.db.remove_item_from_inventory(user_id, item_id, quantity)
            await self.db.update_user_credits(user_id, sell_price)
            
            return {
                'success': True,
                'item_name': item['name'],
                'quantity': quantity,
                'sell_price': sell_price
            }
            
        except Exception as e:
            logger.error(f"Error selling item: {e}")
            return {'success': False, 'error': 'Database error'}
    
    async def get_user_inventory_value(self, user_id: int) -> Dict[str, any]:
        """Calculate total value of user's inventory"""
        try:
            inventory = await self.db.get_user_inventory(user_id)
            
            total_value = 0
            item_breakdown = {}
            
            for item in inventory:
                item_value = item['cost'] * item['quantity']
                total_value += item_value
                
                if item['category'] not in item_breakdown:
                    item_breakdown[item['category']] = 0
                item_breakdown[item['category']] += item_value
            
            return {
                'success': True,
                'total_value': total_value,
                'breakdown': item_breakdown,
                'item_count': len(inventory)
            }
            
        except Exception as e:
            logger.error(f"Error calculating inventory value: {e}")
            return {'success': False, 'error': 'Database error'}