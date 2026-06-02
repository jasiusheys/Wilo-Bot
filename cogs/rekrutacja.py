import discord
from discord.ext import commands
from discord import ui
import json
import os

# --- KONFIGURACJA ---
CATEGORY_ID = 1511466087278051410
CONFIG_FILE = "config_rekrutacja.json"

class RecruitmentModal(ui.Modal, title='Rekrutacja'):
    def __init__(self, title_name):
        super().__init__(title=f"Rekrutacja: {title_name}"[:45])

    q1 = ui.TextInput(label='1. Czy zagrasz cały event? Wiek? Premium?', placeholder='Tak / Wiek / Tak', style=discord.TextStyle.short)
    q2 = ui.TextInput(label='2. Twój nick MC? Czy rozumiesz zakaz cheatów?', placeholder='Np. jasiu_shey , rozumiem', style=discord.TextStyle.short)
    q3 = ui.TextInput(label='3. Co to RP? Scenka z Wilem?', placeholder='RP to... Gdy spotkam Wila...', style=discord.TextStyle.paragraph)
    q4 = ui.TextInput(label='4. Grałeś już u kogoś na eventach?', placeholder='Tak (u kogo) / Nie', style=discord.TextStyle.short)
    q5 = ui.TextInput(label='5. Link do filmu (Mikrofon + POV)', placeholder='Wklej link (Youtube/Medal/Dysk)', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Wysłano! Tworzę ticket...", ephemeral=True)
        category = interaction.guild.get_channel(CATEGORY_ID)
        channel = await interaction.guild.create_text_channel(f"podanie-{interaction.user.name}", category=category)
        
        embed = discord.Embed(title=f"📝 PODANIE - {interaction.user.name}", color=discord.Color.gold())
        embed.add_field(name="1", value=self.q1.value, inline=False)
        embed.add_field(name="2", value=self.q2.value, inline=False)
        embed.add_field(name="3", value=self.q3.value, inline=False)
        embed.add_field(name="4", value=self.q4.value, inline=False)
        embed.add_field(name="5", value=self.q5.value, inline=False)
        
        await channel.send(embed=embed)

class StartView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Złóż podanie na event", style=discord.ButtonStyle.primary, custom_id="start_rec")
    async def button_callback(self, interaction: discord.Interaction, button: ui.Button):
        cfg = {"event_name": "Rekrutacja"} # Uproszczone dla testu
        await interaction.response.send_modal(RecruitmentModal(cfg["event_name"]))

class Rekrutacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(StartView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx, *, nazwa: str):
        await ctx.send(f"🎥 **REKRUTACJA: {nazwa}**\nKliknij poniżej:", view=StartView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
