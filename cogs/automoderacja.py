import discord
from discord.ext import commands
import re
import datetime

class Moderacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # --- KONFIGURACJA ---
        # ID kanału, na który bot ma wysyłać powiadomienia o karach
        self.KARY_CHANNEL_ID = 1147558452131004446
        
        # --- ID RÓL DLA ZWYKŁYCH LINKÓW I SŁÓW ---
        self.MIN_MOD_ROLE_ID = 1470849725065330780
        self.EXCEPTIONAL_ROLE_ID = 1490094494492655868
        
        # --- NOWA KONFIGURACJA DLA GIFÓW ---
        self.GIF_ROLE_ID = 1470145948490666284
        self.ALLOWED_GIF_CHANNELS = [1470146632480854257, 1470146537240924171]
        
        # --- PAMIĘĆ OSTRZEŻEŃ DLA LINKÓW ---
        self.ostrzezenia_uzytkownikow = {}  # Licznik używany tylko dla YT i zaproszeń
        
        # --- REGEXY (FILTRY) ---
        self.INVITE_REGEX = re.compile(
            r"(discord\.(gg|io|me|li)|discordapp\.com\/invite|discord\.com\/invite)\/[a-zA-Z0-9\-]+", 
            re.IGNORECASE
        )
        
        self.YOUTUBE_REGEX = re.compile(
            r"(youtube\.com|youtu\.be|youtube-nocookie\.com)", 
            re.IGNORECASE
        )
        
        # Wykrywanie gifów z Tenora i Giphy
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

        # --- 1. SPRAWDZANIE ZAKAZANYCH SŁÓW ---
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

        # --- 2. SPRAWDZANIE GIFÓW (NATYCHMIASTOWE USUWANIE) ---
        if self.GIF_REGEX.search(message.content):
            if not self.can_send_gifs(message.author, message.channel.id):
                try:
                    await message.delete()
                except Exception as e:
                    print(f"Nie udało się usunąć GIF-a: {e}")
                return  # Przerywamy działanie – GIF znika całkowicie bez kar i komunikatów

        # --- 3. SPRAWDZANIE LINKÓW (DISCORD / YT - SYSTEM Z KARAMI) ---
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
                user_id = message.author.id
                self.ostrzezenia_uzytkownikow[user_id] = self.ostrzezenia_uzytkownikow.get(user_id, 0) + 1
                
                # Drugie przewinienie dla linków -> Przerwa na 1 dzień i log na kanale kar
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
    await bot.add_cog(Moderacja(bot))
