# Pokemon Discord Bot - Installation Guide

## Quick Setup

1. **Install Python 3.8+**
   ```bash
   python --version  # Should be 3.8 or higher
   ```

2. **Clone/Download the bot files**
   ```bash
   # If you have the files, skip this step
   # Otherwise, download all the provided files to a folder
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   
   # Edit .env with your Discord bot token
   # Get your token from: https://discord.com/developers/applications
   ```

5. **Run Setup Script**
   ```bash
   python setup.py
   ```

6. **Start the Bot**
   ```bash
   # On Windows
   start_bot.bat
   
   # On Linux/Mac
   ./start_bot.sh
   
   # Or directly
   python run_bot.py
   ```

## Environment Variables

Edit the `.env` file and add your Discord bot token:

```
DISCORD_TOKEN=your_discord_bot_token_here
CLIENT_ID=your_client_id_here (optional)
```

## Getting a Discord Bot Token

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application"
3. Give it a name (e.g., "Pokemon Bot")
4. Go to the "Bot" section on the left
5. Click "Add Bot"
6. Copy the token (keep this secret!)
7. Under "Privileged Gateway Intents", enable:
   - Presence Intent
   - Server Members Intent
   - Message Content Intent

## Inviting the Bot to Your Server

1. In the Developer Portal, go to "OAuth2" → "URL Generator"
2. Select these scopes:
   - `bot`
   - `applications.commands`
3. Select these permissions:
   - Send Messages
   - Embed Links
   - Read Message History
   - Use Slash Commands
   - Manage Messages (for cleanup)
   - Add Reactions
   - Use External Emojis
   - Attach Files
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

## First Run

The first time you run the bot, it will:
1. Create the database structure
2. Download Pokemon data from PokeAPI (this may take a few minutes)
3. Populate the database with all Pokemon, moves, abilities, and items
4. Start the bot and connect to Discord

## Troubleshooting

### "Module not found" errors
```bash
pip install -r requirements.txt --upgrade
```

### "Token not found" error
Make sure your `.env` file exists and contains:
```
DISCORD_TOKEN=your_actual_token_here
```

### Database errors
Delete the `data/pokemon_database.db` file and run the bot again to recreate the database.

### Bot not responding to commands
1. Check that the bot has proper permissions in your server
2. Make sure you're using the correct command prefix (`;` for text commands, `/` for slash commands)
3. Check the logs in `logs/pokemon_bot.log`

### Slow startup on first run
The bot needs to download Pokemon data on first startup. This is normal and only happens once.

## Features Overview

Once running, the bot includes:

- **Complete Pokemon Database**: 1000+ Pokemon with all forms
- **Battle System**: Turn-based 6v6 battles with status effects
- **Pokemon Catching**: Pokemon spawn from chat conversations
- **Trading System**: Trade Pokemon with other users
- **Marketplace**: Buy and sell Pokemon
- **Fishing Mini-game**: Catch water Pokemon
- **Daily Missions**: Complete tasks for rewards
- **Economy System**: Credits, items, and progression
- **Tournaments**: Organized competitive events
- **And much more!**

## Support

If you encounter issues:
1. Check the logs in `logs/pokemon_bot.log`
2. Ensure all files are in the same directory
3. Verify Python version is 3.8+
4. Check that all dependencies installed correctly
5. Make sure the Discord bot token is valid

Enjoy your Pokemon Discord bot! 🎮🐾