import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import logging

logger = logging.getLogger(__name__)

class Battle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_battle_views = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Battle cog loaded")
    
    @app_commands.command(name="battle", description="Challenge another trainer to a battle")
    async def battle(self, interaction: discord.Interaction, opponent: discord.User, format: str = "6v6"):
        """Start a battle with another user"""
        if opponent.bot or opponent.id == interaction.user.id:
            await interaction.response.send_message("You can't battle bots or yourself!", ephemeral=True)
            return
        
        # Check if both users have Pokemon
        user1 = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        user2 = await self.bot.db.get_or_create_user(str(opponent.id), opponent.display_name)
        
        party1 = await self.bot.db.get_user_party(user1['user_id'])
        party2 = await self.bot.db.get_user_party(user2['user_id'])
        
        if not party1 or len(party1) == 0:
            await interaction.response.send_message("You need Pokemon in your party to battle!", ephemeral=True)
            return
        
        if not party2 or len(party2) == 0:
            await interaction.response.send_message(f"{opponent.display_name} needs Pokemon in their party to battle!", ephemeral=True)
            return
        
        # Create battle
        battle_id = await self.bot.battle_system.create_battle(
            user1['user_id'], user2['user_id'], 'trainer', str(interaction.channel.id)
        )
        
        # Create battle view
        view = BattleView(self.bot, battle_id, interaction.user, opponent)
        self.active_battle_views[battle_id] = view
        
        embed = await self.bot.battle_system.get_battle_embed(battle_id)
        
        await interaction.response.send_message(
            f"⚔️ **Battle Challenge!**\n{opponent.mention}, {interaction.user.display_name} has challenged you to a battle!",
            embed=embed,
            view=view
        )
    
    @app_commands.command(name="npcbattle", description="Battle against an NPC trainer")
    async def npcbattle(self, interaction: discord.Interaction, difficulty: str = "normal"):
        """Battle against NPC"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        party = await self.bot.db.get_user_party(user['user_id'])
        
        if not party or len(party) == 0:
            await interaction.response.send_message("You need Pokemon in your party to battle!", ephemeral=True)
            return
        
        # Create NPC battle
        battle_id = await self.bot.battle_system.create_battle(
            user['user_id'], None, 'npc', str(interaction.channel.id)
        )
        
        # Generate NPC team based on difficulty
        npc_party = await self._generate_npc_party(difficulty, party[0]['level'])
        
        embed = discord.Embed(
            title=f"⚔️ NPC Battle - {difficulty.title()}",
            description="Battle against a computer-controlled trainer!",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="Your Party",
            value=f"{len(party)} Pokemon ready",
            inline=True
        )
        
        embed.add_field(
            name="NPC Trainer",
            value=f"{len(npc_party)} Pokemon | {difficulty.title()} difficulty",
            inline=True
        )
        
        view = NPCBattleView(self.bot, battle_id, interaction.user, npc_party)
        self.active_battle_views[battle_id] = view
        
        await interaction.response.send_message(embed=embed, view=view)
    
    async def _generate_npc_party(self, difficulty: str, player_level: int) -> list:
        """Generate NPC party based on difficulty"""
        # This would generate a balanced NPC team
        # For now, return a placeholder
        return []
    
    @app_commands.command(name="umoves", description="View available moves in battle")
    async def battle_moves(self, interaction: discord.Interaction):
        """Show available moves in current battle"""
        # Check if user is in a battle
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        active_battles = await self.bot.db.get_active_battles(user['user_id'])
        
        if not active_battles:
            await interaction.response.send_message("You're not in any active battles!", ephemeral=True)
            return
        
        battle = active_battles[0]
        battle_state = self.bot.battle_system.active_battles.get(battle['battle_id'])
        
        if not battle_state:
            await interaction.response.send_message("Battle not found!", ephemeral=True)
            return
        
        # Get active Pokemon moves
        active_pokemon = self.bot.battle_system._get_active_pokemon(battle_state, user['user_id'])
        
        embed = discord.Embed(
            title=f"📝 {active_pokemon['name']}'s Moves",
            color=discord.Color.blue()
        )
        
        # This would show the Pokemon's actual moves
        # For now, show placeholder
        embed.add_field(name="Available Moves", value="Move list would appear here", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

class BattleView(discord.ui.View):
    def __init__(self, bot, battle_id, challenger, opponent):
        super().__init__(timeout=300)
        self.bot = bot
        self.battle_id = battle_id
        self.challenger = challenger
        self.opponent = opponent
        self.accepted = False
    
    @discord.ui.button(label="Accept Battle", style=discord.ButtonStyle.green, emoji="⚔️")
    async def accept_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("Only the challenged user can accept!", ephemeral=True)
            return
        
        self.accepted = True
        
        # Start the battle
        embed = await self.bot.battle_system.get_battle_embed(self.battle_id)
        embed.title = "⚔️ Battle Started!"
        
        # Create battle controls view
        controls_view = BattleControlsView(self.bot, self.battle_id, self.challenger, self.opponent)
        self.bot.active_battle_views[self.battle_id] = controls_view
        
        await interaction.response.edit_message(
            content=f"🎮 **Battle Started!**\n{self.challenger.mention} vs {self.opponent.mention}",
            embed=embed,
            view=controls_view
        )
    
    @discord.ui.button(label="Decline Battle", style=discord.ButtonStyle.red, emoji="❌")
    async def decline_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent.id:
            await interaction.response.send_message("Only the challenged user can decline!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="Battle Declined",
            description=f"{self.opponent.display_name} has declined the battle challenge.",
            color=discord.Color.red()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Clean up battle
        if self.battle_id in self.bot.battle_system.active_battles:
            del self.bot.battle_system.active_battles[self.battle_id]

class BattleControlsView(discord.ui.View):
    def __init__(self, bot, battle_id, player1, player2):
        super().__init__(timeout=None)
        self.bot = bot
        self.battle_id = battle_id
        self.player1 = player1
        self.player2 = player2
        self.current_turn = player1  # Player 1 starts
    
    @discord.ui.button(label="Fight", style=discord.ButtonStyle.red, emoji="⚔️", row=0)
    async def fight(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.current_turn.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        
        # Show move selection
        moves_view = MoveSelectionView(self.bot, self.battle_id, interaction.user)
        await interaction.response.send_message("Select a move:", view=moves_view, ephemeral=True)
    
    @discord.ui.button(label="Pokemon", style=discord.ButtonStyle.green, emoji="🐾", row=0)
    async def switch_pokemon(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.current_turn.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        
        # Show Pokemon selection
        party_view = PokemonSelectionView(self.bot, self.battle_id, interaction.user)
        await interaction.response.send_message("Select a Pokemon:", view=party_view, ephemeral=True)
    
    @discord.ui.button(label="Item", style=discord.ButtonStyle.blurple, emoji="🎒", row=0)
    async def use_item(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.current_turn.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        
        # Show item selection
        item_view = ItemSelectionView(self.bot, self.battle_id, interaction.user)
        await interaction.response.send_message("Select an item:", view=item_view, ephemeral=True)
    
    @discord.ui.button(label="Run", style=discord.ButtonStyle.gray, emoji="🏃", row=0)
    async def forfeit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.current_turn.id:
            await interaction.response.send_message("It's not your turn!", ephemeral=True)
            return
        
        # Confirm forfeit
        confirm_view = ConfirmForfeitView(self.bot, self.battle_id, interaction.user)
        await interaction.response.send_message("Are you sure you want to forfeit?", view=confirm_view, ephemeral=True)

class MoveSelectionView(discord.ui.View):
    def __init__(self, bot, battle_id, player):
        super().__init__(timeout=60)
        self.bot = bot
        self.battle_id = battle_id
        self.player = player
        
        # Add move buttons (placeholder)
        moves = ["Tackle", "Ember", "Water Gun", "Thunder Shock"]
        for i, move in enumerate(moves):
            self.add_item(MoveButton(move, i))

class MoveButton(discord.ui.Button):
    def __init__(self, move_name, index):
        super().__init__(label=move_name, style=discord.ButtonStyle.red)
        self.move_name = move_name
    
    async def callback(self, interaction: discord.Interaction):
        # Process move selection
        action = {
            'type': 'move',
            'move_name': self.move_name,
            'player_id': interaction.user.id
        }
        
        # This would process the move in battle system
        await interaction.response.send_message(f"Used {self.move_name}!", ephemeral=True)
        await interaction.message.delete()

class PokemonSelectionView(discord.ui.View):
    def __init__(self, bot, battle_id, player):
        super().__init__(timeout=60)
        self.bot = bot
        self.battle_id = battle_id
        self.player = player
        
        # Add Pokemon buttons (placeholder)
        pokemon_names = ["Pikachu", "Charizard", "Blastoise", "Venusaur"]
        for i, pokemon in enumerate(pokemon_names):
            self.add_item(PokemonButton(pokemon, i + 1))

class PokemonButton(discord.ui.Button):
    def __init__(self, pokemon_name, slot):
        super().__init__(label=pokemon_name, style=discord.ButtonStyle.green)
        self.pokemon_name = pokemon_name
        self.slot = slot
    
    async def callback(self, interaction: discord.Interaction):
        action = {
            'type': 'switch',
            'pokemon_index': self.slot - 1,
            'player_id': interaction.user.id
        }
        
        await interaction.response.send_message(f"Switched to {self.pokemon_name}!", ephemeral=True)
        await interaction.message.delete()

class ItemSelectionView(discord.ui.View):
    def __init__(self, bot, battle_id, player):
        super().__init__(timeout=60)
        self.bot = bot
        self.battle_id = battle_id
        self.player = player
        
        # Add item buttons (placeholder)
        items = ["Potion", "Super Potion", "Hyper Potion", "Max Potion"]
        for item in items:
            self.add_item(ItemButton(item))

class ItemButton(discord.ui.Button):
    def __init__(self, item_name):
        super().__init__(label=item_name, style=discord.ButtonStyle.blurple)
        self.item_name = item_name
    
    async def callback(self, interaction: discord.Interaction):
        action = {
            'type': 'item',
            'item_name': self.item_name,
            'player_id': interaction.user.id
        }
        
        await interaction.response.send_message(f"Used {self.item_name}!", ephemeral=True)
        await interaction.message.delete()

class ConfirmForfeitView(discord.ui.View):
    def __init__(self, bot, battle_id, player):
        super().__init__(timeout=30)
        self.bot = bot
        self.battle_id = battle_id
        self.player = player
    
    @discord.ui.button(label="Yes, Forfeit", style=discord.ButtonStyle.red, emoji="⚠️")
    async def confirm_forfeit(self, interaction: discord.Interaction, button: discord.ui.Button):
        action = {
            'type': 'forfeit',
            'player_id': interaction.user.id
        }
        
        await interaction.response.send_message("Battle forfeited!", ephemeral=True)
        await interaction.message.delete()
    
    @discord.ui.button(label="No, Continue", style=discord.ButtonStyle.green, emoji="✅")
    async def cancel_forfeit(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("Continuing battle!", ephemeral=True)
        await interaction.message.delete()

class NPCBattleView(discord.ui.View):
    def __init__(self, bot, battle_id, player, npc_party):
        super().__init__(timeout=None)
        self.bot = bot
        self.battle_id = battle_id
        self.player = player
        self.npc_party = npc_party
    
    @discord.ui.button(label="Start Battle", style=discord.ButtonStyle.green, emoji="⚔️")
    async def start_npc_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("This isn't your battle!", ephemeral=True)
            return
        
        # Start NPC battle
        embed = await self.bot.battle_system.get_battle_embed(self.battle_id)
        embed.title = "⚔️ NPC Battle Started!"
        
        # Create battle controls
        controls_view = BattleControlsView(self.bot, self.battle_id, self.player, None)
        self.bot.active_battle_views[self.battle_id] = controls_view
        
        await interaction.response.edit_message(embed=embed, view=controls_view)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red, emoji="❌")
    async def cancel_npc_battle(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.player.id:
            await interaction.response.send_message("This isn't your battle!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title="NPC Battle Cancelled",
            description="You have cancelled the NPC battle.",
            color=discord.Color.red()
        )
        
        await interaction.response.edit_message(embed=embed, view=None)
        
        # Clean up
        if self.battle_id in self.bot.battle_system.active_battles:
            del self.bot.battle_system.active_battles[self.battle_id]

async def setup(bot):
    await bot.add_cog(Battle(bot))