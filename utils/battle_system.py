import discord
import random
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BattleSystem:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.active_battles = {}
        self.status_effects = {
            'burn': {'damage': 0.125, 'attack_multiplier': 0.5},
            'poison': {'damage': 0.125},
            'toxic': {'damage': 0.125, 'increasing': True},
            'paralysis': {'speed_multiplier': 0.25, 'paralyze_chance': 0.25},
            'sleep': {'duration': (1, 3), 'cant_move': True},
            'freeze': {'thaw_chance': 0.2, 'cant_move': True},
            'confusion': {'duration': (1, 4), 'hurt_chance': 0.33},
            'flinch': {'duration': 1, 'cant_move': True}
        }
        self.type_effectiveness = {
            'Normal': {'Rock': 0.5, 'Ghost': 0, 'Steel': 0.5},
            'Fire': {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 2, 'Bug': 2, 'Rock': 0.5, 'Dragon': 0.5, 'Steel': 2},
            'Water': {'Fire': 2, 'Water': 0.5, 'Grass': 0.5, 'Ground': 2, 'Rock': 2, 'Dragon': 0.5},
            'Electric': {'Water': 2, 'Electric': 0.5, 'Grass': 0.5, 'Ground': 0, 'Flying': 2, 'Dragon': 0.5},
            'Grass': {'Fire': 0.5, 'Water': 2, 'Grass': 0.5, 'Poison': 0.5, 'Ground': 2, 'Flying': 0.5, 'Bug': 0.5, 'Rock': 2, 'Dragon': 0.5, 'Steel': 0.5},
            'Ice': {'Fire': 0.5, 'Water': 0.5, 'Grass': 2, 'Ice': 0.5, 'Ground': 2, 'Flying': 2, 'Dragon': 2, 'Steel': 0.5},
            'Fighting': {'Normal': 2, 'Ice': 2, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 0.5, 'Bug': 0.5, 'Rock': 2, 'Ghost': 0, 'Dark': 2, 'Steel': 2, 'Fairy': 0.5},
            'Poison': {'Grass': 2, 'Poison': 0.5, 'Ground': 0.5, 'Rock': 0.5, 'Ghost': 0.5, 'Steel': 0, 'Fairy': 2},
            'Ground': {'Fire': 2, 'Electric': 2, 'Grass': 0.5, 'Poison': 2, 'Flying': 0, 'Bug': 0.5, 'Rock': 2, 'Steel': 2},
            'Flying': {'Electric': 0.5, 'Grass': 2, 'Fighting': 2, 'Bug': 2, 'Rock': 0.5, 'Steel': 0.5},
            'Psychic': {'Fighting': 2, 'Poison': 2, 'Psychic': 0.5, 'Dark': 0, 'Steel': 0.5},
            'Bug': {'Fire': 0.5, 'Grass': 2, 'Fighting': 0.5, 'Poison': 0.5, 'Flying': 0.5, 'Psychic': 2, 'Ghost': 0.5, 'Dark': 2, 'Steel': 0.5, 'Fairy': 0.5},
            'Rock': {'Fire': 2, 'Ice': 2, 'Fighting': 0.5, 'Ground': 0.5, 'Flying': 2, 'Bug': 2, 'Steel': 0.5},
            'Ghost': {'Normal': 0, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5},
            'Dragon': {'Dragon': 2, 'Steel': 0.5, 'Fairy': 0},
            'Dark': {'Fighting': 0.5, 'Psychic': 2, 'Ghost': 2, 'Dark': 0.5, 'Fairy': 0.5},
            'Steel': {'Fire': 0.5, 'Water': 0.5, 'Electric': 0.5, 'Ice': 2, 'Rock': 2, 'Steel': 0.5, 'Fairy': 2},
            'Fairy': {'Fire': 0.5, 'Fighting': 2, 'Poison': 0.5, 'Dragon': 2, 'Dark': 2, 'Steel': 0.5}
        }
    
    async def create_battle(self, player1_id: int, player2_id: int, battle_type: str, channel_id: str) -> int:
        """Create a new battle"""
        battle_id = await self.db.create_battle(player1_id, player2_id, battle_type, channel_id)
        
        # Get player parties
        player1_party = await self.db.get_user_party(player1_id)
        player2_party = await self.db.get_user_party(player2_id)
        
        if not player1_party or not player2_party:
            raise ValueError("One or both players don't have a party")
        
        # Initialize battle state
        battle_state = {
            'battle_id': battle_id,
            'player1_id': player1_id,
            'player2_id': player2_id,
            'player1_party': player1_party,
            'player2_party': player2_party,
            'current_turn': 1,
            'turn_player_id': player1_id,
            'battle_log': [],
            'weather': None,
            'terrain': None,
            'player1_active_pokemon': 0,
            'player2_active_pokemon': 0
        }
        
        self.active_battles[battle_id] = battle_state
        
        return battle_id
    
    async def process_turn(self, battle_id: int, player_id: int, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process a turn in battle"""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return {'error': 'Battle not found'}
        
        if battle['turn_player_id'] != player_id:
            return {'error': 'Not your turn'}
        
        result = {'success': True, 'actions': [], 'battle_over': False}
        
        try:
            if action['type'] == 'move':
                result = await self._process_move_action(battle_id, player_id, action)
            elif action['type'] == 'switch':
                result = await self._process_switch_action(battle_id, player_id, action)
            elif action['type'] == 'item':
                result = await self._process_item_action(battle_id, player_id, action)
            elif action['type'] == 'forfeit':
                result = await self._process_forfeit_action(battle_id, player_id)
            
            # Check if battle is over
            if await self._check_battle_over(battle_id):
                result['battle_over'] = True
                result['winner'] = await self._determine_winner(battle_id)
                await self._end_battle(battle_id)
            else:
                # Switch turns
                battle['turn_player_id'] = battle['player2_id'] if player_id == battle['player1_id'] else battle['player1_id']
                battle['current_turn'] += 1
            
        except Exception as e:
            logger.error(f"Error processing turn: {e}")
            result = {'error': 'Error processing turn'}
        
        return result
    
    async def _process_move_action(self, battle_id: int, player_id: int, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process a move action"""
        battle = self.active_battles[battle_id]
        
        # Get active Pokemon
        active_pokemon = self._get_active_pokemon(battle, player_id)
        opponent_pokemon = self._get_opponent_pokemon(battle, player_id)
        
        # Get move details
        move_id = action['move_id']
        move = await self.db.fetch_one("SELECT * FROM moves WHERE move_id = ?", (move_id,))
        
        if not move:
            return {'error': 'Move not found'}
        
        # Check if Pokemon can move (status conditions)
        if not await self._can_pokemon_move(active_pokemon):
            return {'success': True, 'actions': [f"{active_pokemon['name']} is unable to move!"]}
        
        # Calculate move effects
        results = []
        
        if move['category'] == 'status':
            results.append(await self._process_status_move(active_pokemon, opponent_pokemon, move))
        else:
            results.append(await self._process_damage_move(active_pokemon, opponent_pokemon, move))
        
        # Process status effects
        await self._process_status_effects(active_pokemon, opponent_pokemon)
        
        return {'success': True, 'actions': results}
    
    async def _process_damage_move(self, attacker: Dict[str, Any], defender: Dict[str, Any], move: Dict[str, Any]) -> str:
        """Process a damage-dealing move"""
        # Calculate accuracy check
        if move['accuracy'] and random.random() > move['accuracy'] / 100:
            return f"{attacker['name']}'s {move['name']} missed!"
        
        # Calculate damage
        damage = self._calculate_damage(attacker, defender, move)
        
        # Apply type effectiveness
        type_effectiveness = self._get_type_effectiveness(move['type'], defender['type1'], defender.get('type2'))
        damage = int(damage * type_effectiveness)
        
        # Critical hit
        is_critical = random.random() < 0.0625  # 6.25% base chance
        if is_critical:
            damage = int(damage * 1.5)
        
        # Apply damage
        defender['current_hp'] = max(0, defender['current_hp'] - damage)
        
        # Build result message
        result = f"{attacker['name']} used {move['name']}"
        
        if is_critical:
            result += "! A critical hit!"
        
        if type_effectiveness > 1:
            result += " It's super effective!"
        elif type_effectiveness < 1:
            result += " It's not very effective..."
        elif type_effectiveness == 0:
            result += " It had no effect!"
        
        result += f" ({defender['name']} took {damage} damage)"
        
        # Apply secondary effects
        if move['effect_chance'] and random.random() < move['effect_chance'] / 100:
            if move['ailment']:
                defender['status_condition'] = move['ailment']
                result += f" {defender['name']} was {move['ailment']}!"
        
        return result
    
    def _calculate_damage(self, attacker: Dict[str, Any], defender: Dict[str, Any], move: Dict[str, Any]) -> int:
        """Calculate damage using Pokemon damage formula"""
        if move['power'] is None:
            return 0
        
        # Get attacking and defending stats
        if move['category'] == 'physical':
            attack_stat = attacker['attack']
            defense_stat = defender['defense']
        else:  # special
            attack_stat = attacker['sp_attack']
            defense_stat = defender['sp_defense']
        
        # Level
        level = attacker['level']
        
        # Base damage calculation (simplified)
        damage = int((((2 * level / 5 + 2) * move['power'] * attack_stat / defense_stat) / 50) + 2)
        
        # STAB (Same Type Attack Bonus)
        if move['type'] in [attacker['type1'], attacker.get('type2')]:
            damage = int(damage * 1.5)
        
        # Random variation (85-100%)
        damage = int(damage * random.uniform(0.85, 1.0))
        
        return max(1, damage)
    
    def _get_type_effectiveness(self, move_type: str, defender_type1: str, defender_type2: Optional[str] = None) -> float:
        """Calculate type effectiveness"""
        effectiveness = 1.0
        
        # Check against first type
        if move_type in self.type_effectiveness:
            type_matchups = self.type_effectiveness[move_type]
            if defender_type1 in type_matchups:
                effectiveness *= type_matchups[defender_type1]
        
        # Check against second type
        if defender_type2 and move_type in self.type_effectiveness:
            type_matchups = self.type_effectiveness[move_type]
            if defender_type2 in type_matchups:
                effectiveness *= type_matchups[defender_type2]
        
        return effectiveness
    
    async def _process_status_move(self, attacker: Dict[str, Any], defender: Dict[str, Any], move: Dict[str, Any]) -> str:
        """Process a status move"""
        # This is a simplified implementation
        # In a full implementation, you'd handle specific status effects
        result = f"{attacker['name']} used {move['name']}"
        
        if move['ailment']:
            defender['status_condition'] = move['ailment']
            result += f" {defender['name']} was {move['ailment']}!"
        
        return result
    
    async def _process_switch_action(self, battle_id: int, player_id: int, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process a Pokemon switch action"""
        battle = self.active_battles[battle_id]
        
        # Get the party
        party = battle['player1_party'] if player_id == battle['player1_id'] else battle['player2_party']
        
        # Validate switch
        new_pokemon_index = action['pokemon_index']
        if new_pokemon_index >= len(party) or new_pokemon_index < 0:
            return {'error': 'Invalid Pokemon index'}
        
        # Update active Pokemon
        if player_id == battle['player1_id']:
            battle['player1_active_pokemon'] = new_pokemon_index
        else:
            battle['player2_active_pokemon'] = new_pokemon_index
        
        new_pokemon = party[new_pokemon_index]
        
        return {
            'success': True,
            'actions': [f"Switched to {new_pokemon['name']}!"]
        }
    
    async def _process_item_action(self, battle_id: int, player_id: int, action: Dict[str, Any]) -> Dict[str, Any]:
        """Process an item usage action"""
        # Simplified implementation
        item_id = action['item_id']
        target_pokemon = action['target_pokemon']
        
        # Remove item from inventory
        success = await self.db.remove_item_from_inventory(player_id, item_id)
        
        if not success:
            return {'error': 'Item not found in inventory'}
        
        # Apply item effect (simplified)
        return {
            'success': True,
            'actions': [f"Used item on {target_pokemon['name']}!"]
        }
    
    async def _process_forfeit_action(self, battle_id: int, player_id: int) -> Dict[str, Any]:
        """Process a forfeit action"""
        battle = self.active_battles[battle_id]
        
        # Determine winner
        winner_id = battle['player2_id'] if player_id == battle['player1_id'] else battle['player1_id']
        
        # End battle
        await self._end_battle(battle_id)
        
        return {
            'success': True,
            'actions': [f"Battle forfeited! Winner: {winner_id}"],
            'battle_over': True,
            'winner': winner_id
        }
    
    async def _can_pokemon_move(self, pokemon: Dict[str, Any]) -> bool:
        """Check if Pokemon can move (status condition effects)"""
        status = pokemon.get('status_condition')
        
        if not status:
            return True
        
        if status in ['sleep', 'freeze', 'paralysis']:
            # Check status-specific effects
            if status == 'paralysis' and random.random() < 0.25:
                return False
            elif status in ['sleep', 'freeze']:
                return False
        
        return True
    
    async def _process_status_effects(self, pokemon: Dict[str, Any], opponent: Dict[str, Any]):
        """Process status effects at the end of turn"""
        status = pokemon.get('status_condition')
        
        if status in self.status_effects:
            effect = self.status_effects[status]
            
            # Damage from status
            if 'damage' in effect:
                damage = int(pokemon['max_hp'] * effect['damage'])
                pokemon['current_hp'] = max(0, pokemon['current_hp'] - damage)
            
            # Stat modifications
            if 'attack_multiplier' in effect:
                pokemon['attack'] = int(pokemon['attack'] * effect['attack_multiplier'])
    
    def _get_active_pokemon(self, battle: Dict[str, Any], player_id: int) -> Dict[str, Any]:
        """Get the active Pokemon for a player"""
        party = battle['player1_party'] if player_id == battle['player1_id'] else battle['player2_party']
        active_index = battle['player1_active_pokemon'] if player_id == battle['player1_id'] else battle['player2_active_pokemon']
        return party[active_index]
    
    def _get_opponent_pokemon(self, battle: Dict[str, Any], player_id: int) -> Dict[str, Any]:
        """Get the opponent's active Pokemon"""
        opponent_id = battle['player2_id'] if player_id == battle['player1_id'] else battle['player1_id']
        return self._get_active_pokemon(battle, opponent_id)
    
    async def _check_battle_over(self, battle_id: int) -> bool:
        """Check if battle is over"""
        battle = self.active_battles[battle_id]
        
        # Check if any player has no Pokemon left
        player1_has_pokemon = any(p['current_hp'] > 0 for p in battle['player1_party'])
        player2_has_pokemon = any(p['current_hp'] > 0 for p in battle['player2_party'])
        
        return not player1_has_pokemon or not player2_has_pokemon
    
    async def _determine_winner(self, battle_id: int) -> int:
        """Determine the winner of the battle"""
        battle = self.active_battles[battle_id]
        
        player1_has_pokemon = any(p['current_hp'] > 0 for p in battle['player1_party'])
        player2_has_pokemon = any(p['current_hp'] > 0 for p in battle['player2_party'])
        
        if player1_has_pokemon:
            return battle['player1_id']
        else:
            return battle['player2_id']
    
    async def _end_battle(self, battle_id: int):
        """End a battle and distribute rewards"""
        battle = self.active_battles[battle_id]
        
        # Remove from active battles
        if battle_id in self.active_battles:
            del self.active_battles[battle_id]
        
        # Update battle status in database
        await self.db.execute(
            "UPDATE active_battles SET status = 'completed' WHERE battle_id = ?",
            (battle_id,)
        )
        
        logger.info(f"Battle {battle_id} ended")
    
    async def get_battle_embed(self, battle_id: int) -> discord.Embed:
        """Create an embed showing the current battle state"""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return discord.Embed(title="Battle not found", color=discord.Color.red())
        
        embed = discord.Embed(
            title=f"Battle #{battle_id}",
            description=f"Turn {battle['current_turn']}",
            color=discord.Color.blue()
        )
        
        # Show active Pokemon for both players
        player1_pokemon = self._get_active_pokemon(battle, battle['player1_id'])
        player2_pokemon = self._get_active_pokemon(battle, battle['player2_id'])
        
        # Player 1's Pokemon
        player1_info = f"**{player1_pokemon['name']}** (Lv. {player1_pokemon['level']})\n"
        player1_info += f"HP: {player1_pokemon['current_hp']}/{player1_pokemon['max_hp']}\n"
        if player1_pokemon.get('status_condition'):
            player1_info += f"Status: {player1_pokemon['status_condition'].title()}\n"
        
        # Player 2's Pokemon
        player2_info = f"**{player2_pokemon['name']}** (Lv. {player2_pokemon['level']})\n"
        player2_info += f"HP: {player2_pokemon['current_hp']}/{player2_pokemon['max_hp']}\n"
        if player2_pokemon.get('status_condition'):
            player2_info += f"Status: {player2_pokemon['status_condition'].title()}\n"
        
        embed.add_field(name="Player 1", value=player1_info, inline=True)
        embed.add_field(name="Player 2", value=player2_info, inline=True)
        
        # Show whose turn it is
        current_player = battle['turn_player_id']
        embed.set_footer(text=f"It's Player {current_player}'s turn")
        
        return embed