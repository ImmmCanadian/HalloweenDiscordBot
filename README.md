# Halloween Discord Bot

A feature-rich Discord bot designed for a single server, but adaptable for multiple servers with some configuration changes. This bot includes economy, store, raffle, gambling, and more.

## Getting Started

### 1. Clone the Repository
```sh
git clone https://github.com/ImmmCanadian/HalloweenDiscordBot.git
cd HalloweenDiscordBot
```

### 2. Set Up Your Python Environment
It is recommended to use a virtual environment:
```sh
python -m venv venv
venv\Scripts\activate  # On Windows
source venv/bin/activate  # On Mac/Linux
```

### 3. Install Requirements
```sh
pip install -r requirements.txt
```

### 4. Create Your Discord Bot & Token
- Go to the [Discord Developer Portal](https://discord.com/developers/applications)
- Create a new application and bot
- Copy your bot token
- Create a file named `secret.env` in the project root:
  ```env
  TOKEN=your-bot-token-here
  ```

### 5. Run the Bot
```sh
python main.py
```

## Server-Specific Configuration
- This bot was created for a single Discord server. Role IDs and some logic are hardcoded for one server.
- The database is configured for a single server. To use in multiple servers, you must:
  - Update hardcoded role IDs in the cogs
  - Refactor database logic for multi-server support by intergrating guild id into users database entries

## Features
- Economy system (candy, bank, rob, gamble, store)
- Raffle system
- Store with pagination
- Gambling games (roulette, slots, etc.)
- Profile image generation (PIL)
- Logging to file
- Custom commands and cooldowns

### Disabled/Commented Features
- Custom profile uploads
- Slot machine game

These features exist in the code but are commented out. You may enable them if you wish to use them.

## Requirements
- Python 3.10+
- discord.py
- asqlite
- Pillow (PIL)
- aiohttp
- python-dotenv

All required packages are listed in `requirements.txt`.

## Notes
- For multi-server use, you must update hardcoded values and database logic.
- Logging is enabled by default and writes to the `logs/` directory.
- Some features are disabled by default but can be re-enabled in the code.

## License
MIT
