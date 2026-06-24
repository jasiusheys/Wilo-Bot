import discord
from discord.ext import commands
import json
import os
import asyncio

BLACKLIST_FILE = "blacklist.json"
DATA_FILE = "podania.json"
KANAL_BLACKLISTY_ID = 1518407650633580636

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

    # --- AUTOMATYCZNE DODAWANIE PRZEZ OZNACZENIE ---
    @commands.Cog.listener()
    async def on_message(self, message):
        # Sprawdzamy czy autor to nie bot, kanał się zgadza ORAZ autor jest administratorem
        if message.author.bot or message.channel.id != KANAL_BLACKLISTY_ID:
            return
        
        if not message.author.guild_permissions.administrator:
            return

        if message.mentions:
            blacklist = load_blacklist()
            applicants = load_applicants()
            zbanowani_count = 0
            
            for member in message.mentions:
                blacklist[str(member.id)] = "blacklista"
                zbanowani_count += 1
                
                applicants = [x for x in applicants if x['user_id'] != member.id]
                
                for channel in message.guild.channels:
                    if hasattr(channel, 'topic') and channel.topic and str(member.id) in channel.topic:
                        try: 
                            await channel.delete()
                            await asyncio.sleep(0.5) 
                        except: pass
            
            save_blacklist(blacklist)
            save_all_applicants(applicants)
            await message.add_reaction("✅")
            await message.channel.send(f"✅ Dodano {zbanowani_count} osób do blacklisty (Powód: blacklista).")

    # --- KOMENDY ---
    @commands.command(name="blacklista")
    @commands.has_permissions(administrator=True)
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
    async def komenda_dodaj(self, ctx, members: commands.Greedy[discord.Member], *, powod: str = "Brak podanego powodu"):
        if not members:
            return await ctx.send("❌ Musisz oznaczyć przynajmniej jedną osobę!")
        
        blacklist = load_blacklist()
        applicants = load_applicants()
        zbanowani = []
        
        for member in members:
            blacklist[str(member.id)] = powod
            applicants = [x for x in applicants if x['user_id'] != member.id]
            for channel in ctx.guild.channels:
                if hasattr(channel, 'topic') and channel.topic and str(member.id) in channel.topic:
                    try: await channel.delete()
                    except: pass
            zbanowani.append(member.mention)
        
        save_blacklist(blacklist)
        save_all_applicants(applicants)
        await ctx.send(f"✅ Zablokowano {len(members)} użytkowników: {', '.join(zbanowani)}.\n**Powód:** {powod}")

    @commands.command(name="blacklista_usun")
    @commands.has_permissions(administrator=True)
    async def komenda_usun(self, ctx, members: commands.Greedy[discord.Member]):
        if not members:
            return await ctx.send("❌ Musisz oznaczyć przynajmniej jedną osobę!")
            
        blacklist = load_blacklist()
        odbanowani = []
        
        for member in members:
            if str(member.id) in blacklist:
                del blacklist[str(member.id)]
                odbanowani.append(member.mention)
        
        save_blacklist(blacklist)
        if odbanowani:
            await ctx.send(f"✅ Odblokowano: {', '.join(odbanowani)}.")
        else:
            await ctx.send("ℹ️ Żaden z oznaczonych użytkowników nie był na liście.")

    @commands.command(name="blacklista_usunall")
    @commands.has_permissions(administrator=True)
    async def komenda_usunall(self, ctx):
        if not load_blacklist():
            return await ctx.send("ℹ️ Blacklista jest już pusta.")
        save_blacklist({}) 
        await ctx.send("✅ Blacklista została wyczyszczona.")

async def setup(bot):
    await bot.add_cog(BlacklistaCog(bot))
