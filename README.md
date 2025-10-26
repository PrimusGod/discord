# Pokemon Discord Bot

A comprehensive Pokemon Discord bot with turn-based battles, Pokemon catching, trading, and more!

## Features

### 🐾 Pokemon Collection
- **Catch Pokemon**: Pokemon spawn randomly from chat conversations
- **Complete Pokedex**: All Pokemon from generations 1-9
- **Pokemon Forms**: All forms including shinies, megas, regional variants
- **Individual Values (IVs)**: Each Pokemon has unique stats
- **Effort Values (EVs)**: Train your Pokemon through battles

### ⚔️ Battle System
- **Turn-based Battles**: Full 6v6 Pokemon battles
- **Status Effects**: Burn, poison, paralysis, sleep, freeze, confusion
- **Type Effectiveness**: Complete type chart with STAB bonuses
- **Critical Hits**: Random critical hit mechanics
- **Status Moves**: Full status move implementation
- **NPC Battles**: Battle against AI trainers

### 💰 Economy System
- **Credits**: Earn credits through various activities
- **Daily Bonus**: Claim daily rewards
- **Voting Rewards**: Get credits and upvote points for voting
- **Item Shop**: Buy and sell items
- **Marketplace**: Trade Pokemon with other players
- **Auctions**: Bid on rare Pokemon

### 🎮 Mini-Games
- **Fishing**: Catch water Pokemon through fishing
- **Slot Machine**: Gamble credits in the casino
- **Daily Missions**: Complete missions for big rewards
- **Tournaments**: Compete in organized tournaments

### 🔄 Trading System
- **Player Trading**: Trade Pokemon and credits with other players
- **Global Market**: Buy and sell Pokemon
- **Trade Safety**: Secure trading system

### 🏆 Progression
- **Experience System**: Gain EXP from various activities
- **Fishing Levels**: Improve fishing skills
- **Luck System**: Increase spawn rates and rewards
- **Achievements**: Unlock rewards through gameplay

## Commands

### General Commands
- `;start` - Start your Pokemon journey
- `;profile [@user]` - View trainer profile
- `;stats` - Check your stats and balance
- `;daily` - Claim daily bonus
- `;vote` - Get voting rewards
- `;leaderboard [category]` - View leaderboards

### Pokemon Commands
- `;pokemon [page] [sort_by]` - View your Pokemon collection
- `;party` - Check your current battle party
- `;dex <pokemon>` - View Pokemon information
- `;addparty <pokemon_id> [slot]` - Add Pokemon to party
- `;removeparty <slot>` - Remove Pokemon from party

### Battle Commands
- `;battle @user [format]` - Challenge someone to battle
- `;npcbattle [difficulty]` - Battle against AI trainer
- `;moves [pokemon]` - View Pokemon moves

### Economy Commands
- `;shop [category]` - View item shop
- `;buy <item> [quantity]` - Buy items
- `;sell <item> [quantity]` - Sell items
- `;inventory` - View your inventory
- `;market [page] [search]` - Browse Pokemon market
- `;sellpokemon <pokemon_id> <price>` - List Pokemon for sale
- `;buypokemon <listing_id>` - Buy Pokemon from market

### Trading Commands
- `;trade @user` - Start trade with another user
- `;addpokemon <trade_id> <pokemon_id>` - Add Pokemon to trade
- `;addcredits <trade_id> <amount>` - Add credits to trade
- `;accepttrade <trade_id>` - Accept trade offer
- `;canceltrade <trade_id>` - Cancel trade
- `;mytrades` - View your active trades

### Mini-Game Commands
- `;missions` - View daily missions
- `;claim` - Claim mission rewards
- `;fish` - Go fishing
- `;slots [amount]` - Play slot machine
- `;missionleaderboard` - View mission completion leaderboard

### Utility Commands
- `;help` - Show help information
- `;hint` - Get hint for current Pokemon spawn

## Setup

### Requirements
- Python 3.8+
- Discord.py 2.3+
- SQLite3
- aiohttp
- PokeAPI integration

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pokemon-discord-bot.git
cd pokemon-discord-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a Discord bot application:
   - Go to [Discord Developer Portal](https://discord.com/developers/applications)
   - Create a new application
   - Add a bot to the application
   - Copy the bot token

4. Set up environment variables:
```bash
export DISCORD_TOKEN="your-bot-token-here"
```

5. Run the database setup:
```python
# This will be handled automatically on first run
python bot.py
```

6. Invite the bot to your server using the OAuth2 URL from the Discord Developer Portal

### Database Population

The bot will automatically populate the database with Pokemon data from PokeAPI on first run. This may take some time as it fetches:
- All Pokemon species (1000+)
- All moves (1000+)
- All abilities (300+)
- All items (1000+)

## Configuration

Edit `config.py` to customize:
- Spawn rates
- Battle timeouts
- Economy settings
- Reward amounts
- And more!

## Development

### Adding New Features
1. Create a new cog in the `cogs/` directory
2. Add your commands using the `@app_commands.command()` decorator
3. Register the cog in `bot.py`
4. Add any new database tables to `database/schema.sql`

### Database Schema
The bot uses SQLite with the following main tables:
- `users` - User information and stats
- `pokemon_species` - Pokemon data from PokeAPI
- `player_pokemon` - User's Pokemon collection
- `moves` - Pokemon moves
- `items` - Items and their effects
- `active_battles` - Current battles
- `market_listings` - Pokemon marketplace
- `trades` - Player trades

## Support

For support, please:
1. Check the logs in `pokemon_bot.log`
2. Ensure all dependencies are installed
3. Verify your Discord bot token is correct
4. Check that the bot has proper permissions in your server

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License.

## Credits

- Pokemon data from [PokeAPI](https://pokeapi.co/)
- Built with [discord.py](https://discordpy.readthedocs.io/)
- Inspired by popular Pokemon bots like Mewbot and DittoBot

---

**Note**: This is a fan-made project and is not affiliated with Nintendo, Game Freak, or The Pokemon Company.