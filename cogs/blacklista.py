import discord
from discord.ext import commands
import json
import os

BLACKLIST_FILE = "blacklist.json"
DATA_FILE = "podania.json"

# --- FUNKCJE POMOCNICZE ---
def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE): return {}
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(blacklist, f, ensure_ascii=False, indent=4)

def load_applicants():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if data and isinstance(data[0], list):
                converted = []
                for x in data:
                    if len(x) >= 2:
                        converted.append({"user_id": x[0], "event": x[1].lower(), "status": "OCZEKUJE"})
                return converted
            return data
        except: return []

def save_all_applicants(applicants):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(applicants, f, ensure_ascii=False, indent=4)

# --- KLASA COG ---
class BlacklistaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="blacklista")
    async def komenda_blacklista(self, ctx):
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

    @commands.command(name="blacklista_dodaj")
    @commands.has_permissions(administrator=True)
    async def komenda_dodaj(self, ctx, member: discord.Member, *, powod: str = "Brak podanego powodu"):
        blacklist = load_blacklist()
        applicants = load_applicants()
        
        blacklist[str(member.id)] = powod
        # Usuwanie z listy podań
        applicants = [x for x in applicants if x['user_id'] != member.id]
        # Usuwanie kanałów podania
        for channel in ctx.guild.channels:
            if hasattr(channel, 'topic') and channel.topic and str(member.id) in channel.topic:
                try: await channel.delete()
                except: pass
        
        save_blacklist(blacklist)
        save_all_applicants(applicants)
        
        await ctx.send(f"✅ Zablokowano użytkownika {member.mention}.\n**Powód:** {powod}")

    @commands.command(name="blacklista_usun")
    @commands.has_permissions(administrator=True)
    async def komenda_usun(self, ctx, member: discord.Member):
        blacklist = load_blacklist()
        if str(member.id) in blacklist:
            del blacklist[str(member.id)]
            save_blacklist(blacklist)
            await ctx.send(f"✅ Odblokowano użytkownika {member.mention}.")
        else:
            await ctx.send("ℹ️ Ten użytkownik nie jest na czarnej liście.")

    @commands.command(name="blacklista_usunall")
    @commands.has_permissions(administrator=True)
    async def komenda_usunall(self, ctx):
        if not load_blacklist():
            return await ctx.send("ℹ️ Blacklista jest już pusta.")
        save_blacklist({}) 
        await ctx.send("✅ Blacklista została wyczyszczona.")

async def setup(bot):
    await bot.add_cog(BlacklistaCog(bot))
