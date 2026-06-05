import discord
from discord.ext import commands

class Ekonomia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # --- KONFIGURACJA KANAŁU PROPOZYCJI ---
        self.PROPOZYCJE_CHANNEL_ID = 1512227610392789215

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignoruj wiadomości od botów oraz wiadomości prywatne (DM)
        if message.author.bot or not message.guild:
            return

        # Sprawdź, czy wiadomość została napisana na kanale propozycji
        if message.channel.id == self.PROPOZYCJE_CHANNEL_ID:
            try:
                await message.add_reaction("✅")
                await message.add_reaction("❌")
            except Exception as e:
                print(f"Błąd podczas dodawania reakcji: {e}")

async def setup(bot):
    await bot.add_cog(Ekonomia(bot))
