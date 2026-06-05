import discord
from discord.ext import commands
import re
import datetime

class AutoModeracja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # --- KONFIGURACJA ---
        # ID kanału, na który bot ma wysyłać powiadomienia o karach (timeoutach)
        self.KARY_CHANNEL_ID = 1147558452131004446
        
        # ID roli, od której w górę (w hierarchii serwera) można wysyłać linki i pisać wszystko
        self.MIN_MOD_ROLE_ID = 1470849725065330780
        
        # ID JEDNEJ konkretnej niższej roli, która też ma wyjątek
        self.EXCEPTIONAL_ROLE_ID = 1490094494492655868
        
        # --- PAMIĘĆ OSTRZEŻEŃ DLA LINKÓW ---
        self.linki_ostrzezenia = {}
        
        # --- REGEXY (LINKI i FILTRY) ---
        self.INVITE_REGEX = re.compile(
            r"(discord\.(gg|io|me|li)|discordapp\.com\/invite|discord\.com\/invite)\/[a-zA-Z0-9\-]+", 
            re.IGNORECASE
        )
        
        self.YOUTUBE_REGEX = re.compile(
            r"(youtube\.com|youtu\.be|youtube-nocookie\.com)", 
            re.IGNORECASE
        )

        # --- CZARNA LISTA SŁÓW ---
        self.ZAKAZANE_SLOWA = [
            "cwel", "cfel", "cw3l", "cwiel",
            "niger", "nigger", "nygus",
            "dziwka", "dziwke", "dziwki"
        ]

    def can_bypass_moderation(self, member: discord.Member) -> bool:
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

    def przygotuj_tekst(self, tekst: str) -> str:
        """Funkcja czyszcząca tekst z zamienników liter i znaków specjalnych"""
        tekst = tekst.lower()
        zamienniki = {
            '3': 'e', '4': 'a', '@': 'a', '1': 'l', '|': 'l', '0': 'o', 'vv': 'w'
        }
        for znak, litera in zamienniki.items():
            tekst = tekst.replace(znak, litera)
            
        tekst = re.sub(r'[^a-ząćęłńóśźż]', '', tekst)
        return tekst

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignoruj boty i DM
        if message.author.bot or not message.guild:
            return

        # Jeśli autor ma immunitet, bot niczego nie sprawdza
        if self.can_bypass_moderation(message.author):
            return

        # Pobieramy kanał do kar
        kanal_kar = message.guild.get_channel(self.KARY_CHANNEL_ID)

        # --- 1. SPRAWDZANIE ZAKAZANYCH SŁÓW ---
        oczyszczony_tekst = self.przygotuj_tekst(message.content)
        
        for slowo in self.ZAKAZANE_SLOWA:
            if slowo in oczyszczony_tekst:
                try:
                    await message.delete()
                    
                    # Nadanie przerwy na 5 minut
                    czas_timeoutu = datetime.timedelta(minutes=5)
                    await message.author.timeout(czas_timeoutu, reason="Używanie zakazanego słownictwa")
                    
                    # Wysyłanie powiadomienia na dedykowany kanał kar
                    if kanal_kar:
                        await kanal_kar.send(
                            f"🛑 {message.author.mention} otrzymał przerwę na **5 minut**. Powód: Używanie zakazanego słownictwa na kanale {message.channel.mention}."
                        )
                    return
                except Exception as e:
                    print(f"Błąd auto-mod (słowa/timeout): {e}")
                    return

        # --- 2. SPRAWDZANIE LINKÓW (DISCORD / YT) ---
        powod_blokady = None

        if self.INVITE_REGEX.search(message.content):
            powod_blokady = "zakaz reklamowania innych projektów"
        elif self.YOUTUBE_REGEX.search(message.content):
            powod_blokady = "zakaz wysyłania linków do YouTube"

        if powod_blokady:
            try:
                await message.delete()
                
                user_id = message.author.id
                self.linki_ostrzezenia[user_id] = self.linki_ostrzezenia.get(user_id, 0) + 1
                
                # Drugie przewinienie -> Timeout na 1 dzień i wpis na kanał kar
                if self.linki_ostrzezenia[user_id] >= 2:
                    czas_timeoutu_linki = datetime.timedelta(days=1)
                    await message.author.timeout(czas_timeoutu_linki, reason="Nagminne wysyłanie zakazanych linków")
                    
                    if kanal_kar:
                        await kanal_kar.send(
                            f"🛑 {message.author.mention} otrzymał przerwę na **1 dzień** za ponowne złamanie zakazu wysyłania linków na kanale {message.channel.mention}!"
                        )
                    self.linki_ostrzezenia[user_id] = 0
                    
                # Pierwsze przewinienie -> Ostrzeżenie na czacie, gdzie wysłano link
                else:
                    await message.channel.send(
                        f"⚠️ {message.author.mention}, na tym serwerze obowiązuje {powod_blokady}! Kolejna próba skończy się przerwą na 1 dzień."
                    )
                    
            except Exception as e:
                print(f"Błąd auto-mod (linki/timeout): {e}")

async def setup(bot):
    await bot.add_cog(AutoModeracja(bot))
