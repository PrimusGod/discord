-- Pokemon Discord Bot Database Schema
-- Comprehensive database structure for all game components

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    discord_id TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    credits INTEGER DEFAULT 0,
    total_exp INTEGER DEFAULT 0,
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_daily TIMESTAMP,
    upvote_points INTEGER DEFAULT 0,
    luck INTEGER DEFAULT 0,
    fishing_level INTEGER DEFAULT 1,
    fishing_exp INTEGER DEFAULT 0
);

-- Pokemon species table (from PokeAPI)
CREATE TABLE IF NOT EXISTS pokemon_species (
    pokemon_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    pokedex_number INTEGER NOT NULL,
    type1 TEXT NOT NULL,
    type2 TEXT,
    base_hp INTEGER NOT NULL,
    base_attack INTEGER NOT NULL,
    base_defense INTEGER NOT NULL,
    base_sp_attack INTEGER NOT NULL,
    base_sp_defense INTEGER NOT NULL,
    base_speed INTEGER NOT NULL,
    height INTEGER NOT NULL,
    weight INTEGER NOT NULL,
    sprite_url TEXT,
    shiny_sprite_url TEXT,
    category TEXT, -- legendary, mythical, ultra_beast, normal
    is_mega BOOLEAN DEFAULT FALSE,
    is_alolan BOOLEAN DEFAULT FALSE,
    is_galarian BOOLEAN DEFAULT FALSE,
    is_hisuian BOOLEAN DEFAULT FALSE,
    is_paldean BOOLEAN DEFAULT FALSE,
    evolution_chain_id INTEGER,
    evolves_from_species_id INTEGER,
    habitat TEXT,
    color TEXT,
    shape TEXT,
    generation INTEGER
);

-- Pokemon moves table
CREATE TABLE IF NOT EXISTS moves (
    move_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL, -- physical, special, status
    power INTEGER,
    accuracy INTEGER,
    pp INTEGER NOT NULL,
    max_pp INTEGER NOT NULL,
    priority INTEGER DEFAULT 0,
    target TEXT NOT NULL, -- user, selected-pokemon, all-opponents, etc
    effect_chance INTEGER,
    effect_description TEXT,
    short_effect TEXT,
    flavor_text TEXT,
    damage_class TEXT,
    crit_rate INTEGER DEFAULT 0,
    drain INTEGER DEFAULT 0,
    healing INTEGER DEFAULT 0,
    ailment TEXT,
    ailment_chance INTEGER DEFAULT 0,
    stat_changes TEXT, -- JSON string of stat changes
    min_hits INTEGER DEFAULT 1,
    max_hits INTEGER DEFAULT 1,
    min_turns INTEGER DEFAULT 1,
    max_turns INTEGER DEFAULT 1
);

-- Pokemon abilities table
CREATE TABLE IF NOT EXISTS abilities (
    ability_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    short_effect TEXT,
    flavor_text TEXT,
    is_hidden BOOLEAN DEFAULT FALSE,
    generation INTEGER
);

-- Items table
CREATE TABLE IF NOT EXISTS items (
    item_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT NOT NULL, -- medicine, pokeballs, battle-items, etc
    cost INTEGER DEFAULT 0,
    description TEXT NOT NULL,
    short_effect TEXT,
    flavor_text TEXT,
    sprite_url TEXT,
    battle_effect TEXT, -- JSON string for battle effects
    field_effect TEXT, -- JSON string for field effects
    pocket TEXT, -- items, medicine, pokeballs, tm, hm, berries, key
    fling_power INTEGER,
    fling_effect TEXT
);

-- Player's Pokemon collection
CREATE TABLE IF NOT EXISTS player_pokemon (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pokemon_id INTEGER NOT NULL,
    nickname TEXT,
    level INTEGER DEFAULT 5,
    exp INTEGER DEFAULT 0,
    hp_iv INTEGER DEFAULT 0,
    attack_iv INTEGER DEFAULT 0,
    defense_iv INTEGER DEFAULT 0,
    sp_attack_iv INTEGER DEFAULT 0,
    sp_defense_iv INTEGER DEFAULT 0,
    speed_iv INTEGER DEFAULT 0,
    hp_ev INTEGER DEFAULT 0,
    attack_ev INTEGER DEFAULT 0,
    defense_ev INTEGER DEFAULT 0,
    sp_attack_ev INTEGER DEFAULT 0,
    sp_defense_ev INTEGER DEFAULT 0,
    speed_ev INTEGER DEFAULT 0,
    current_hp INTEGER,
    max_hp INTEGER,
    is_shiny BOOLEAN DEFAULT FALSE,
    is_radiant BOOLEAN DEFAULT FALSE,
    is_shadow BOOLEAN DEFAULT FALSE,
    ability_id INTEGER,
    nature TEXT DEFAULT 'Hardy',
    friendship INTEGER DEFAULT 0,
    pokerus BOOLEAN DEFAULT FALSE,
    caught_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    caught_location TEXT DEFAULT 'Wild',
    ot_user_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon_species(pokemon_id),
    FOREIGN KEY (ability_id) REFERENCES abilities(ability_id)
);

