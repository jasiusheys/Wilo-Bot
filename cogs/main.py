import os
import asyncio
import discord
from discord.ext import commands

# 1. Konfiguracja intencji (intents) bota
intents = discord.Intents.default()
intents.message_content = True  # Wymagane, aby bot czytał treść wiadomości tekstowych
intents.members = True          # Wymagane do działania moderacji (kick, ban)

bot = commands.Bot(command_prefix="!", intents=intents)

# 2. Ładowanie modułów (cogs)
async def load_extensions():
    # Upewnij się, że folder 'cogs' istnieje
   if os.path.exists('./cogs'):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Załadowano moduł: {filename}')
    else:
        print("Folder 'cogs' nie istnieje, pomijam ładowanie modułów.")

# 3. Wydarzenie on_ready
@bot.event
async def on_ready():
    # Synchronizacja komend, aby działały w Discordzie
    try:
        synced = await bot.tree.sync()
        print(f'Zsynchronizowano {len(synced)} komend(y).')
    except Exception as e:
        print(f'Błąd synchronizacji: {e}')

    print(f'Wilo bot wstał! Zalogowano jako: {bot.user}')

# 4. Główna funkcja uruchamiająca bota
async def main():
    async with bot:
        await load_extensions()
        # Pobieramy ukryty token z bezpiecznych ustawień hostingu
        token = os.getenv('DISCORD_TOKEN') 
        await bot.start(token)

# Uruchomienie bota
asyncio.run(main())

