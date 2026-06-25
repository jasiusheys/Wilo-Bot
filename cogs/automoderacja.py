import discord
from discord.ext import commands
import re
import datetime
import json
import os

class AutoModeracja(commands.Cog, name="AutoModeracjaWilo"):
    def __init__(self, bot):
        self.bot = bot
        self.FILE_NAME = "allowed_channels.json"
        
        # --- KONFIGURACJA ---
        self.KARY_CHANNEL_ID = 1147558452131004446
        self.MIN_MOD_ROLE_ID = 1470849725065330780
        self.EXCEPTIONAL_ROLE_ID = 1490094494492655868
        self.ZAKAZ_PINGU_ROLE_ID = 1242180257864486962
        self.ROLE_10LVL_ID = 1470145948490666284
        
        # --- PAMIĘĆ ---
        self.historia_spamu = {}
        self.kary_antyspam = {}
        self.liczb_pingow = {}
        self.kary_pingowanie = {}
        self.ALLOWED_LINK_CHANNELS = self.load_channels()
        
        # --- REGEXY ---
        self.INVITE_REGEX = re.compile(r"(discord\.(gg|io|me|li)|discordapp\.com\/invite|discord\.com\/invite)\/[a-zA-Z0-9\-]+", re.IGNORECASE)
        self.YOUTUBE_REGEX = re.compile(r"(youtube\.com|youtu\.be|youtube-nocookie\.com)", re.IGNORECASE)
        self.ZAKAZANE_SLOWA = ["cwel", "cfel", "cw3l", "cwiel", "niger", "nigger", "nygus", "dziwka", "dziwke", "dziwki"]

    # --- ZARZĄDZANIE PLIKIEM ---
    def load_channels(self):
        if os.path.exists(self.FILE_NAME):
            with open(self.FILE_NAME, "r") as f: return set(json.load(f))
        return set()

    def save_channels(self):
        with open(self.FILE_NAME, "w") as f: json.dump(list(self.ALLOWED_LINK_CHANNELS), f)

    # --- KOMENDY ---
    @commands.command(name="linki_dodaj")
    @commands.has_permissions(administrator=True)
    async def linki_dodaj(self, ctx, channel: discord.TextChannel):
        self.ALLOWED_LINK_CHANNELS.add(channel.id)
        self.save_channels()
        await ctx.send(f"✅ Kanał {channel.mention} został dodany do listy dozwolonych dla linków.")

    @commands.command(name="linki_usun")
    @commands.has_permissions(administrator=True)
    async def linki_usun(self, ctx, channel: discord.TextChannel):
        if channel.id in self.ALLOWED_LINK_CHANNELS:
            self.ALLOWED_LINK_CHANNELS.remove(channel.id)
            self.save_channels()
            await ctx.send(f"✅ Kanał {channel.mention} został usunięty z listy.")
        else:
            await ctx.send("ℹ️ Ten kanał nie był na liście.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int):
        try: await ctx.channel.purge(limit=amount + 1)
        except: pass

    # --- LOGIKA ---
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

        # --- 3. WULGARYZMY, LINKI ORAZ GIF-Y ---
        wulgaryzm = any(slowo in self.przygotuj_tekst(message.content) for slowo in self.ZAKAZANE_SLOWA)
        
        # Sprawdzenie wulgaryzmów zawsze (nawet na dozwolonych kanałach)
        if wulgaryzm:
            try: await message.delete()
            except: pass
            return

        # Jeśli kanał jest na liście dozwolonych, ignorujemy resztę (linki/gif)
        if message.channel.id in self.ALLOWED_LINK_CHANNELS:
            return

        # --- ANTY-SPAM I PINGI ---
        # (Tutaj wstawiasz kod z anty-spamem i pingami, który miałeś wcześniej)
        # ...

        # --- BLOKOWANIE LINKÓW/GIF ---
        has_gif_permission = any(role.id == self.ROLE_10LVL_ID for role in message.author.roles)
        is_gif = any(embed.type == "gifv" for embed in message.embeds)
        has_gif_link = message.content.lower().endswith(".gif")
        is_link = self.INVITE_REGEX.search(message.content) or self.YOUTUBE_REGEX.search(message.content) or "http" in message.content.lower()
        
        if is_link:
            if (is_gif or has_gif_link) and has_gif_permission:
                return
            else:
                try: await message.delete()
                except: pass
        elif is_gif and not has_gif_permission:
            try: await message.delete()
            except: pass

async def setup(bot):
    await bot.add_cog(AutoModeracja(bot))
