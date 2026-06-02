import discord
from discord.ext import commands
from discord import ui
import json
import os
import asyncio

# --- KONFIGURACJA ---
CATEGORY_ID = 1511466087278051410
CONFIG_FILE = "config_rekrutacja.json"
DATA_FILE = "podania.json"

def load_config():
    if not os.path.exists(CONFIG_FILE): return {"event_name": "Rekrutacja"}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)

# --- FORMULARZ (Naprawione wcięcia i etykiety < 45 znaków) ---
class RecruitmentModal(ui.Modal, title='Formularz Rekrutacji'):
    q1 = ui.TextInput(label='1. Cały event? | Wiek? | Premium?', placeholder='Tak, 16, Tak', style=discord.TextStyle.short)
    q2 = ui.TextInput(label='2. Twój nick MC? | Zakaz cheatów?', placeholder='Np. jasiu_shey, rozumiem', style=discord.TextStyle.short)
    q3 = ui.TextInput(label='3. Czym jest RP? | Scenka z Wilem?', placeholder='RP to..., Gdy spotkam Wila...', style=discord.TextStyle.paragraph)
    q4 = ui.TextInput(label='4. Grałeś już na takich eventach?', placeholder='Np. Tak, u Ciebie / Nie', style=discord.TextStyle.short)
    q5 = ui.TextInput(label='5. Link do filmu (Mikrofon + POV)', placeholder='Wklej link (YT/Medal/Dysk)', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Wysłano! Sprawdź listę kanałów.", ephemeral=True)
        
        category = interaction.guild.get_channel(CATEGORY_ID)
        channel = await interaction.guild.create_text_channel(
            name=f"podanie-{interaction.user.name}",
            category=category,
            overwrites={
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )
        
        embed = discord.Embed(title=f"📝 Podanie - {interaction.user.name}", color=discord.Color.gold())
        embed.add_field(name="1. Info", value=self.q1.value, inline=False)
        embed.add_field(name="2. Nick/Zasady", value=self.q2.value, inline=False)
        embed.add_field(name="3. RP/Scenka", value=self.q3.value, inline=False)
        embed.add_field(name="4. Historia", value=self.q4.value, inline=False)
        embed.add_field(name="5. Linki", value=self.q5.value, inline=False)
        
        await channel.send(f"🛡️ **Panel Decyzji:** {interaction.user.mention}")
        await channel.send(embed=embed)

# --- RESZTA KODU (StartView itp.) ---
class StartView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Złóż podanie", style=discord.ButtonStyle.primary, custom_id="persistent_view:start_rec")
    async def button_click(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RecruitmentModal())

class Rekrutacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(StartView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx, *, nazwa: str):
        embed = discord.Embed(title=f"🎥 REKRUTACJA: {nazwa.upper()}", description="Kliknij przycisk poniżej!", color=discord.Color.gold())
        await ctx.send(embed=embed, view=StartView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
