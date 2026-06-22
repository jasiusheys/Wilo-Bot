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
                  "`!koniec_eventu <nazwa>` - Zamyka rekrutacje i pokazuje całe staty.",
            inline=False
        )

        # 2. Nagrywki
        embed.add_field(
            name="🎥 System Nagrywek",
            value="`!setupnagrywka <nazwa> @nowa_rola @everyone` - Tworzy kanały dla nowej nagrywki.",
            inline=False
        )

        # 3. Blacklista
        embed.add_field(
            name="🚫 Blacklista ",
            value="`!blacklista` - Wyświetla wszystkie osoby z blacklisty.\n"
                  "`!blacklista_dodaj @user...` - Osoba dodana nie może zrobić podania na nagrywke.\n"
                  "`!blacklista_usun @user` - Usuwa z blki.\n"
                  "`!blacklista_usunall` - resetuje całą blke.",
            inline=False
        )

        # 4. Moderacja
        embed.add_field(
            name="🛡️ Moderacja ",
            value="`!ping` - Sprawdza opóźnienie.\n"
                  "`!kick @user <powód>` - Wyrzuca użytkownika.\n"
                  "`!ban @user <powód>` - Banuje użytkownika.\n"
                  "`!clear <ilość>` - Usuwa  wiadomości.",
            inline=False
        )

      
        embed.set_footer(text="Wilo-Bot | komendy 2026")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Pomoc(bot))
