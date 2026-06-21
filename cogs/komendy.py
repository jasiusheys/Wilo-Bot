import discord
from discord.ext import commands

class Pomoc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="komendy")
    async def komendy(self, ctx):
        embed = discord.Embed(
            title="KOMENDY do wilo bota",
            description="Pełny spis wszystkich funkcji i komend bota.",
            color=discord.Color.gold()
        )

        # 1. Rekrutacja
        embed.add_field(
            name="📥 System Rekrutacji",
            value="`!nowy_event <ranga_id> <nazwa>` - Rozpoczyna rekrutację.\n"
                  "`!koniec_eventu <nazwa>` - Zamyka nabór i generuje raport.",
            inline=False
        )

        # 2. Nagrywki
        embed.add_field(
            name="🎥 System Nagrywek",
            value="`!setupnagrywka <nazwa> @nowa_rola @stara_rola` - Tworzy kanały dla nowej nagrywki.",
            inline=False
        )

        # 3. Blacklista
        embed.add_field(
            name="🚫 Blacklista (Admin)",
            value="`!blacklista` - Wyświetla zbanowanych.\n"
                  "`!blacklista_dodaj @user...` - Banuje i czyści kanały.\n"
                  "`!blacklista_usun @user` - Usuwa z listy.\n"
                  "`!blacklista_usunall` - Reset blacklisty.",
            inline=False
        )

        # 4. Moderacja
        embed.add_field(
            name="🛡️ Moderacja i Narzędzia",
            value="`!ping` - Sprawdza opóźnienie.\n"
                  "`!kick @user <powód>` - Wyrzuca użytkownika.\n"
                  "`!ban @user <powód>` - Banuje użytkownika.\n"
                  "`!clear <ilość>` - Usuwa masowo wiadomości.",
            inline=False
        )

        # 5. Automatyka
        embed.add_field(
            name="⚙️ Funkcje Automatyczne",
            value="• **Powitania:** Automatyczne wiadomości powitalne.\n"
                  "• **Auto-Mod:** Wykrywanie spamu, wulgaryzmów i pingów.\n"
                  "• **Propozycje:** Dodaje reakcje ✅/❌ do propozycji.\n"
                  "• **Auto-Odpowiedzi:** Reaguje na 'kiedy event'.",
            inline=False
        )

        embed.set_footer(text="Wilo-Bot | System Zarządzania 2026")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Pomoc(bot))
