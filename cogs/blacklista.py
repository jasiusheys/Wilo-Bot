import discord
from discord.ext import commands
import json
import os

BLACKLIST_FILE = "blacklist.json"

def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE): return {}
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(blacklist, f, ensure_ascii=False, indent=4)

class BlacklistaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ban_rekrutacja(self, ctx, *, args: str):
        members = ctx.message.mentions
        if not members: return await ctx.send("❌ Musisz oznaczyć przynajmniej jedną osobę!")
        
        powod = args
        for member in members:
            powod = powod.replace(f"<@{member.id}>", "").replace(f"<@!{member.id}>", "")
        powod = powod.strip() or "Brak podanego powodu"

        try:
            blacklist = load_blacklist()
            # Tutaj musisz mieć też dostęp do load_applicants, 
            # najlepiej importuj je z głównego pliku lub trzymaj funkcje w osobnym 'utils.py'
            zbanowani = []
            for member in members:
                blacklist[str(member.id)] = powod
                zbanowani.append(member.mention)
            save_blacklist(blacklist)
            
            embed = discord.Embed(title="✅ Zablokowano użytkowników", color=discord.Color.red())
            embed.add_field(name="Osoby", value=", ".join(zbanowani), inline=False)
            embed.add_field(name="Powód", value=powod, inline=False)
            await ctx.send(embed=embed)
        except Exception as e: await ctx.send(f"⚠️ Wystąpił błąd: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unban_rekrutacja(self, ctx, members: commands.Greedy[discord.Member]):
        if not members: return await ctx.send("❌ Musisz oznaczyć przynajmniej jedną osobę!")
        blacklist = load_blacklist()
        odbanowani = []
        for member in members:
            if str(member.id) in blacklist:
                del blacklist[str(member.id)]
                odbanowani.append(member.mention)
        save_blacklist(blacklist)
        if odbanowani: await ctx.send(f"✅ Odblokowano: {', '.join(odbanowani)}.")
        else: await ctx.send("ℹ️ Żaden z oznaczonych użytkowników nie był na liście.")

    @commands.command()
    async def blacklista(self, ctx):
        blacklist = load_blacklist()
        if not blacklist: return await ctx.send("ℹ️ Blacklista jest pusta.")
        embed = discord.Embed(title="🚫 Blacklista Rekrutacji", color=discord.Color.dark_red())
        text = ""
        for user_id, powod in blacklist.items():
            user = self.bot.get_user(int(user_id))
            name = user.name if user else f"ID: {user_id}"
            text += f"• **{name}**: {powod}\n"
        embed.description = text
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def rekrutacja_uball(self, ctx):
        blacklist = load_blacklist()
        if not blacklist:
            return await ctx.send("ℹ️ Blacklista jest już pusta.")
        save_blacklist({}) 
        await ctx.send("✅ Blacklista została wyczyszczona.")

async def setup(bot):
    await bot.add_cog(BlacklistaCog(bot))
