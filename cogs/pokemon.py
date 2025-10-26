import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger(__name__)

class Pokemon(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        logger.info(f"Pokemon cog loaded")
    
    @app_commands.command(name="pokemon", description="View your Pokemon collection")
    @app_commands.choices(sort_by=[
        app_commands.Choice(name="Recent", value="recent"),
        app_commands.Choice(name="Name", value="name"),
        app_commands.Choice(name="Level", value="level"),
        app_commands.Choice(name="Rarity", value="rarity")
    ])
    async def pokemon(self, interaction: discord.Interaction, page: int = 1, sort_by: str = "recent"):
        """Display user's Pokemon collection"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        # Get Pokemon with pagination
        per_page = 20
        offset = (page - 1) * per_page
        
        pokemon_list = await self.bot.db.get_user_pokemon(user['user_id'], per_page, offset)
        total_pokemon = await self.bot.db.get_user_pokemon_count(user['user_id'])
        
        if not pokemon_list:
            embed = discord.Embed(
                title="No Pokemon Found",
                description="You haven't caught any Pokemon yet! Chat in channels to make them spawn.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"🐾 {interaction.user.display_name}'s Pokemon",
            description=f"Showing {offset + 1}-{min(offset + per_page, total_pokemon)} of {total_pokemon} Pokemon",
            color=discord.Color.blue()
        )
        
        pokemon_text = ""
        for i, pokemon in enumerate(pokemon_list, 1):
            # Pokemon info
            name = pokemon['name']
            level = pokemon['level']
            is_shiny = "✨" if pokemon['is_shiny'] else ""
            
            # Type display
            type_str = pokemon['type1']
            if pokemon['type2']:
                type_str += f"/" + pokemon['type2']
            
            # IV display (simplified)
            total_iv = (pokemon['hp_iv'] + pokemon['attack_iv'] + pokemon['defense_iv'] + 
                       pokemon['sp_attack_iv'] + pokemon['sp_defense_iv'] + pokemon['speed_iv']) / 6
            iv_rating = "★" * int(total_iv / 31 * 5)
            
            pokemon_text += f"`{i:2d}`. {is_shiny}**{name}** (Lv.{level}) [{type_str}] {iv_rating}\n"
        
        embed.add_field(name="Pokemon", value=pokemon_text, inline=False)
        
        # Add sorting info
        embed.set_footer(text=f"Sorted by: {sort_by.title()} | Page {page}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="party", description="View and manage your Pokemon party")
    async def party(self, interaction: discord.Interaction):
        """Display user's current party"""
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        party = await self.bot.db.get_user_party(user['user_id'])
        
        if not party:
            embed = discord.Embed(
                title="Empty Party",
                description="You don't have any Pokemon in your party! Add some Pokemon to get started.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)
            return
        
        embed = discord.Embed(
            title=f"⚔️ {interaction.user.display_name}'s Party",
            color=discord.Color.green()
        )
        
        for i, pokemon in enumerate(party, 1):
            # Pokemon details
            name = pokemon['name']
            level = pokemon['level']
            current_hp = pokemon['current_hp'] or pokemon['max_hp']
            max_hp = pokemon['max_hp']
            
            # Status
            status = ""
            if pokemon.get('status_condition'):
                status = f" [{pokemon['status_condition'].title()}]"
            
            # Types
            types = pokemon['type1']
            if pokemon['type2']:
                types += f"/" + pokemon['type2']
            
            # IVs
            total_iv = (pokemon['hp_iv'] + pokemon['attack_iv'] + pokemon['defense_iv'] + 
                       pokemon['sp_attack_iv'] + pokemon['sp_defense_iv'] + pokemon['speed_iv']) / 6
            iv_percentage = int(total_iv / 31 * 100)
            
            # Create Pokemon info
            pokemon_info = f"**Lv.{level} {name}**{status}\n"
            pokemon_info += f"Type: {types}\n"
            pokemon_info += f"HP: {current_hp}/{max_hp}\n"
            pokemon_info += f"IV: {iv_percentage}%\n"
            
            if pokemon['is_shiny']:
                pokemon_info += "✨ Shiny Pokemon ✨\n"
            
            embed.add_field(
                name=f"Slot {i}",
                value=pokemon_info,
                inline=True
            )
        
        embed.set_footer(text="Use /addparty to add Pokemon to your party")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="addparty", description="Add a Pokemon to your party")
    async def addparty(self, interaction: discord.Interaction, pokemon_id: int, slot: int = None):
        """Add a Pokemon to party"""
        if slot is None:
            # Find empty slot
            party = await self.bot.db.get_user_party(
                (await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name))['user_id']
            )
            existing_slots = [p['slot'] for p in party]
            for i in range(1, 7):
                if i not in existing_slots:
                    slot = i
                    break
            
            if slot is None:
                await interaction.response.send_message("Your party is full! Remove a Pokemon first.", ephemeral=True)
                return
        
        if slot < 1 or slot > 6:
            await interaction.response.send_message("Slot must be between 1 and 6!", ephemeral=True)
            return
        
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        # Verify Pokemon belongs to user
        pokemon = await self.bot.db.fetch_one(
            "SELECT * FROM player_pokemon WHERE id = ? AND user_id = ?",
            (pokemon_id, user['user_id'])
        )
        
        if not pokemon:
            await interaction.response.send_message("Pokemon not found or doesn't belong to you!", ephemeral=True)
            return
        
        # Add to party
        success = await self.bot.db.add_pokemon_to_party(user['user_id'], pokemon_id, slot)
        
        if success:
            pokemon_species = await self.bot.db.fetch_one(
                "SELECT name FROM pokemon_species WHERE pokemon_id = ?",
                (pokemon['pokemon_id'],)
            )
            
            embed = discord.Embed(
                title="✅ Pokemon Added to Party",
                description=f"**{pokemon_species['name']}** has been added to slot {slot}!",
                color=discord.Color.green()
            )
            
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Failed to add Pokemon to party!", ephemeral=True)
    
    @app_commands.command(name="removeparty", description="Remove a Pokemon from your party")
    async def removeparty(self, interaction: discord.Interaction, slot: int):
        """Remove a Pokemon from party"""
        if slot < 1 or slot > 6:
            await interaction.response.send_message("Slot must be between 1 and 6!", ephemeral=True)
            return
        
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        
        # Remove from party
        await self.bot.db.remove_pokemon_from_party(user['user_id'], slot)
        
        embed = discord.Embed(
            title="✅ Pokemon Removed",
            description=f"Pokemon removed from slot {slot}",
            color=discord.Color.orange()
        )
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="dex", description="View Pokemon information")
    async def dex(self, interaction: discord.Interaction, pokemon_name: str):
        """Show Pokemon information"""
        # Find Pokemon by name
        pokemon = await self.bot.db.fetch_one(
            "SELECT * FROM pokemon_species WHERE LOWER(name) = LOWER(?)",
            (pokemon_name,)
        )
        
        if not pokemon:
            await interaction.response.send_message(f"Pokemon '{pokemon_name}' not found!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"#{pokemon['pokedex_number']} {pokemon['name']}",
            color=discord.Color.blue()
        )
        
        if pokemon['sprite_url']:
            embed.set_thumbnail(url=pokemon['sprite_url'])
        
        # Basic info
        type_str = pokemon['type1']
        if pokemon['type2']:
            type_str += f"/" + pokemon['type2']
        
        embed.add_field(
            name="Basic Info",
            value=f"Type: **{type_str}**\n"
                  f"Height: {pokemon['height']} dm\n"
                  f"Weight: {pokemon['weight']} hg\n"
                  f"Category: **{pokemon['category'].title()}**",
            inline=True
        )
        
        # Base stats
        total_stats = (pokemon['base_hp'] + pokemon['base_attack'] + pokemon['base_defense'] +
                      pokemon['base_sp_attack'] + pokemon['base_sp_defense'] + pokemon['base_speed'])
        
        embed.add_field(
            name="Base Stats",
            value=f"HP: **{pokemon['base_hp']}**\n"
                  f"Attack: **{pokemon['base_attack']}**\n"
                  f"Defense: **{pokemon['base_defense']}**\n"
                  f"Sp. Atk: **{pokemon['base_sp_attack']}**\n"
                  f"Sp. Def: **{pokemon['base_sp_defense']}**\n"
                  f"Speed: **{pokemon['base_speed']}**\n"
                  f"Total: **{total_stats}**",
            inline=True
        )
        
        # Check if user owns this Pokemon
        user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
        owned_count = await self.bot.db.fetch_val(
            "SELECT COUNT(*) FROM player_pokemon WHERE user_id = ? AND pokemon_id = ?",
            (user['user_id'], pokemon['pokemon_id'])
        ) or 0
        
        if owned_count > 0:
            embed.add_field(
                name="Collection",
                value=f"You own **{owned_count}** of this Pokemon!",
                inline=False
            )
        
        embed.set_footer(text=f"Generation {pokemon['generation']}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="moves", description="View Pokemon moves")
    async def moves(self, interaction: discord.Interaction, pokemon_name: str = None):
        """Show Pokemon moves"""
        if pokemon_name:
            # Get Pokemon by name
            pokemon = await self.bot.db.fetch_one(
                "SELECT * FROM pokemon_species WHERE LOWER(name) = LOWER(?)",
                (pokemon_name,)
            )
            
            if not pokemon:
                await interaction.response.send_message(f"Pokemon '{pokemon_name}' not found!", ephemeral=True)
                return
            
            pokemon_id = pokemon['pokemon_id']
            pokemon_name = pokemon['name']
        else:
            # Get user's first party Pokemon
            user = await self.bot.db.get_or_create_user(str(interaction.user.id), interaction.user.display_name)
            party = await self.bot.db.get_user_party(user['user_id'])
            
            if not party:
                await interaction.response.send_message("You don't have any Pokemon in your party!", ephemeral=True)
                return
            
            pokemon_id = party[0]['pokemon_id']
            pokemon_name = party[0]['name']
        
        # Get Pokemon's moves
        moves = await self.bot.db.fetch_all("""
            SELECT m.*, pm.learn_method, pm.level_learned
            FROM pokemon_moves pm
            JOIN moves m ON pm.move_id = m.move_id
            WHERE pm.pokemon_id = ?
            ORDER BY 
                CASE pm.learn_method
                    WHEN 'level-up' THEN 1
                    WHEN 'tm' THEN 2
                    WHEN 'egg' THEN 3
                    ELSE 4
                END,
                pm.level_learned
        """, (pokemon_id,))
        
        if not moves:
            await interaction.response.send_message(f"No moves found for {pokemon_name}!", ephemeral=True)
            return
        
        embed = discord.Embed(
            title=f"📝 {pokemon_name}'s Moves",
            color=discord.Color.purple()
        )
        
        # Group moves by learning method
        moves_by_method = {}
        for move in moves:
            method = move['learn_method']
            if method not in moves_by_method:
                moves_by_method[method] = []
            moves_by_method[method].append(move)
        
        for method, method_moves in moves_by_method.items():
            method_name = {
                'level-up': 'Level Up',
                'tm': 'TM/TR',
                'egg': 'Egg Moves',
                'tutor': 'Move Tutor'
            }.get(method, method.title())
            
            move_text = ""
            for move in method_moves[:10]:  # Limit to 10 moves per method
                if method == 'level-up' and move['level_learned'] > 0:
                    move_text += f"Lv.{move['level_learned']}: **{move['name']}**\n"
                else:
                    move_text += f"**{move['name']}**\n"
            
            if len(method_moves) > 10:
                move_text += f"... and {len(method_moves) - 10} more"
            
            embed.add_field(name=method_name, value=move_text or "No moves", inline=True)
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="catch", description="Catch a Pokemon (alternative to typing name)")
    async def catch(self, interaction: discord.Interaction, pokemon_name: str):
        """Alternative method to catch Pokemon"""
        # This will be handled by the spawn system
        await interaction.response.send_message(
            f"Trying to catch {pokemon_name}... (This works the same as typing the name)",
            ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Pokemon(bot))