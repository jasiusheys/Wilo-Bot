import discord
from discord.ext import commands
import os
import asyncio

# Ustawienia uprawnień (Intents)
intents = discord.Intents.default()
intents.message_content = True  # Pozwala botowi czytać treść wiadomości, jeśli tego potrzebujesz
intents.members = True          # Potrzebne do zarządzania użytkownikami

# Inicjalizacja bota
bot = commands.Bot(command_prefix="!", intents=intents)

# 1. Funkcja ładowania modułów (cogs) z Twojego folderu 'cogs'
async def load_extensions():
    if os.path.exists('./cogs'):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                # Ładowanie np. cogs.moderacja
                await bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'✅ Załadowano moduł: {filename}')
    else:
        print("⚠️ Folder 'cogs' nie istnieje, pomijam ładowanie modułów.")

# 2. Wydarzenie on_ready - uruchamia się, gdy bot wejdzie online
@bot.event
async def on_ready():
    # Synchronizacja komend slash (/), żeby były widoczne na Discordzie
    try:
        synced = await bot.tree.sync()
        print(f'🔄 Zsynchronizowano {len(synced)} komend(y).')
    except Exception as e:
        print(f'❌ Błąd synchronizacji komend: {e}')
    
    print(f'🚀 Wilo-Bot wstał! Zalogowano jako: {bot.user}')

# 3. Główna funkcja startowa
async def main():
    async with bot:
        # Najpierw ładujemy moduły
        await load_extensions()
        
        # Pobieramy token z bezpiecznych ustawień Railway (Variable)
        token = os.getenv('DISCORD_TOKEN')
        
        if token:
            await bot.start(token)
        else:
            print("❌ BŁĄD: Nie znaleziono zmiennej DISCORD_TOKEN w ustawieniach Railway!")

# Uruchomienie wszystkiego
if __name__ == "__main__":
    asyncio.run(main())
