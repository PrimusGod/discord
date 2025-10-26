import aiohttp
import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from database.db_manager import DatabaseManager

logger = logging.getLogger(__name__)

class PokeAPIClient:
    def __init__(self, db_manager: DatabaseManager):
        self.base_url = "https://pokeapi.co/api/v2"
        self.db = db_manager
        self.session = None
    
    async def initialize(self):
        """Initialize the HTTP session"""
        self.session = aiohttp.ClientSession()
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
    
    async def fetch_pokemon_species(self, pokemon_id: int) -> Optional[Dict[str, Any]]:
        """Fetch Pokemon species data from PokeAPI"""
        try:
            async with self.session.get(f"{self.base_url}/pokemon-species/{pokemon_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch Pokemon species {pokemon_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching Pokemon species {pokemon_id}: {e}")
            return None
    
    async def fetch_pokemon(self, pokemon_id: int) -> Optional[Dict[str, Any]]:
        """Fetch Pokemon data from PokeAPI"""
        try:
            async with self.session.get(f"{self.base_url}/pokemon/{pokemon_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch Pokemon {pokemon_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching Pokemon {pokemon_id}: {e}")
            return None
    
    async def fetch_move(self, move_id: int) -> Optional[Dict[str, Any]]:
        """Fetch move data from PokeAPI"""
        try:
            async with self.session.get(f"{self.base_url}/move/{move_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch move {move_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching move {move_id}: {e}")
            return None
    
    async def fetch_ability(self, ability_id: int) -> Optional[Dict[str, Any]]:
        """Fetch ability data from PokeAPI"""
        try:
            async with self.session.get(f"{self.base_url}/ability/{ability_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch ability {ability_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching ability {ability_id}: {e}")
            return None
    
    async def fetch_item(self, item_id: int) -> Optional[Dict[str, Any]]:
        """Fetch item data from PokeAPI"""
        try:
            async with self.session.get(f"{self.base_url}/item/{item_id}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch item {item_id}: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching item {item_id}: {e}")
            return None
    
    async def fetch_pokemon_list(self, limit: int = 1000, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Fetch Pokemon list from PokeAPI"""
        try:
            async with self.session.get(f"{self.base_url}/pokemon?limit={limit}&offset={offset}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch Pokemon list: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching Pokemon list: {e}")
            return None
    
    async def fetch_move_list(self, limit: int = 1000, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Fetch move list from PokeAPI"""
        try:
            async with self.session.get(f"{self.base_url}/move?limit={limit}&offset={offset}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch move list: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching move list: {e}")
            return None
    
    async def fetch_ability_list(self, limit: int = 1000, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Fetch ability list from PokeAPI"""
        try:
            async with self.session.get(f"{self.base_url}/ability?limit={limit}&offset={offset}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch ability list: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching ability list: {e}")
            return None
    
    async def fetch_item_list(self, limit: int = 1000, offset: int = 0) -> Optional[Dict[str, Any]]:
        """Fetch item list from PokeAPI"""
        try:
            async with self.session.get(f"{self.base_url}/item?limit={limit}&offset={offset}") as response:
                if response.status == 200:
                    return await response.json()
                else:
                    logger.error(f"Failed to fetch item list: {response.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching item list: {e}")
            return None
    
    async def populate_pokemon_database(self, start_id: int = 1, end_id: int = 1008):
        """Populate the database with Pokemon data"""
        logger.info(f"Starting Pokemon database population from {start_id} to {end_id}")
        
        for pokemon_id in range(start_id, end_id + 1):
            try:
                # Fetch Pokemon data
                pokemon_data = await self.fetch_pokemon(pokemon_id)
                species_data = await self.fetch_pokemon_species(pokemon_id)
                
                if not pokemon_data or not species_data:
                    logger.warning(f"Skipping Pokemon {pokemon_id} due to missing data")
                    continue
                
                # Extract Pokemon information
                pokemon_info = self._extract_pokemon_info(pokemon_data, species_data)
                
                # Insert into database
                await self.db.execute("""
                    INSERT OR REPLACE INTO pokemon_species (
                        pokemon_id, name, pokedex_number, type1, type2,
                        base_hp, base_attack, base_defense, base_sp_attack, base_sp_defense, base_speed,
                        height, weight, sprite_url, shiny_sprite_url, category, generation
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    pokemon_info['id'],
                    pokemon_info['name'],
                    pokemon_info['pokedex_number'],
                    pokemon_info['type1'],
                    pokemon_info['type2'],
                    pokemon_info['base_hp'],
                    pokemon_info['base_attack'],
                    pokemon_info['base_defense'],
                    pokemon_info['base_sp_attack'],
                    pokemon_info['base_sp_defense'],
                    pokemon_info['base_speed'],
                    pokemon_info['height'],
                    pokemon_info['weight'],
                    pokemon_info['sprite_url'],
                    pokemon_info['shiny_sprite_url'],
                    pokemon_info['category'],
                    pokemon_info['generation']
                ))
                
                # Add moves
                for move_data in pokemon_data.get('moves', []):
                    move_name = move_data['move']['name']
                    move_id = move_data['move']['url'].split('/')[-2]
                    
                    # Get the first version group details
                    version_details = move_data.get('version_group_details', [])
                    if version_details:
                        learn_method = version_details[0]['move_learn_method']['name']
                        level_learned = version_details[0]['level_learned_at']
                        
                        await self.db.execute("""
                            INSERT OR IGNORE INTO pokemon_moves (pokemon_id, move_id, learn_method, level_learned)
                            VALUES (?, ?, ?, ?)
                        """, (pokemon_id, move_id, learn_method, level_learned))
                
                # Add abilities
                for ability_data in pokemon_data.get('abilities', []):
                    ability_name = ability_data['ability']['name']
                    ability_id = ability_data['ability']['url'].split('/')[-2]
                    is_hidden = ability_data['is_hidden']
                    slot = ability_data['slot']
                    
                    await self.db.execute("""
                        INSERT OR IGNORE INTO pokemon_abilities (pokemon_id, ability_id, is_hidden, slot)
                        VALUES (?, ?, ?, ?)
                    """, (pokemon_id, ability_id, is_hidden, slot))
                
                logger.info(f"Successfully populated Pokemon {pokemon_id}: {pokemon_info['name']}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error populating Pokemon {pokemon_id}: {e}")
                continue
        
        logger.info("Pokemon database population completed")
    
    def _extract_pokemon_info(self, pokemon_data: Dict[str, Any], species_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant Pokemon information from API data"""
        # Basic info
        pokemon_id = pokemon_data['id']
        name = pokemon_data['name'].title()
        
        # Types
        types = pokemon_data.get('types', [])
        type1 = types[0]['type']['name'].title() if types else 'Normal'
        type2 = types[1]['type']['name'].title() if len(types) > 1 else None
        
        # Stats
        stats = {stat['stat']['name']: stat['base_stat'] for stat in pokemon_data.get('stats', [])}
        
        # Sprites
        sprite_url = pokemon_data['sprites']['front_default']
        shiny_sprite_url = pokemon_data['sprites']['front_shiny']
        
        # Category (legendary, mythical, etc)
        category = 'normal'
        if species_data.get('is_legendary'):
            category = 'legendary'
        elif species_data.get('is_mythical'):
            category = 'mythical'
        
        # Generation
        generation = species_data.get('generation', {}).get('url', '').split('/')[-2]
        generation = int(generation) if generation.isdigit() else 1
        
        return {
            'id': pokemon_id,
            'name': name,
            'pokedex_number': pokemon_id,
            'type1': type1,
            'type2': type2,
            'base_hp': stats.get('hp', 50),
            'base_attack': stats.get('attack', 50),
            'base_defense': stats.get('defense', 50),
            'base_sp_attack': stats.get('special-attack', 50),
            'base_sp_defense': stats.get('special-defense', 50),
            'base_speed': stats.get('speed', 50),
            'height': pokemon_data.get('height', 0),
            'weight': pokemon_data.get('weight', 0),
            'sprite_url': sprite_url,
            'shiny_sprite_url': shiny_sprite_url,
            'category': category,
            'generation': generation
        }
    
    async def populate_moves_database(self, start_id: int = 1, end_id: int = 1000):
        """Populate the database with move data"""
        logger.info(f"Starting moves database population from {start_id} to {end_id}")
        
        for move_id in range(start_id, end_id + 1):
            try:
                move_data = await self.fetch_move(move_id)
                
                if not move_data:
                    logger.warning(f"Skipping move {move_id} due to missing data")
                    continue
                
                # Extract move information
                move_info = self._extract_move_info(move_data)
                
                # Insert into database
                await self.db.execute("""
                    INSERT OR REPLACE INTO moves (
                        move_id, name, type, category, power, accuracy, pp, max_pp,
                        priority, target, effect_chance, effect_description, short_effect,
                        flavor_text, damage_class, min_hits, max_hits, min_turns, max_turns
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    move_info['id'],
                    move_info['name'],
                    move_info['type'],
                    move_info['category'],
                    move_info['power'],
                    move_info['accuracy'],
                    move_info['pp'],
                    move_info['max_pp'],
                    move_info['priority'],
                    move_info['target'],
                    move_info['effect_chance'],
                    move_info['effect_description'],
                    move_info['short_effect'],
                    move_info['flavor_text'],
                    move_info['damage_class'],
                    move_info['min_hits'],
                    move_info['max_hits'],
                    move_info['min_turns'],
                    move_info['max_turns']
                ))
                
                logger.info(f"Successfully populated move {move_id}: {move_info['name']}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Error populating move {move_id}: {e}")
                continue
        
        logger.info("Moves database population completed")
    
    def _extract_move_info(self, move_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant move information from API data"""
        return {
            'id': move_data['id'],
            'name': move_data['name'].replace('-', ' ').title(),
            'type': move_data['type']['name'].title(),
            'category': move_data['damage_class']['name'],
            'power': move_data.get('power'),
            'accuracy': move_data.get('accuracy'),
            'pp': move_data.get('pp', 0),
            'max_pp': move_data.get('pp', 0),
            'priority': move_data.get('priority', 0),
            'target': move_data['target']['name'],
            'effect_chance': move_data.get('effect_chance'),
            'effect_description': move_data['effect_entries'][0]['effect'] if move_data.get('effect_entries') else '',
            'short_effect': move_data['effect_entries'][0]['short_effect'] if move_data.get('effect_entries') else '',
            'flavor_text': move_data['flavor_text_entries'][0]['flavor_text'] if move_data.get('flavor_text_entries') else '',
            'damage_class': move_data['damage_class']['name'],
            'min_hits': move_data.get('meta', {}).get('min_hits', 1),
            'max_hits': move_data.get('meta', {}).get('max_hits', 1),
            'min_turns': move_data.get('meta', {}).get('min_turns', 1),
            'max_turns': move_data.get('meta', {}).get('max_turns', 1)
        }
    
    async def populate_abilities_database(self, start_id: int = 1, end_id: int = 300):
        """Populate the database with ability data"""
        logger.info(f"Starting abilities database population from {start_id} to {end_id}")
        
        for ability_id in range(start_id, end_id + 1):
            try:
                ability_data = await self.fetch_ability(ability_id)
                
                if not ability_data:
                    logger.warning(f"Skipping ability {ability_id} due to missing data")
                    continue
                
                # Extract ability information
                ability_info = self._extract_ability_info(ability_data)
                
                # Insert into database
                await self.db.execute("""
                    INSERT OR REPLACE INTO abilities (
                        ability_id, name, description, short_effect, flavor_text, generation
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    ability_info['id'],
                    ability_info['name'],
                    ability_info['description'],
                    ability_info['short_effect'],
                    ability_info['flavor_text'],
                    ability_info['generation']
                ))
                
                logger.info(f"Successfully populated ability {ability_id}: {ability_info['name']}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Error populating ability {ability_id}: {e}")
                continue
        
        logger.info("Abilities database population completed")
    
    def _extract_ability_info(self, ability_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant ability information from API data"""
        return {
            'id': ability_data['id'],
            'name': ability_data['name'].replace('-', ' ').title(),
            'description': ability_data['effect_entries'][0]['effect'] if ability_data.get('effect_entries') else '',
            'short_effect': ability_data['effect_entries'][0]['short_effect'] if ability_data.get('effect_entries') else '',
            'flavor_text': ability_data['flavor_text_entries'][0]['flavor_text'] if ability_data.get('flavor_text_entries') else '',
            'generation': ability_data.get('generation', {}).get('url', '').split('/')[-2]
        }
    
    async def populate_items_database(self, start_id: int = 1, end_id: int = 1000):
        """Populate the database with item data"""
        logger.info(f"Starting items database population from {start_id} to {end_id}")
        
        for item_id in range(start_id, end_id + 1):
            try:
                item_data = await self.fetch_item(item_id)
                
                if not item_data:
                    logger.warning(f"Skipping item {item_id} due to missing data")
                    continue
                
                # Extract item information
                item_info = self._extract_item_info(item_data)
                
                # Insert into database
                await self.db.execute("""
                    INSERT OR REPLACE INTO items (
                        item_id, name, category, cost, description, short_effect,
                        flavor_text, sprite_url, pocket
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    item_info['id'],
                    item_info['name'],
                    item_info['category'],
                    item_info['cost'],
                    item_info['description'],
                    item_info['short_effect'],
                    item_info['flavor_text'],
                    item_info['sprite_url'],
                    item_info['pocket']
                ))
                
                logger.info(f"Successfully populated item {item_id}: {item_info['name']}")
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.05)
                
            except Exception as e:
                logger.error(f"Error populating item {item_id}: {e}")
                continue
        
        logger.info("Items database population completed")
    
    def _extract_item_info(self, item_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant item information from API data"""
        return {
            'id': item_data['id'],
            'name': item_data['name'].replace('-', ' ').title(),
            'category': item_data['category']['name'],
            'cost': item_data.get('cost', 0),
            'description': item_data['effect_entries'][0]['effect'] if item_data.get('effect_entries') else '',
            'short_effect': item_data['effect_entries'][0]['short_effect'] if item_data.get('effect_entries') else '',
            'flavor_text': item_data['flavor_text_entries'][0]['flavor_text'] if item_data.get('flavor_text_entries') else '',
            'sprite_url': item_data['sprites']['default'],
            'pocket': item_data.get('pocket', {}).get('name', 'items')
        }
    
    async def populate_all_databases(self):
        """Populate all databases with data from PokeAPI"""
        logger.info("Starting complete database population")
        
        try:
            # Populate Pokemon
            await self.populate_pokemon_database(1, 1008)
            
            # Populate moves
            await self.populate_moves_database(1, 1000)
            
            # Populate abilities
            await self.populate_abilities_database(1, 300)
            
            # Populate items
            await self.populate_items_database(1, 1000)
            
            logger.info("Complete database population finished successfully")
            
        except Exception as e:
            logger.error(f"Error during database population: {e}")
            raise