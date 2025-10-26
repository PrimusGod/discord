import discord
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class TournamentSystem:
    def __init__(self, db, config):
        self.db = db
        self.config = config
        self.active_tournaments = {}
    
    async def create_tournament(self, name: str, tournament_type: str, max_participants: int, 
                               entry_fee: int, created_by: int) -> int:
        """Create a new tournament"""
        try:
            tournament_id = await self.db.create_tournament(
                name, tournament_type, max_participants, entry_fee, created_by
            )
            return tournament_id
        except Exception as e:
            logger.error(f"Error creating tournament: {e}")
            return 0
    
    async def join_tournament(self, tournament_id: int, user_id: int) -> Dict[str, any]:
        """Join a tournament"""
        try:
            # Check tournament exists and is open
            tournament = await self.db.fetch_one(
                "SELECT * FROM tournaments WHERE tournament_id = ?",
                (tournament_id,)
            )
            
            if not tournament:
                return {
                    'success': False,
                    'error': 'Tournament not found'
                }
            
            if tournament['status'] != 'registration':
                return {
                    'success': False,
                    'error': 'Tournament registration is closed'
                }
            
            # Check if already registered
            existing = await self.db.fetch_one(
                "SELECT * FROM tournament_participants WHERE tournament_id = ? AND user_id = ?",
                (tournament_id, user_id)
            )
            
            if existing:
                return {
                    'success': False,
                    'error': 'Already registered for this tournament'
                }
            
            # Check participant limit
            participant_count = await self.db.fetch_val(
                "SELECT COUNT(*) FROM tournament_participants WHERE tournament_id = ?",
                (tournament_id,)
            )
            
            if participant_count >= tournament['max_participants']:
                return {
                    'success': False,
                    'error': 'Tournament is full'
                }
            
            # Deduct entry fee if applicable
            if tournament['entry_fee'] > 0:
                user = await self.db.fetch_one(
                    "SELECT credits FROM users WHERE user_id = ?",
                    (user_id,)
                )
                
                if not user or user['credits'] < tournament['entry_fee']:
                    return {
                        'success': False,
                        'error': 'Insufficient credits for entry fee'
                    }
                
                await self.db.update_user_credits(user_id, -tournament['entry_fee'])
                await self.db.execute(
                    "UPDATE tournaments SET prize_pool = prize_pool + ? WHERE tournament_id = ?",
                    (int(tournament['entry_fee'] * 0.8), tournament_id)
                )
            
            # Add participant
            success = await self.db.join_tournament(tournament_id, user_id)
            
            if success:
                return {
                    'success': True,
                    'tournament_id': tournament_id,
                    'entry_fee': tournament['entry_fee']
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to join tournament'
                }
                
        except Exception as e:
            logger.error(f"Error joining tournament: {e}")
            return {
                'success': False,
                'error': 'Database error'
            }
    
    async def start_tournament(self, tournament_id: int) -> Dict[str, any]:
        """Start a tournament"""
        try:
            # Get tournament details
            tournament = await self.db.fetch_one(
                "SELECT * FROM tournaments WHERE tournament_id = ?",
                (tournament_id,)
            )
            
            if not tournament:
                return {
                    'success': False,
                    'error': 'Tournament not found'
                }
            
            # Get participants
            participants = await self.db.fetch_all(
                "SELECT * FROM tournament_participants WHERE tournament_id = ?",
                (tournament_id,)
            )
            
            if len(participants) < 2:
                return {
                    'success': False,
                    'error': 'Need at least 2 participants to start tournament'
                }
            
            # Update tournament status
            await self.db.execute(
                "UPDATE tournaments SET status = 'active' WHERE tournament_id = ?",
                (tournament_id,)
            )
            
            # Create tournament bracket (simplified)
            # This would create the initial bracket structure
            
            return {
                'success': True,
                'tournament_id': tournament_id,
                'participants': len(participants),
                'prize_pool': tournament['prize_pool']
            }
            
        except Exception as e:
            logger.error(f"Error starting tournament: {e}")
            return {
                'success': False,
                'error': 'Database error'
            }
    
    async def get_tournament_leaderboard(self, tournament_id: int) -> Dict[str, any]:
        """Get tournament leaderboard"""
        try:
            participants = await self.db.fetch_all("""
                SELECT tp.*, u.username 
                FROM tournament_participants tp
                JOIN users u ON tp.user_id = u.user_id
                WHERE tp.tournament_id = ?
                ORDER BY tp.wins DESC, tp.losses ASC
            """, (tournament_id,))
            
            return {
                'success': True,
                'participants': participants
            }
            
        except Exception as e:
            logger.error(f"Error getting tournament leaderboard: {e}")
            return {
                'success': False,
                'error': 'Database error'
            }