-- Pokemon movesets (which Pokemon can learn which moves)
CREATE TABLE IF NOT EXISTS pokemon_moves (
    pokemon_id INTEGER NOT NULL,
    move_id INTEGER NOT NULL,
    learn_method TEXT NOT NULL, -- level-up, tm, tr, egg, tutor, evolution
    level_learned INTEGER DEFAULT 0,
    PRIMARY KEY (pokemon_id, move_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon_species(pokemon_id),
    FOREIGN KEY (move_id) REFERENCES moves(move_id)
);

-- Pokemon abilities (which Pokemon have which abilities)
CREATE TABLE IF NOT EXISTS pokemon_abilities (
    pokemon_id INTEGER NOT NULL,
    ability_id INTEGER NOT NULL,
    is_hidden BOOLEAN DEFAULT FALSE,
    slot INTEGER NOT NULL,
    PRIMARY KEY (pokemon_id, ability_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon_species(pokemon_id),
    FOREIGN KEY (ability_id) REFERENCES abilities(ability_id)
);

-- Player's Pokemon party (current team)
CREATE TABLE IF NOT EXISTS player_party (
    user_id INTEGER NOT NULL,
    pokemon_uid INTEGER NOT NULL,
    slot INTEGER NOT NULL,
    PRIMARY KEY (user_id, slot),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (pokemon_uid) REFERENCES player_pokemon(id)
);

-- Player's inventory
CREATE TABLE IF NOT EXISTS player_inventory (
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, item_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (item_id) REFERENCES items(item_id)
);

-- Active spawns
CREATE TABLE IF NOT EXISTS active_spawns (
    spawn_id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    pokemon_id INTEGER NOT NULL,
    is_shiny BOOLEAN DEFAULT FALSE,
    spawn_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    despawn_time TIMESTAMP,
    is_caught BOOLEAN DEFAULT FALSE,
    hint_used BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (pokemon_id) REFERENCES pokemon_species(pokemon_id)
);

-- Active battles
CREATE TABLE IF NOT EXISTS active_battles (
    battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    player1_id INTEGER NOT NULL,
    player2_id INTEGER, -- NULL for NPC battles
    battle_type TEXT NOT NULL, -- wild, trainer, npc, tournament
    status TEXT DEFAULT 'active', -- active, completed, forfeited
    current_turn INTEGER DEFAULT 1,
    turn_player_id INTEGER,
    battle_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_action TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player1_id) REFERENCES users(user_id),
    FOREIGN KEY (player2_id) REFERENCES users(user_id)
);

-- Battle Pokemon (Pokemon currently in battle)
CREATE TABLE IF NOT EXISTS battle_pokemon (
    battle_id INTEGER NOT NULL,
    pokemon_uid INTEGER NOT NULL,
    player_slot INTEGER NOT NULL, -- 1 or 2
    pokemon_slot INTEGER NOT NULL, -- 1-6
    current_hp INTEGER NOT NULL,
    max_hp INTEGER NOT NULL,
    attack INTEGER NOT NULL,
    defense INTEGER NOT NULL,
    sp_attack INTEGER NOT NULL,
    sp_defense INTEGER NOT NULL,
    speed INTEGER NOT NULL,
    status_condition TEXT DEFAULT 'none',
    status_turns INTEGER DEFAULT 0,
    stat_changes TEXT DEFAULT '{}', -- JSON string of stat changes
    moves TEXT NOT NULL, -- JSON string of move IDs
    ability_id INTEGER,
    is_active BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (battle_id, pokemon_uid),
    FOREIGN KEY (battle_id) REFERENCES active_battles(battle_id),
    FOREIGN KEY (pokemon_uid) REFERENCES player_pokemon(id)
);

-- Battle actions log
CREATE TABLE IF NOT EXISTS battle_actions (
    action_id INTEGER PRIMARY KEY AUTOINCREMENT,
    battle_id INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    pokemon_uid INTEGER NOT NULL,
    action_type TEXT NOT NULL, -- move, item, switch, forfeit
    action_details TEXT NOT NULL, -- JSON string of action details
    damage_dealt INTEGER DEFAULT 0,
    damage_received INTEGER DEFAULT 0,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (battle_id) REFERENCES active_battles(battle_id),
    FOREIGN KEY (player_id) REFERENCES users(user_id),
    FOREIGN KEY (pokemon_uid) REFERENCES player_pokemon(id)
);

-- Market listings
CREATE TABLE IF NOT EXISTS market_listings (
    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL,
    pokemon_uid INTEGER NOT NULL,
    price INTEGER NOT NULL,
    listed_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_date TIMESTAMP,
    is_sold BOOLEAN DEFAULT FALSE,
    buyer_id INTEGER,
    sale_date TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users(user_id),
    FOREIGN KEY (buyer_id) REFERENCES users(user_id),
    FOREIGN KEY (pokemon_uid) REFERENCES player_pokemon(id)
);

-- Trades
CREATE TABLE IF NOT EXISTS trades (
    trade_id INTEGER PRIMARY KEY AUTOINCREMENT,
    initiator_id INTEGER NOT NULL,
    recipient_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending', -- pending, accepted, declined, cancelled
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date TIMESTAMP,
    FOREIGN KEY (initiator_id) REFERENCES users(user_id),
    FOREIGN KEY (recipient_id) REFERENCES users(user_id)
);

-- Trade Pokemon
CREATE TABLE IF NOT EXISTS trade_pokemon (
    trade_id INTEGER NOT NULL,
    pokemon_uid INTEGER NOT NULL,
    offered_by INTEGER NOT NULL, -- user_id of who offered this Pokemon
    credits INTEGER DEFAULT 0,
    PRIMARY KEY (trade_id, pokemon_uid),
    FOREIGN KEY (trade_id) REFERENCES trades(trade_id),
    FOREIGN KEY (pokemon_uid) REFERENCES player_pokemon(id),
    FOREIGN KEY (offered_by) REFERENCES users(user_id)
);

-- Daily missions
CREATE TABLE IF NOT EXISTS daily_missions (
    mission_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    mission_type TEXT NOT NULL, -- catch, battle, fish, etc
    requirement INTEGER NOT NULL,
    progress INTEGER DEFAULT 0,
    reward_credits INTEGER DEFAULT 0,
    reward_items TEXT, -- JSON string of item rewards
    completed BOOLEAN DEFAULT FALSE,
    claimed BOOLEAN DEFAULT FALSE,
    mission_date DATE NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Fishing records
CREATE TABLE IF NOT EXISTS fishing_records (
    record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pokemon_id INTEGER NOT NULL,
    fish_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rod_used TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (pokemon_id) REFERENCES pokemon_species(pokemon_id)
);

-- Tournament records
CREATE TABLE IF NOT EXISTS tournaments (
    tournament_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- single_elimination, double_elimination, round_robin
    status TEXT DEFAULT 'registration', -- registration, active, completed
    max_participants INTEGER,
    entry_fee INTEGER DEFAULT 0,
    prize_pool INTEGER DEFAULT 0,
    registration_start TIMESTAMP,
    registration_end TIMESTAMP,
    tournament_start TIMESTAMP,
    created_by INTEGER NOT NULL,
    FOREIGN KEY (created_by) REFERENCES users(user_id)
);

-- Tournament participants
CREATE TABLE IF NOT EXISTS tournament_participants (
    tournament_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'active', -- active, eliminated, winner
    bracket_position INTEGER,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    PRIMARY KEY (tournament_id, user_id),
    FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Tournament battles
CREATE TABLE IF NOT EXISTS tournament_battles (
    battle_id INTEGER NOT NULL,
    tournament_id INTEGER NOT NULL,
    round INTEGER NOT NULL,
    bracket_position INTEGER NOT NULL,
    player1_id INTEGER NOT NULL,
    player2_id INTEGER NOT NULL,
    winner_id INTEGER,
    loser_id INTEGER,
    PRIMARY KEY (battle_id),
    FOREIGN KEY (battle_id) REFERENCES active_battles(battle_id),
    FOREIGN KEY (tournament_id) REFERENCES tournaments(tournament_id),
    FOREIGN KEY (player1_id) REFERENCES users(user_id),
    FOREIGN KEY (player2_id) REFERENCES users(user_id),
    FOREIGN KEY (winner_id) REFERENCES users(user_id),
    FOREIGN KEY (loser_id) REFERENCES users(user_id)
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_pokemon_species_name ON pokemon_species(name);
CREATE INDEX IF NOT EXISTS idx_pokemon_species_type ON pokemon_species(type1, type2);
CREATE INDEX IF NOT EXISTS idx_pokemon_species_category ON pokemon_species(category);
CREATE INDEX IF NOT EXISTS idx_moves_type ON moves(type);
CREATE INDEX IF NOT EXISTS idx_moves_category ON moves(category);
CREATE INDEX IF NOT EXISTS idx_player_pokemon_user ON player_pokemon(user_id);
CREATE INDEX IF NOT EXISTS idx_player_pokemon_pokemon ON player_pokemon(pokemon_id);
CREATE INDEX IF NOT EXISTS idx_active_spawns_channel ON active_spawns(channel_id);
CREATE INDEX IF NOT EXISTS idx_active_battles_status ON active_battles(status);
CREATE INDEX IF NOT EXISTS idx_market_listings_seller ON market_listings(seller_id);
CREATE INDEX IF NOT EXISTS idx_trades_status ON trades(status);
CREATE INDEX IF NOT EXISTS idx_daily_missions_user ON daily_missions(user_id, mission_date);