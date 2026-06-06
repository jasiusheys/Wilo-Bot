import discord
from discord.ext import commands
import re
import datetime

class AutoModeracja(commands.Cog, name="AutoModeracjaWilo"):
    def __init__(self, bot):
        self.bot = bot
        
        # --- KONFIGURACJA ---
        self.KARY_CHANNEL_ID = 1147558452131004446
        self.MIN_MOD_ROLE_ID = 1470849725065330780
        self.EXCEPTIONAL_ROLE_ID = 1490094494492655868
        self.ZAKAZ_PINGU_ROLE_ID = 1242180257864486962
        
        # --- PAMIĘĆ ---
        self.historia_spamu = {}
        self.kary_antyspam = {}
        self.liczb_pingow = {}
        self.kary_pingowanie = {}
        
        # --- REGEXY ---
        self.INVITE_REGEX = re.compile(r"(discord\.(gg|io|me|li)|discordapp\.com\/invite|discord\.com\/invite)\/[a-zA-Z0-9\-]+", re.IGNORECASE)
        self.YOUTUBE_REGEX = re.compile(r"(youtube\.com|youtu\.be|youtube-nocookie\.com)", re.IGNORECASE)
        self.ZAKAZANE_SLOWA = ["cwel", "cfel", "cw3l", "cwiel", "niger", "nigger", "nygus", "dziwka", "dziwke", "dziwki"]

    # --- KOMENDA CLEAR ---
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        try:
            await ctx.channel.purge(limit=amount + 1)
        except: pass

    def can_bypass_everything(self, member: discord.Member) -> bool:
        if member.guild_permissions.administrator: return True
        if self.EXCEPTIONAL_ROLE_ID in [r.id for r in member.roles]: return True
        target_role = member.guild.get_role(self.MIN_MOD_ROLE_ID)
        return any(r.position >= target_role.position for r in member.roles) if target_role else False

    def przygotuj_tekst(self, tekst: str) -> str:
        tekst = tekst.lower()
        for z, l in {'3': 'e', '4': 'a', '@': 'a', '1': 'l', '|': 'l', '0': 'o', 'vv': 'w'}.items(): tekst = tekst.replace(z, l)
        return re.sub(r'[^a-ząćęłńóśźż]', '', tekst)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild or self.can_bypass_everything(message.author):
            return

        kanal_kar = message.guild.get_channel(self.KARY_CHANNEL_ID)
        user_id = message.author.id
        now = datetime.datetime.now(datetime.timezone.utc)

        # --- 1. ANTY-SPAM ---
        if message.content and len(message.content.strip()) > 0:
            czysty_tekst = message.content.strip().lower()
            historia = self.historia_spamu.get(user_id)
            if historia and historia["text"] == czysty_tekst and (now - historia["time"]).total_seconds() <= 30:
                historia["channels"].add(message.channel.id)
                historia["messages"].append(message)
                if len(historia["channels"]) >= 3:
                    for msg in historia["messages"]: 
                        try: await msg.delete()
                        except: pass
                    self.kary_antyspam[user_id] = self.kary_antyspam.get(user_id, 0) + 1
                    ile = self.kary_antyspam[user_id]
                    czas = datetime.timedelta(hours=1) if ile == 1 else datetime.timedelta(days=1)
                    try:
                        await message.author.timeout(czas, reason="Spam")
                        if kanal_kar: await kanal_kar.send(f"🛑 {message.author.mention} otrzymał przerwę za spam.")
                    except: pass
                    self.historia_spamu[user_id] = None
                    return
            else:
                self.historia_spamu[user_id] = {"text": czysty_tekst, "time": now, "channels": {message.channel.id}, "messages": [message]}

        # --- 2. ZAKAZANE PINGI (bez karania za odpowiedzi) ---
        if not message.reference and message.mentions:
            rola_graniczna = message.guild.get_role(self.ZAKAZ_PINGU_ROLE_ID)
            if rola_graniczna:
                ile_pingow = sum(1 for o in message.mentions if not o.bot and o.id != user_id and any(r.position >= rola_graniczna.position for r in o.roles))
                if ile_pingow > 0:
                    self.liczb_pingow[user_id] = self.liczb_pingow.get(user_id, 0) + ile_pingow
                    obecne = self.liczb_pingow[user_id]
                    if obecne >= 3 or ile_pingow > 5:
                        try: await message.delete()
                        except: pass
                        self.kary_pingowanie[user_id] = self.kary_pingowanie.get(user_id, 0) + 1
                        poziom = self.kary_pingowanie[user_id]
                        czas = [datetime.timedelta(minutes=5), datetime.timedelta(hours=1), datetime.timedelta(days=1)][min(poziom-1, 2)]
                        try:
                            await message.author.timeout(czas, reason="Nagminne pingowanie")
                            if kanal_kar: await kanal_kar.send(f"🛑 {message.author.mention} otrzymał przerwę za pingowanie.")
                        except: pass
                        self.liczb_pingow[user_id] = 0
                        return

        # --- 3. WULGARYZMY I LINKI ---
        if any(slowo in self.przygotuj_tekst(message.content) for slowo in self.ZAKAZANE_SLOWA) or self.INVITE_REGEX.search(message.content) or self.YOUTUBE_REGEX.search(message.content):
            try: await message.delete()
            except: pass

async def setup(bot):
    await bot.add_cog(AutoModeracja(bot))
