import discord
from discord.ext import commands

class Moderacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Komenda PING
    @commands.command()
    async def ping(self, ctx):
        await ctx.send(f'🏓 Pong! Opóźnienie: {round(self.bot.latency * 1000)}ms')

    # Komenda KICK (!kick @nick powód)
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        await member.kick(reason=reason)
        await ctx.send(f'✅ Gracz {member.mention} został wyrzucony. Powód: {reason}')

    # Komenda BAN (!ban @nick powód)
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        await member.ban(reason=reason)
        await ctx.send(f'✅ Gracz {member.mention} został zbanowany. Powód: {reason}')

    # Obsługa błędu braku uprawnień
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send('❌ Nie masz uprawnień do używania tej komendy!')

async def setup(bot):
    await bot.add_cog(Moderacja(bot))
import discord
from discord.ext import commands

class Moderacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Komenda clear
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        await ctx.send(f"✅ Usunięto {amount} wiadomości!", delete_after=3)

    # Komendy społecznościowe
    @commands.command(aliases=['youtube', 'yt'])
    async def yt(self, ctx):
        await ctx.send(f"🎥 Sprawdź kanał Wila tutaj: https://youtube.com/@wilo93")

    @commands.command(aliases=['ig'])
    async def instagram(self, ctx):
        await ctx.send(f"📸 Obserwuj Instagram Wila: https://www.instagram.com/hejkatuwilo")

    @commands.command(aliases=['tt'])
    async def tiktok(self, ctx):
        await ctx.send(f"🎵 Zobacz TikToka Wila: https://www.tiktok.com/@hejkatuwilo")

    # Obsługa błędów uprawnień
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ Nie masz uprawnień do używania tej komendy!")

async def setup(bot):
    await bot.add_cog(Moderacja(bot))
