import discord
from discord.ext import commands
from discord import ui
import json
import os

# --- KONFIGURACJA ---
ADMIN_ROLE_ID = 1511396320173359144
CATEGORY_ID = 1511466087278051410
DATA_FILE = "podania.json"

# --- ZARZĄDZANIE DANYMI ---
def save_applicant(user_id):
    applicants = []
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try: applicants = json.load(f)
            except: applicants = []
    if user_id not in applicants:
        applicants.append(user_id)
        with open(DATA_FILE, "w") as f: json.dump(applicants, f)

# --- MODAL ---
class RecruitmentModal(ui.Modal, title='Formularz Rekrutacji'):
    q1 = ui.TextInput(label='1. Cały event, wiek, premium?', placeholder='Tak, 16, Tak', style=discord.TextStyle.short)
    q2 = ui.TextInput(label='2. Nick MC + zgoda na zakaz cheatów', placeholder='Nick: ..., Zgadzam się', style=discord.TextStyle.short)
    q3 = ui.TextInput(label='3. Co to RP? + Scenka: spotkanie Wila', placeholder='RP to..., Gdy spotkam Wila...', style=discord.TextStyle.paragraph)
    q4 = ui.TextInput(label='4. Grałeś już u kogoś na eventach?', placeholder='Np. Tak, u X, albo Nie', style=discord.TextStyle.short)
    q5 = ui.TextInput(label='5. Link do filmu (Mikrofon + POV)', placeholder='Wklej link (YT/Medal/Dysk)', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        # Szybka odpowiedź, aby uniknąć błędu 3 sekund
        await interaction.response.send_message("✅ Podanie wysłane! Tworzę ticket...", ephemeral=True)
        
        save_applicant(interaction.user.id)
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
        embed.add_field(name="2. Nick", value=self.q2.value, inline=False)
        embed.add_field(name="3. RP/Scenka", value=self.q3.value, inline=False)
        embed.add_field(name="4. Doświadczenie", value=self.q4.value, inline=False)
        embed.add_field(name="5. Film", value=self.q5.value, inline=False)
        
        # Przyciski decyzji dla adminów
        view = ui.View(timeout=None)
        # Tu uprościłem logikę, żeby nie tworzyć dodatkowych klas wewnątrz
        await channel.send(f"🛡️ **Panel Decyzji dla:** {interaction.user.mention}")
        await channel.send(embed=embed)

# --- PRZYCISK STARTOWY (Persistent) ---
class StartView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Złóż podanie", style=discord.ButtonStyle.primary, custom_id="persistent_view:start_rec")
    async def button_click(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RecruitmentModal())

# --- KOG ---
class Rekrutacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # To rejestruje przycisk na stałe, żeby działał po restarcie
        self.bot.add_view(StartView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx, *, nazwa: str):
        if os.path.exists(DATA_FILE): os.remove(DATA_FILE)
        embed = discord.Embed(title=f"🎥 REKRUTACJA: {nazwa.upper()}", description="Kliknij przycisk poniżej!", color=discord.Color.gold())
        await ctx.send(embed=embed, view=StartView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
