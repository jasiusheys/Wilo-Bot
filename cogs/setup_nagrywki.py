import discord
from discord.ext import commands

class SetupNagrywki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.WZOR_KATEGORIA_ID = 1506316808179810364
        self.WZOR_ROLA_ID = 1513320051246370866

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setupnagrywka(self, ctx, nazwa: str, nowa_rola: discord.Role, stara_rola: discord.Role):
        guild = ctx.guild
        kategoria_wzor = guild.get_channel(self.WZOR_KATEGORIA_ID)
        wzor_rola = guild.get_role(self.WZOR_ROLA_ID)
        
        if not kategoria_wzor or not wzor_rola:
            await ctx.send("❌ Błąd: Nie odnaleziono kategorii lub roli wzorcowej!")
            return

        await ctx.send(f"⏳ Tworzę nagrywkę **{nazwa}**...")
        
        nowa_kategoria = await guild.create_category(f"Nagrywka - {nazwa}")
        
        for ch in kategoria_wzor.channels:
            if isinstance(ch, discord.TextChannel):
                nowy_ch = await guild.create_text_channel(ch.name, category=nowa_kategoria)
            elif isinstance(ch, discord.VoiceChannel):
                nowy_ch = await guild.create_voice_channel(ch.name, category=nowa_kategoria)
            else:
                continue
            
            permy_wzoru = ch.overwrites_for(wzor_rola)
            await nowy_ch.set_permissions(nowa_rola, overwrite=permy_wzoru)
            await nowy_ch.set_permissions(stara_rola, view_channel=False, send_messages=False)
            
        await ctx.send(f"✅ Gotowe! Kategoria `{nowa_kategoria.name}` stworzona.")

async def setup(bot):
    await bot.add_cog(SetupNagrywki(bot))
