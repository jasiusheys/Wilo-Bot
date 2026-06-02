import discord
from discord.ext import commands

class Moderacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Komendy podstawowe
    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'🏓 Pong! Opóźnienie: {round(self.bot.latency * 1000)}ms')

    # Komendy moderacyjne
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f'✅ Gracz {member.mention} został wyrzucony. Powód: {reason}')

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f'✅ Gracz {member.mention} został zbanowany. Powód: {reason}')

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"✅ Usunięto {amount} wiadomości!", delete_after=3)

    # Komendy społecznościowe z unikalnymi aliasami
    @commands.command(aliases=['linkyt'])
    async def yt(self, ctx):
        await ctx.send(f"🎥 Sprawdź kanał Wila tutaj: https://youtube.com/@wilo93")

    @commands.command(aliases=['linkig'])
    async def instagram(self, ctx):
        await ctx.send(f"📸 Obserwuj Instagram Wila: https://www.instagram.com/hejkatuwilo")

    @commands.command(aliases=['linktt'])
    async def tiktok(self, ctx):
        await ctx.send(f"🎵 Zobacz TikToka Wila: https://www.tiktok.com/@hejkatuwilo")

    # Obsługa błędów
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Nie masz uprawnień do używania tej komendy!")

async def setup(bot):
    await bot.add_cog(Moderacja(bot))
