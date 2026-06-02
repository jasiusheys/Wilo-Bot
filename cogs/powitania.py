import discord
from discord.ext import commands

class Powitania(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Twoje ID kanału powitań
        channel_id = 1280541432259678352
        channel = self.bot.get_channel(channel_id)

        if channel:
            # Tworzymy ramkę wizualną wewnątrz opisu
            ramka_gora = "╔════════════════════════╗"
            ramka_dol = "╚════════════════════════╝"
            
            tresc = f"Siema {member.mention}!\nDobrze Cię widzieć u nas.\nRozgość się i baw się dobrze!"

            embed = discord.Embed(
                title="💎 Witaj na serwerze Wilo - Eventy 💎",
                description=f"{ramka_gora}\n\n{tresc}\n\n{ramka_dol}",
                color=discord.Color.blue()
            )
            
            # Dodaje awatar użytkownika po prawej stronie
            embed.set_thumbnail(url=member.display_avatar.url)
            
            # Stopka z licznikiem osób
            embed.set_footer(text=f"Jesteś naszym {len(member.guild.members)} członkiem!")

            # TO BYŁO BRAKUJĄCE OGNIWO:
            await channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Powitania(bot))
