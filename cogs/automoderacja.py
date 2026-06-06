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

        # Jeśli autor ma pełny immunitet (Admin/Mod+), bot całkowicie ignoruje sprawdzanie
        if self.can_bypass_everything(message.author):
            return

        kanal_kar = message.guild.get_channel(self.KARY_CHANNEL_ID)
        user_id = message.author.id
        now = datetime.datetime.now(datetime.timezone.utc)

        # --- 1. DETEKCJA ANTY-SPAMU (3 takie same wiadomości na min. 3 kanałach w 30s) ---
        if message.content and len(message.content.strip()) > 0:
            czysty_tekst = message.content.strip().lower()
            dane_uzytkownika = self.historia_spamu.get(user_id)
            
            if dane_uzytkownika and dane_uzytkownika["text"] == czysty_tekst:
                if (now - dane_uzytkownika["time"]).total_seconds() <= 30:
                    dane_uzytkownika["channels"].add(message.channel.id)
                    dane_uzytkownika["messages"].append(message)
                    
                    if len(dane_uzytkownika["channels"]) >= 3:
                        for msg in dane_uzytkownika["messages"]:
                            try:
                                await msg.delete()
                            except Exception as e:
                                print(f"Nie udało się usunąć jednej z wiadomości spamu: {e}")
                                
                        self.kary_antyspam[user_id] = self.kary_antyspam.get(user_id, 0) + 1
                        ile_razy = self.kary_antyspam[user_id]
                        
                        if ile_razy == 1:
                            czas_mutowania = datetime.timedelta(hours=1)
                            str_czasu = "1 godzinę"
                        else:
                            czas_mutowania = datetime.timedelta(days=1)
                            str_czasu = "1 dzień"
                            
                        try:
                            await message.author.timeout(czas_mutowania, reason="Rozsyłanie spamu na wielu kanałach (30s)")
                            if kanal_kar:
                                await kanal_kar.send(
                                    f"🛑 {message.author.mention} otrzymał przerwę na **{str_czasu}**. Powód: Rozsyłanie spamu na wielu kanałach w ciągu 30 sekund. Wszystkie wiadomości zostały wyczyszczone."
                                )
                        except Exception as e:
                            print(f"Błąd nadawania kary za antyspam: {e}")
                            
                        self.historia_spamu[user_id] = None
                        return
                else:
                    self.historia_spamu[user_id] = {
                        "text": czysty_tekst, 
                        "time": now, 
                        "channels": {message.channel.id}, 
                        "messages": [message]
                    }
            else:
                self.historia_spamu[user_id] = {
                    "text": czysty_tekst, 
                    "time": now, 
                    "channels": {message.channel.id}, 
                    "messages": [message]
                }

        # --- 2. DETEKCJA ZAKAZANYCH PINGÓW ---
        if message.mentions:
            rola_graniczna = message.guild.get_role(self.ZAKAZ_PINGU_ROLE_ID)
            if rola_graniczna:
                ile_zakazanych_pingow = 0
                
                # Zliczamy każdy nielegalny ping z tej wiadomości
                for oznaczony in message.mentions:
                    if oznaczony.bot or oznaczony.id == user_id:
                        continue
                    
                    ma_wysoka_range = False
                    for rrola in oznaczony.roles:
                        if rrola.position >= rola_graniczna.position:
                            ma_wysoka_range = True
                            break
                            
                    if ma_wysoka_range:
                        wzmianka_id = f"<@{oznaczony.id}>"
                        wzmianka_nick_id = f"<@!{oznaczony.id}>"
                        ilosc_w_tekscie = message.content.count(wzmianka_id) + message.content.count(wzmianka_nick_id)
                        ile_zakazanych_pingow += max(1, ilosc_w_tekscie)
                
                if ile_zakazanych_pingow > 0:
                    self.liczb_pingow[user_id] = self.liczb_pingow.get(user_id, 0) + ile_zakazanych_pingow
                    obecne_pingi = self.liczb_pingow[user_id]
                    
                    # Jeśli przekroczy ogólny próg (3) LUB wyśle bombę powyżej 5 pingów w 1 wiadomości
                    if obecne_pingi >= 3 or ile_zakazanych_pingow > 5:
                        try:
                            await message.delete()
                        except Exception as e:
                            print(f"Błąd usuwania wiadomości z pingiem: {e}")
                            
                        self.kary_pingowanie[user_id] = self.kary_pingowanie.get(user_id, 0) + 1
                        poziom_kary = self.kary_pingowanie[user_id]
                        
                        if poziom_kary == 1:
                            czas_kary = datetime.timedelta(minutes=5)
                            tekst_kary = "5 minut"
                        elif poziom_kary == 2:
                            czas_kary = datetime.timedelta(hours=1)
                            tekst_kary = "1 godzinę"
                        else:
                            czas_kary = datetime.timedelta(days=1)
                            tekst_kary = "1 dzień"
                            
                        try:
                            await message.author.timeout(czas_kary, reason="Nagminne oznaczanie wyższej administracji")
                            
                            await message.channel.send(
                                f"🛑 {message.author.mention} otrzymał przerwę na **{tekst_kary}** za nagminne oznaczanie administracji!"
                            )
                            if kanal_kar:
                                await kanal_kar.send(
                                    f"🛑 {message.author.mention} otrzymał przerwę na **{tekst_kary}**. Powód: Oznaczenie administracji (Wiadomość miała {ile_zakazanych_pingow} pingu/ów, Łącznie na koncie: {obecne_pingi}/3) na kanale {message.channel.mention}."
                                )
                        except Exception as e:
                            print(f"Błąd nadawania kary za pingowanie: {e}")
                            
                        self.liczb_pingow[user_id] = 0
                        return
                        
                    # Zwykłe upomnienia - tekst zostaje na czacie
                    elif obecne_pingi == 1:
                        await message.channel.send(
                            f"⚠️ {message.author.mention}, nie pinguj administracji bez ważnego powodu! (1/3)"
                        )
                    elif obecne_pingi == 2:
                        await message.channel.send(
                            f"⚠️ {message.author.mention}, nie pinguj administracji! Kolejna próba skończy się przerwą. (2/3)"
                        )

        # --- 3. SPRAWDZANIE ZAKAZANYCH SŁÓW ---
        oczyszczony_tekst = self.przygotuj_tekst(message.content)
        for slowo in self.ZAKAZANE_SLOWA:
            if slowo in oczyszczony_tekst:
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Błąd usuwania wulgaryzmu: {e}")

                try:
                    czas_timeoutu = datetime.timedelta(minutes=5)
                    await message.author.timeout(czas_timeoutu, reason="Używanie zakazanego słownictwa")
                    if kanal_kar:
                        await kanal_kar.send(
                            f"🛑 {message.author.mention} otrzymał przerwę na **5 minut**. Powód: Używanie zakazanego słownictwa na kanale {message.channel.mention}."
                        )
                except Exception as e:
                    print(f"Błąd nadawania timeoutu za słowa: {e}")
                return

        # --- 4. SPRAWDZANIE GIFÓW (NATYCHMIASTOWE USUWANIE) ---
        if self.GIF_REGEX.search(message.content):
            if not self.can_send_gifs(message.author, message.channel.id):
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Nie udało się usunąć GIF-a: {e}")
                return

        # --- 5. SPRAWDZANIE LINKÓW (DISCORD / YT - SYSTEM Z KARAMI) ---
        powod_blokady = None

        if self.INVITE_REGEX.search(message.content):
            powod_blokady = "zakaz reklamowania innych projektów"
        elif self.YOUTUBE_REGEX.search(message.content):
            powod_blokady = "zakaz wysyłania linków do YouTube"

        if powod_blokady:
            try:
                await message.delete()
            except Exception as e:
                print(f"Nie udało się usunąć wiadomości z linkiem: {e}")
            
            try:
                self.ostrzezenia_uzytkownikow[user_id] = self.ostrzezenia_uzytkownikow.get(user_id, 0) + 1
                
                if self.ostrzezenia_uzytkownikow[user_id] >= 2:
                    czas_timeoutu_media = datetime.timedelta(days=1)
                    await message.author.timeout(czas_timeoutu_media, reason="Nagminne wysyłanie zakazanych linków")
                    
                    if kanal_kar:
                        await kanal_kar.send(
                            f"🛑 {message.author.mention} otrzymał przerwę na **1 dzień** za ponowne złamanie zakazu wysyłania linków na kanale {message.channel.mention}!"
                        )
                    self.ostrzezenia_uzytkownikow[user_id] = 0
                    
            except Exception as e:
                print(f"Błąd logiki karania za linki: {e}")

async def setup(bot):
    await bot.add_cog(AutoModeracja(bot))
