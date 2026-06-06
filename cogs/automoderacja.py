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
        
        # --- ZAKAZ PINGOWANIA ---
        self.ZAKAZ_PINGU_ROLE_ID = 1242180257864486962  # Od tej roli w górę nie wolno pingować
        
        # --- CONFIG DLA GIFÓW ---
        self.GIF_ROLE_ID = 1470145948490666284
        self.ALLOWED_GIF_CHANNELS = [1470146632480854257, 1470146537240924171]
        
        # --- PAMIĘĆ LINKÓW, SPAMU I PINGÓW ---
        self.ostrzezenia_uzytkownikow = {}  # Licznik dla YT / zaproszeń
        self.historia_spamu = {}            # Pamięć spamu: {user_id: {"text": str, "time": datetime, "messages": list, "channels": set}}
        self.kary_antyspam = {}             # Licznik multispamu użytkownika: {user_id: int}
        self.liczb_pingow = {}              # Licznik nielegalnych pingów: {user_id: int}
        self.kary_pingowanie = {}           # Licznik kolejnych kar za pingi
        
        # --- REGEXY (FILTRY) ---
        self.INVITE_REGEX = re.compile(
            r"(discord\.(gg|io|me|li)|discordapp\.com\/invite|discord\.com\/invite)\/[a-zA-Z0-9\-]+", 
            re.IGNORECASE
        )
        self.YOUTUBE_REGEX = re.compile(
            r"(youtube\.com|youtu\.be|youtube-nocookie\.com)", 
            re.IGNORECASE
        )
        self.GIF_REGEX = re.compile(
            r"(tenor\.com|giphy\.com)", 
            re.IGNORECASE
        )

        # --- CZARNA LISTA SŁÓW ---
        self.ZAKAZANE_SLOWA = [
            "cwel", "cfel", "cw3l", "cwiel",
            "niger", "nigger", "nygus",
            "dziwka", "dziwke", "dziwki"
        ]

    # --- KOMENDA CLEAR ---
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        """Usuwa określoną liczbę wiadomości"""
        if amount < 1:
            await ctx.send("Podaj liczbę większą niż 0!")
            return
            
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)
            msg = await ctx.send(f"✅ Usunięto {len(deleted)-1} wiadomości.")
            await msg.delete(delay=3)
        except Exception as e:
            await ctx.send(f"Błąd przy czyszczeniu: {e}")

    def can_bypass_everything(self, member: discord.Member) -> bool:
        """Sprawdza, czy użytkownik ma absolutny immunitet na wszystko (Mod+, Admin, Wyjątek)"""
        if member.guild_permissions.administrator:
            return True
            
        user_role_ids = [role.id for role in member.roles]
        if self.EXCEPTIONAL_ROLE_ID in user_role_ids:
            return True
            
        target_role = member.guild.get_role(self.MIN_MOD_ROLE_ID)
        if target_role:
            for role in member.roles:
                if role.position >= target_role.position:
                    return True
        return False

    def can_send_gifs(self, member: discord.Member, channel_id: int) -> bool:
        """Dedykowana funkcja sprawdzająca uprawnienia do wysyłania GIF-ów"""
        if self.can_bypass_everything(member):
            return True
            
        user_role_ids = [role.id for role in member.roles]
        if self.GIF_ROLE_ID in user_role_ids:
            if channel_id in self.ALLOWED_GIF_CHANNELS:
                return True
                
        return False

    def przygotuj_tekst(self, tekst: str) -> str:
        tekst = tekst.lower()
        zamienniki = {'3': 'e', '4': 'a', '@': 'a', '1': 'l', '|': 'l', '0': 'o', 'vv': 'w'}
        for znak, litera in zamienniki.items():
            tekst = tekst.replace(znak, litera)
        tekst = re.sub(r'[^a-ząćęłńóśźż]', '', tekst)
        return tekst

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        if self.can_bypass_everything(message.author):
            return

        kanal_kar = message.guild.get_channel(self.KARY_CHANNEL_ID)
        user_id = message.author.id
        now = datetime.datetime.now(datetime.timezone.utc)

        # --- 1. DETEKCJA ANTY-SPAMU ---
        if message.content and len(message.content.strip()) > 0:
            czysty_tekst = message.content.strip().lower()
            dane_uzytkownika = self.historia_spamu.get(user_id)
            
            if dane_uzytkownika and dane_uzytkownika["text"] == czysty_tekst:
                if (now - dane_uzytkownika["time"]).total_seconds() <= 30:
                    dane_uzytkownika["channels"].add(message.channel.id)
                    dane_uzytkownika["messages"].append(message)
                    
                    if len(dane_uzytkownika["channels"]) >= 3:
                        for msg in dane_uzytkownika["messages"]:
                            try: await msg.delete()
                            except: pass
                                
                        self.kary_antyspam[user_id] = self.kary_antyspam.get(user_id, 0) + 1
                        ile_razy = self.kary_antyspam[user_id]
                        
                        czas_mutowania = datetime.timedelta(hours=1) if ile_razy == 1 else datetime.timedelta(days=1)
                        str_czasu = "1 godzinę" if ile_razy == 1 else "1 dzień"
                            
                        try:
                            await message.author.timeout(czas_mutowania, reason="Rozsyłanie spamu")
                            if kanal_kar:
                                await kanal_kar.send(f"🛑 {message.author.mention} otrzymał przerwę na **{str_czasu}** za spam.")
                        except: pass
                            
                        self.historia_spamu[user_id] = None
                        return
                else:
                    self.historia_spamu[user_id] = {"text": czysty_tekst, "time": now, "channels": {message.channel.id}, "messages": [message]}
            else:
                self.historia_spamu[user_id] = {"text": czysty_tekst, "time": now, "channels": {message.channel.id}, "messages": [message]}

        # --- 2. DETEKCJA ZAKAZANYCH PINGÓW ---
        if message.mentions:
            rola_graniczna = message.guild.get_role(self.ZAKAZ_PINGU_ROLE_ID)
            if rola_graniczna:
                ile_zakazanych_pingow = 0
                for oznaczony in message.mentions:
                    if oznaczony.bot or oznaczony.id == user_id: continue
                    ma_wysoka_range = any(rrola.position >= rola_graniczna.position for rrola in oznaczony.roles)
                    if ma_wysoka_range:
                        ilosc_w_tekscie = message.content.count(f"<@{oznaczony.id}>") + message.content.count(f"<@!{oznaczony.id}>")
                        ile_zakazanych_pingow += max(1, ilosc_w_tekscie)
                
                if ile_zakazanych_pingow > 0:
                    self.liczb_pingow[user_id] = self.liczb_pingow.get(user_id, 0) + ile_zakazanych_pingow
                    obecne_pingi = self.liczb_pingow[user_id]
                    
                    if obecne_pingi >= 3 or ile_zakazanych_pingow > 5:
                        try: await message.delete()
                        except: pass
                            
                        self.kary_pingowanie[user_id] = self.kary_pingowanie.get(user_id, 0) + 1
                        poziom = self.kary_pingowanie[user_id]
                        czas = [datetime.timedelta(minutes=5), datetime.timedelta(hours=1), datetime.timedelta(days=1)][min(poziom-1, 2)]
                        tekst = ["5 minut", "1 godzinę", "1 dzień"][min(poziom-1, 2)]
                            
                        try:
                            await message.author.timeout(czas, reason="Nagminne pingowanie")
                            await message.channel.send(f"🛑 {message.author.mention} otrzymał przerwę na **{tekst}** za pingowanie!")
                        except: pass
                        self.liczb_pingow[user_id] = 0
                        return
                    elif obecne_pingi == 1: await message.channel.send(f"⚠️ {message.author.mention}, nie pinguj administracji! (1/3)")
                    elif obecne_pingi == 2: await message.channel.send(f"⚠️ {message.author.mention}, nie pinguj administracji! Ostatnie ostrzeżenie. (2/3)")

        # --- 3. POZOSTAŁE FILTRY (SŁOWA, GIF, LINKI) ---
        # ... (kod pozostałych filtrów bez zmian)

async def setup(bot):
    await bot.add_cog(AutoModeracja(bot))
