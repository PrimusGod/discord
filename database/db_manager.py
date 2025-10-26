import sqlite3
import json
import asyncio
import aiosqlite
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.pool = None
    
    async def initialize(self):
        """Initialize the database connection pool"""
        self.pool = await aiosqlite.connect(self.db_path)
        self.pool.row_factory = aiosqlite.Row
        await self.create_tables()
    
    async def close(self):
        """Close the database connection"""
        if self.pool:
            await self.pool.close()
    
    async def create_tables(self):
        """Create all database tables from schema"""
        try:
            with open('database/schema.sql', 'r') as f:
                schema = f.read()
            
            await self.pool.executescript(schema)
            await self.pool.commit()
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    async def execute(self, query: str, params: Tuple = ()) -> int:
        """Execute a query and return the number of affected rows"""
        async with self.pool.execute(query, params) as cursor:
            await self.pool.commit()
            return cursor.rowcount
    
    async def fetch_one(self, query: str, params: Tuple = ()) -> Optional[Dict[str, Any]]:
        """Fetch a single row from the database"""
        async with self.pool.execute(query, params) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    async def fetch_all(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Fetch all rows from the database"""
        async with self.pool.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def fetch_val(self, query: str, params: Tuple = ()) -> Optional[Any]:
        """Fetch a single value from the database"""
        async with self.pool.execute(query, params) as cursor:
            row = await cursor.fetchone()
            if row:
                return row[0]
            return None
    
    async def insert_and_get_id(self, query: str, params: Tuple = ()) -> int:
        """Insert a row and return the inserted ID"""
        async with self.pool.execute(query, params) as cursor:
            await self.pool.commit()
            return cursor.lastrowid
    
    # User management
    async def get_or_create_user(self, discord_id: str, username: str) -> Dict[str, Any]:
        """Get or create a user"""
        user = await self.fetch_one(
            "SELECT * FROM users WHERE discord_id = ?",
            (discord_id,)
        )
        
        if not user:
            user_id = await self.insert_and_get_id(
                "INSERT INTO users (discord_id, username) VALUES (?, ?)",
                (discord_id, username)
            )
            user = await self.fetch_one(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
        
        return user
    
    async def update_user_credits(self, user_id: int, credits: int):
        """Update user credits"""
        await self.execute(
            "UPDATE users SET credits = credits + ? WHERE user_id = ?",
            (credits, user_id)
        )
    
    async def update_user_exp(self, user_id: int, exp: int):
        """Update user experience"""
        await self.execute(
            "UPDATE users SET total_exp = total_exp + ? WHERE user_id = ?",
            (exp, user_id)
        )
    
    # Pokemon management
    async def add_pokemon_to_user(self, user_id: int, pokemon_id: int, level: int = 5, 
                                  is_shiny: bool = False, caught_location: str = "Wild") -> int:
        """Add a Pokemon to user's collection"""
        # Get Pokemon base stats
        pokemon = await self.fetch_one(
            "SELECT * FROM pokemon_species WHERE pokemon_id = ?",
            (pokemon_id,)
        )
        
        if not pokemon:
            raise ValueError(f"Pokemon with ID {pokemon_id} not found")
        
        # Generate IVs (0-31)
        import random
        ivs = {
            'hp_iv': random.randint(0, 31),
            'attack_iv': random.randint(0, 31),
            'defense_iv': random.randint(0, 31),
            'sp_attack_iv': random.randint(0, 31),
            'sp_defense_iv': random.randint(0, 31),
            'speed_iv': random.randint(0, 31)
        }
        
        # Calculate stats
        base_stats = {
            'hp': pokemon['base_hp'],
            'attack': pokemon['base_attack'],
            'defense': pokemon['base_defense'],
            'sp_attack': pokemon['base_sp_attack'],
            'sp_defense': pokemon['base_sp_defense'],
            'speed': pokemon['base_speed']
        }
        
        # Simple stat calculation (simplified for this implementation)
        max_hp = int(((2 * base_stats['hp'] + ivs['hp_iv']) * level) / 100) + level + 10
        other_stats = {
            stat: int(((2 * base_stats[stat.replace('_iv', '')] + ivs[f"{stat}"]) * level) / 100) + 5
            for stat in ['attack_iv', 'defense_iv', 'sp_attack_iv', 'sp_defense_iv', 'speed_iv']
        }
        
        pokemon_uid = await self.insert_and_get_id("""
            INSERT INTO player_pokemon (
                user_id, pokemon_id, level, current_hp, max_hp,
                hp_iv, attack_iv, defense_iv, sp_attack_iv, sp_defense_iv, speed_iv,
                is_shiny, caught_location, ot_user_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id, pokemon_id, level, max_hp, max_hp,
            ivs['hp_iv'], ivs['attack_iv'], ivs['defense_iv'],
            ivs['sp_attack_iv'], ivs['sp_defense_iv'], ivs['speed_iv'],
            is_shiny, caught_location, user_id
        ))
        
        return pokemon_uid
    
    async def get_user_pokemon_count(self, user_id: int) -> int:
        """Get the number of Pokemon a user has"""
        return await self.fetch_val(
            "SELECT COUNT(*) FROM player_pokemon WHERE user_id = ?",
            (user_id,)
        ) or 0
    
    async def get_user_pokemon(self, user_id: int, limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get user's Pokemon with pagination"""
        query = """
            SELECT pp.*, ps.name, ps.type1, ps.type2, ps.sprite_url, ps.shiny_sprite_url
            FROM player_pokemon pp
            JOIN pokemon_species ps ON pp.pokemon_id = ps.pokemon_id
            WHERE pp.user_id = ?
            ORDER BY pp.caught_date DESC
        """
        
        params = [user_id]
        if limit:
            query += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        
        return await self.fetch_all(query, tuple(params))
    
    # Spawn management
    async def create_spawn(self, channel_id: str, pokemon_id: int, is_shiny: bool = False) -> int:
        """Create a new Pokemon spawn"""
        despawn_time = datetime.now() + timedelta(minutes=40)
        
        spawn_id = await self.insert_and_get_id("""
            INSERT INTO active_spawns (channel_id, pokemon_id, is_shiny, despawn_time)
            VALUES (?, ?, ?, ?)
        """, (channel_id, pokemon_id, is_shiny, despawn_time))
        
        return spawn_id
    
    async def get_active_spawns(self, channel_id: str) -> List[Dict[str, Any]]:
        """Get all active spawns in a channel"""
        return await self.fetch_all("""
            SELECT act.*, ps.name, ps.type1, ps.type2, ps.sprite_url, ps.shiny_sprite_url
            FROM active_spawns act
            JOIN pokemon_species ps ON act.pokemon_id = ps.pokemon_id
            WHERE act.channel_id = ? AND act.is_caught = FALSE 
            AND act.despawn_time > datetime('now')
        """, (channel_id,))
    
    async def catch_spawn(self, spawn_id: int, user_id: int) -> bool:
        """Mark a spawn as caught and add Pokemon to user"""
        async with self.pool:
            # Get spawn details
            spawn = await self.fetch_one(
                "SELECT * FROM active_spawns WHERE spawn_id = ?",
                (spawn_id,)
            )
            
            if not spawn or spawn['is_caught']:
                return False
            
            # Mark as caught
            await self.execute(
                "UPDATE active_spawns SET is_caught = TRUE WHERE spawn_id = ?",
                (spawn_id,)
            )
            
            # Add Pokemon to user
            pokemon_uid = await self.add_pokemon_to_user(
                user_id, spawn['pokemon_id'],
                is_shiny=spawn['is_shiny']
            )
            
            return pokemon_uid is not None
    
    # Battle management
    async def create_battle(self, player1_id: int, player2_id: int, battle_type: str, channel_id: str) -> int:
        """Create a new battle"""
        battle_id = await self.insert_and_get_id("""
            INSERT INTO active_battles (player1_id, player2_id, battle_type, channel_id)
            VALUES (?, ?, ?, ?)
        """, (player1_id, player2_id, battle_type, channel_id))
        
        return battle_id
    
    async def get_battle(self, battle_id: int) -> Optional[Dict[str, Any]]:
        """Get battle details"""
        return await self.fetch_one(
            "SELECT * FROM active_battles WHERE battle_id = ?",
            (battle_id,)
        )
    
    async def get_active_battles(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's active battles"""
        return await self.fetch_all("""
            SELECT * FROM active_battles 
            WHERE (player1_id = ? OR player2_id = ?) 
            AND status = 'active'
        """, (user_id, user_id))
    
    # Inventory management
    async def get_user_inventory(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's inventory"""
        return await self.fetch_all("""
            SELECT pi.*, i.name, i.description, i.sprite_url
            FROM player_inventory pi
            JOIN items i ON pi.item_id = i.item_id
            WHERE pi.user_id = ? AND pi.quantity > 0
        """, (user_id,))
    
    async def add_item_to_inventory(self, user_id: int, item_id: int, quantity: int = 1):
        """Add item to user's inventory"""
        await self.execute("""
            INSERT OR REPLACE INTO player_inventory (user_id, item_id, quantity)
            VALUES (?, ?, COALESCE((SELECT quantity FROM player_inventory WHERE user_id = ? AND item_id = ?), 0) + ?)
        """, (user_id, item_id, user_id, item_id, quantity))
    
    async def remove_item_from_inventory(self, user_id: int, item_id: int, quantity: int = 1):
        """Remove item from user's inventory"""
        current_qty = await self.fetch_val(
            "SELECT quantity FROM player_inventory WHERE user_id = ? AND item_id = ?",
            (user_id, item_id)
        ) or 0
        
        if current_qty >= quantity:
            await self.execute(
                "UPDATE player_inventory SET quantity = quantity - ? WHERE user_id = ? AND item_id = ?",
                (quantity, user_id, item_id)
            )
            return True
        return False
    
    # Market management
    async def create_market_listing(self, seller_id: int, pokemon_uid: int, price: int) -> int:
        """Create a market listing"""
        expires_date = datetime.now() + timedelta(days=7)
        
        listing_id = await self.insert_and_get_id("""
            INSERT INTO market_listings (seller_id, pokemon_uid, price, expires_date)
            VALUES (?, ?, ?, ?)
        """, (seller_id, pokemon_uid, price, expires_date))
        
        return listing_id
    
    async def get_market_listings(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get active market listings"""
        return await self.fetch_all("""
            SELECT ml.*, ps.name, ps.sprite_url, ps.shiny_sprite_url, u.username as seller_name
            FROM market_listings ml
            JOIN player_pokemon pp ON ml.pokemon_uid = pp.id
            JOIN pokemon_species ps ON pp.pokemon_id = ps.pokemon_id
            JOIN users u ON ml.seller_id = u.user_id
            WHERE ml.is_sold = FALSE AND ml.expires_date > datetime('now')
            ORDER BY ml.listed_date DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
    
    # Daily missions
    async def get_or_create_daily_mission(self, user_id: int, mission_date: str) -> Dict[str, Any]:
        """Get or create a daily mission for user"""
        mission = await self.fetch_one(
            "SELECT * FROM daily_missions WHERE user_id = ? AND mission_date = ?",
            (user_id, mission_date)
        )
        
        if not mission:
            # Create new mission
            import random
            mission_types = ['catch', 'battle', 'fish']
            mission_type = random.choice(mission_types)
            
            requirements = {
                'catch': random.randint(5, 15),
                'battle': random.randint(3, 10),
                'fish': random.randint(3, 8)
            }
            
            mission_id = await self.insert_and_get_id("""
                INSERT INTO daily_missions (user_id, mission_type, requirement, reward_credits, mission_date)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, mission_type, requirements[mission_type], 10000, mission_date))
            
            mission = await self.fetch_one(
                "SELECT * FROM daily_missions WHERE mission_id = ?",
                (mission_id,)
            )
        
        return mission
    
    async def update_mission_progress(self, user_id: int, mission_type: str, progress: int = 1):
        """Update mission progress"""
        today = datetime.now().strftime('%Y-%m-%d')
        
        await self.execute("""
            UPDATE daily_missions 
            SET progress = progress + ?
            WHERE user_id = ? AND mission_type = ? AND mission_date = ?
        """, (progress, user_id, mission_type, today))
        
        # Check if mission is completed
        mission = await self.fetch_one("""
            SELECT * FROM daily_missions 
            WHERE user_id = ? AND mission_type = ? AND mission_date = ?
        """, (user_id, mission_type, today))
        
        if mission and mission['progress'] >= mission['requirement'] and not mission['completed']:
            await self.execute("""
                UPDATE daily_missions 
                SET completed = TRUE 
                WHERE user_id = ? AND mission_type = ? AND mission_date = ?
            """, (user_id, mission_type, today))
    
    # Party management
    async def get_user_party(self, user_id: int) -> List[Dict[str, Any]]:
        """Get user's current party"""
        return await self.fetch_all("""
            SELECT pp.*, ps.name, ps.type1, ps.type2, ps.sprite_url, ps.shiny_sprite_url
            FROM player_party p
            JOIN player_pokemon pp ON p.pokemon_uid = pp.id
            JOIN pokemon_species ps ON pp.pokemon_id = ps.pokemon_id
            WHERE p.user_id = ?
            ORDER BY p.slot
        """, (user_id,))
    
    async def add_pokemon_to_party(self, user_id: int, pokemon_uid: int, slot: int) -> bool:
        """Add Pokemon to party"""
        try:
            await self.execute("""
                INSERT OR REPLACE INTO player_party (user_id, pokemon_uid, slot)
                VALUES (?, ?, ?)
            """, (user_id, pokemon_uid, slot))
            return True
        except Exception as e:
            logger.error(f"Error adding Pokemon to party: {e}")
            return False
    
    async def remove_pokemon_from_party(self, user_id: int, slot: int):
        """Remove Pokemon from party"""
        await self.execute(
            "DELETE FROM player_party WHERE user_id = ? AND slot = ?",
            (user_id, slot)
        )
    
    # Trade management
    async def create_trade(self, initiator_id: int, recipient_id: int) -> int:
        """Create a new trade"""
        trade_id = await self.insert_and_get_id("""
            INSERT INTO trades (initiator_id, recipient_id)
            VALUES (?, ?)
        """, (initiator_id, recipient_id))
        
        return trade_id
    
    async def add_pokemon_to_trade(self, trade_id: int, pokemon_uid: int, offered_by: int, credits: int = 0):
        """Add Pokemon to trade"""
        await self.execute("""
            INSERT INTO trade_pokemon (trade_id, pokemon_uid, offered_by, credits)
            VALUES (?, ?, ?, ?)
        """, (trade_id, pokemon_uid, offered_by, credits))
    
    async def get_trade(self, trade_id: int) -> Optional[Dict[str, Any]]:
        """Get trade details"""
        return await self.fetch_one(
            "SELECT * FROM trades WHERE trade_id = ?",
            (trade_id,)
        )
    
    # Tournament management
    async def create_tournament(self, name: str, tournament_type: str, max_participants: int, 
                               entry_fee: int, created_by: int) -> int:
        """Create a new tournament"""
        tournament_id = await self.insert_and_get_id("""
            INSERT INTO tournaments (name, type, max_participants, entry_fee, prize_pool, created_by)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, tournament_type, max_participants, entry_fee, 
              int(entry_fee * max_participants * 0.8), created_by))
        
        return tournament_id
    
    async def join_tournament(self, tournament_id: int, user_id: int) -> bool:
        """Join a tournament"""
        try:
            await self.execute("""
                INSERT INTO tournament_participants (tournament_id, user_id)
                VALUES (?, ?)
            """, (tournament_id, user_id))
            return True
        except Exception as e:
            logger.error(f"Error joining tournament: {e}")
            return False
    
    # Fishing records
    async def add_fishing_record(self, user_id: int, pokemon_id: int, rod_used: str):
        """Add a fishing record"""
        await self.execute(
            "INSERT INTO fishing_records (user_id, pokemon_id, rod_used) VALUES (?, ?, ?)",
            (user_id, pokemon_id, rod_used)
        )
    
    async def get_fishing_records(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Get user's fishing records"""
        return await self.fetch_all("""
            SELECT fr.*, ps.name, ps.sprite_url
            FROM fishing_records fr
            JOIN pokemon_species ps ON fr.pokemon_id = ps.pokemon_id
            WHERE fr.user_id = ?
            ORDER BY fr.fish_time DESC
            LIMIT ?
        """, (user_id, limit))
    
    # Cleanup methods
    async def cleanup_expired_spawns(self):
        """Clean up expired spawns"""
        await self.execute(
            "DELETE FROM active_spawns WHERE despawn_time < datetime('now')"
        )
    
    async def cleanup_expired_market_listings(self):
        """Clean up expired market listings"""
        await self.execute(
            "DELETE FROM market_listings WHERE expires_date < datetime('now') AND is_sold = FALSE"
        )
    
    async def cleanup_old_battles(self):
        """Clean up old inactive battles"""
        cutoff_time = datetime.now() - timedelta(hours=2)
        await self.execute(
            "DELETE FROM active_battles WHERE last_action < ? AND status = 'active'",
            (cutoff_time,)
        )
