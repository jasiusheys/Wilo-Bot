import discord
from discord.ext import commands

class AutoOdpowiedzi(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Klucze muszą być dokładnie takie, jakie mają zostać napisane (tylko małe litery)
        self.odpowiedzi = {
            "kiedy event": "wszystko masz na kanale rekrutacja nagrywki",
            
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        # Nie reaguj na boty
        if message.author.bot:
            return

        # Sprawdzamy czystą treść (bez zbędnych spacji po bokach, małe litery)
        content = message.content.lower().strip()

        # Bot odpisze tylko, jeśli treść jest dokładnie równa jednemu z kluczy
        if content in self.odpowiedzi:
            await message.channel.send(self.odpowiedzi[content])

async def setup(bot):
    await bot.add_cog(AutoOdpowiedzi(bot))
