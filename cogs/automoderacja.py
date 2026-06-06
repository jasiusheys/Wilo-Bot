import discord
from discord.ext import commands
import re
import datetime

class AutoModeracja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # --- KONFIGURACJA ---
        self.KARY_CHANNEL_ID = 1147558452131004446
        self.MIN_MOD_ROLE_ID = 1470849725065330780
        self.EXCEPTIONAL_ROLE_ID = 1490094494492655868
        
        # --- CONFIG DLA GIFÓW ---
        self.GIF_ROLE_ID = 1470145948490666284
        self.ALLOWED_GIF_CHANNELS = [1470146632480854257, 1470146537240924171]
        
        # --- PAMIĘĆ LINKÓW I SPAMU ---
        self.ostrzezenia_uzytkownikow = {}  # Licznik dla YT / zaproszeń
        self.historia_spamu = {}            # Pamięć spamu: {user_id: {"text": str, "time": datetime, "messages": list, "channels": set}}
        self.kary_antyspam = {}             # Licznik multispamu użytkownika: {user_id: int}
        
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

        # Jeśli autor ma pełny immunitet, bot niczego nie tyka
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
                # Sprawdź, czy od wysłania pierwszej wiadomości minęło mniej niż 30 sekund
                if (now - dane_uzytkownika["time"]).total_seconds() <= 30:
                    dane_uzytkownika["channels"].add(message.channel.id)
                    dane_uzytkownika["messages"].append(message)
                    
                    # Jeśli ta sama wiadomość pojawiła się na przynajmniej 3 kanałach
                    if len(dane_uzytkownika["channels"]) >= 3:
                        
                        # USUWANIE WSZYSTKICH USZEREGOWANYCH WIADOMOŚCI
                        for msg in dane_uzytkownika["messages"]:
                            try:
                                await msg.delete()
                            except Exception as e:
                                print(f"Nie udało się usunąć jednej z wiadomości spamu: {e}")
                                
                        # Wyliczamy karę (1. raz = 1 godzina, kolejne = 1 dzień)
                        self.kary_antyspam[user_id] = self.kary_antyspam.get(user_id, 0) + 1
                        ile_razy = self.kary_antyspam[user_id]
                        
                        if ile_razy == 1:
                            czas_mutowania = datetime.timedelta(hours=1)
                            str_czasu = "1 godzinę"
                        else:
                            czas_mutowania = datetime.timedelta(days=1)
                            str_czasu = "1 dzień"
                            
                        # Nadajemy timeout
                        try:
                            await message.author.timeout(czas_mutowania, reason="Rozsyłanie spamu na wielu kanałach (30s)")
                            
                            # Wysyłamy log TYLKO na kanał kar
                            if kanal_kar:
                                await kanal_kar.send(
                                    f"🛑 {message.author.mention} otrzymał przerwę na **{str_czasu}**. Powód: Rozsyłanie spamu na wielu kanałach w ciągu 30 sekund. Wszystkie wiadomości zostały wyczyszczone."
                                )
                        except Exception as e:
                            print(f"Błąd nadawania kary za antyspam: {e}")
                            
                        self.historia_spamu[user_id] = None
                        return
                else:
                    # Minęło 30 sekund -> resetujemy licznik spamu
                    self.historia_spamu[user_id] = {
                        "text": czysty_tekst, 
                        "time": now, 
                        "channels": {message.channel.id}, 
                        "messages": [message]
                    }
            else:
                # Zupełnie inny tekst -> zaczynamy mierzyć od nowa
                self.historia_spamu[user_id] = {
                    "text": czysty_tekst, 
                    "time": now, 
                    "channels": {message.channel.id}, 
                    "messages": [message]
                }

        # --- 2. SPRAWDZANIE ZAKAZANYCH SŁÓW ---
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

        # --- 3. SPRAWDZANIE GIFÓW (NATYCHMIASTOWE USUWANIE) ---
        if self.GIF_REGEX.search(message.content):
            if not self.can_send_gifs(message.author, message.channel.id):
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Nie udało się usunąć GIF-a: {e}")
                return

        # --- 4. SPRAWDZANIE LINKÓW (DISCORD / YT - SYSTEM Z KARAMI) ---
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
