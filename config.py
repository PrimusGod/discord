import json
import os

class Config:
    def __init__(self):
        self.token = os.getenv('DISCORD_TOKEN', 'your-bot-token-here')
        self.client_id = os.getenv('CLIENT_ID', 'your-client-id-here')
        self.database_path = 'data/pokemon_database.db'
        self.spawn_rate = 0.05  # 5% chance per message
        self.despawn_time = 2400  # 40 minutes in seconds
        self.max_spawns_per_channel = 3
        self.battle_timeout = 180  # 3 minutes
        self.trade_timeout = 300  # 5 minutes
        self.daily_credits = 100
        self.catch_credits = 10
        self.battle_win_credits = 50
        self.mission_credits = 10000
        
        # Game balance settings
        self.shiny_rate = 0.0001  # 0.01%
        self.legendary_rate = 0.0005  # 0.05%
        self.mythical_rate = 0.0002  # 0.02%
        self.ultra_beast_rate = 0.0003  # 0.03%
        
        # Experience settings
        self.catch_exp = 10
        self.battle_win_exp = 50
        self.battle_lose_exp = 10
        self.npc_battle_exp = 25
        
        # Fishing settings
        self.fish_cooldown = 300  # 5 minutes
        self.fish_exp_rate = 0.5
        
        # Market settings
        self.market_tax = 0.05  # 5% tax
        self.max_listing_days = 7
        
        # Tournament settings
        self.tournament_entry_fee = 1000
        self.tournament_prize_pool = 0.8  # 80% goes to prize pool
        
    def save_config(self, filepath='config.json'):
        config_data = {
            'token': self.token,
            'client_id': self.client_id,
            'database_path': self.database_path,
            'spawn_rate': self.spawn_rate,
            'despawn_time': self.despawn_time,
            'max_spawns_per_channel': self.max_spawns_per_channel,
            'battle_timeout': self.battle_timeout,
            'trade_timeout': self.trade_timeout,
            'daily_credits': self.daily_credits,
            'catch_credits': self.catch_credits,
            'battle_win_credits': self.battle_win_credits,
            'mission_credits': self.mission_credits,
            'shiny_rate': self.shiny_rate,
            'legendary_rate': self.legendary_rate,
            'mythical_rate': self.mythical_rate,
            'ultra_beast_rate': self.ultra_beast_rate,
            'catch_exp': self.catch_exp,
            'battle_win_exp': self.battle_win_exp,
            'battle_lose_exp': self.battle_lose_exp,
            'npc_battle_exp': self.npc_battle_exp,
            'fish_cooldown': self.fish_cooldown,
            'fish_exp_rate': self.fish_exp_rate,
            'market_tax': self.market_tax,
            'max_listing_days': self.max_listing_days,
            'tournament_entry_fee': self.tournament_entry_fee,
            'tournament_prize_pool': self.tournament_prize_pool
        }
        
        with open(filepath, 'w') as f:
            json.dump(config_data, f, indent=4)
    
    def load_config(self, filepath='config.json'):
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                config_data = json.load(f)
                
            for key, value in config_data.items():
                if hasattr(self, key):
                    setattr(self, key, value)