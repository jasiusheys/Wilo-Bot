import discord
from discord.ext import commands
from discord import ui
import json
import os
import asyncio

# --- KONFIGURACJA ---
ADMIN_ROLE_ID = 1511396320173359144
CATEGORY_ID = 1511466087278051410
CONFIG_FILE = "config_rekrutacja.json"
DATA_FILE = "podania.json"

# --- FUNKCJE ---
def load_config():
    if not os.path.exists(CONFIG_FILE): return {"event_name": "Rekrutacja", "role_id": None}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)

def load_applicants():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE, "r") as f: return json.load(f)

def save_applicant(user_id):
    applicants = load_applicants()
    if user_id not in applicants:
        applicants.append(user_id)
        with open(DATA_FILE, "w") as f: json.dump(applicants, f)

# --- PANEL DECYZJI W TICKETACH ---
class AdminDecisionView(ui.View):
    def __init__(self, applicant):
        super().__init__(timeout=None)
        self.applicant = applicant

    @ui.button(label="Zaakceptuj", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        config = load_config()
        if config["role_id"]:
            role = interaction.guild.get_role(int(config["role_id"]))
            if role: await self.applicant.add_roles(role)
        try: await self.applicant.send(f"✅ Gratulacje! Twoje podanie na **{config['event_name']}** zaakceptowane!")
        except: pass
        await interaction.response.send_message("🟢 Zaakceptowano. Usuwam kanał...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

    @ui.button(label="Odrzuć", style=discord.ButtonStyle.danger, emoji="❌")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("🔴 Odrzucono. Usuwam kanał...")
        await asyncio.sleep(3)
        await interaction.channel.delete()

# --- FORMULARZ ---
class RecruitmentModal(ui.Modal):
    def __init__(self, title_name):
        super().__init__(title=f"Rekrutacja: {title_name}"[:45])

  q1 = ui.TextInput(label='1. Cały event? | Wiek? | MC Premium?', placeholder='Tak / 16 / Tak', style=discord.TextStyle.short)
    # Naprawiony cudzysłów i skrócony tekst
    q2 = ui.TextInput(label='2. Twój nick MC? | Zakaz cheatów?', placeholder='Np. jasiu_shey , rozumiem', style=discord.TextStyle.short)
    # Skrócony tekst (był za długi)
    q3 = ui.TextInput(label='3. Co to RP? | Scenka: spotkanie Wila', placeholder='RP to... Gdy spotkam Wila...', style=discord.TextStyle.paragraph)
    q4 = ui.TextInput(label='4. Grałeś już na takich eventach?', placeholder='Np. Tak, u Ciebie / Nie brałem udziału', style=discord.TextStyle.short)
    # Skrócony tekst
    q5 = ui.TextInput(label='5. Link do filmu (Mikrofon + POV)', placeholder='Wklej linki do filmu i screena suba', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Wysłano! Tworzę Twój ticket...", ephemeral=True)
        save_applicant(interaction.user.id)
        
        category = interaction.guild.get_channel(CATEGORY_ID)
        channel = await interaction.guild.create_text_channel(
            f"podanie-{interaction.user.name}", category=category,
            overwrites={interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                        interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        )
        
        ans = discord.Embed(title=f"📝 TREŚĆ PODANIA - {interaction.user.name}", color=discord.Color.gold())
        ans.add_field(name="1. Info", value=self.q1.value, inline=False)
        ans.add_field(name="2. Dane", value=self.q2.value, inline=False)
        ans.add_field(name="3. RP/Scenka", value=self.q3.value, inline=False)
        ans.add_field(name="4. Historia", value=self.q4.value, inline=False)
        ans.add_field(name="5. Dowody", value=self.q5.value, inline=False)
        
        await channel.send(f"🛡️ **Panel Decyzji:** {interaction.user.mention}", view=AdminDecisionView(interaction.user))
        await channel.send(embed=ans)

# --- GŁÓWNY WIDOK PRZYCISKU ---
class StartView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Złóż podanie na event", style=discord.ButtonStyle.primary, custom_id="start_rec")
    async def button_callback(self, interaction: discord.Interaction, button: ui.Button):
        cfg = load_config()
        if interaction.user.id in load_applicants():
            return await interaction.response.send_message("❌ Już wysłałeś podanie!", ephemeral=True)
        await interaction.response.send_modal(RecruitmentModal(cfg["event_name"]))

# --- KOG ---
class Rekrutacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self
