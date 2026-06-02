import discord
from discord.ext import commands

class Powitania(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # TUTAJ WPISZ ID SWOJEGO KANAŁU (bez cudzysłowu)
        channel_id = 1280550904839540842 
        channel = self.bot.get_channel(channel_id)

        if channel:
            embed = discord.Embed(
                title=f"Witaj na serwerze Wilo - Eventy!",
                description=f"Cześć {member.mention}! Cieszymy się, że jesteś z nami. Przeczytaj regulamin i baw się dobrze!",
                color=discord.Color.blue()
            )
            # Dodaje awatar użytkownika do powitania
            embed.set_thumbnail(url=member.display_avatar.url)
            # Pokazuje, którym użytkownikiem jest dana osoba
            embed.set_footer(text=f"Jesteś naszym {len(member.guild.members)} członkiem!")

            await channel.send(content=f"Hej {member.mention}!", embed=embed)

async def setup(bot):
    await bot.add_cog(Powitania(bot))
