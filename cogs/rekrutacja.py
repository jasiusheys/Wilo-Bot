import discord
from discord.ext import commands
from discord import ui
import json
import os
import asyncio

# --- KONFIGURACJA ---
ADMIN_ROLE_ID = 1511396320173359144
CONFIG_FILE = "config_rekrutacja.json"
DATA_FILE = "podania.json"

# LISTA TWOICH TRZECH KATEGORII
CATEGORY_IDS = [
    1511466087278051410,
    1511687027727401010,
    1511687075601317948
]

# --- WPISZ TUTAJ SAME CYFRY EMOTKI ---
WILO_ID = "TUTAJ_WKLEJ_ID" 

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"event_name": "Rekrutacja", "role_id": None}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(event_name, role_id):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"event_name": event_name, "role_id": role_id}, f, ensure_ascii=False, indent=4)

def load_applicants():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return []

def save_applicant(user_id):
    applicants = load_applicants()
    if user_id not in applicants:
        applicants.append(user_id)
        with open(DATA_FILE, "w") as f:
            json.dump(applicants, f)

def clear_applicants():
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# --- PANEL DECYZJI ---
class AdminDecisionView(ui.View):
    def __init__(self, applicant_id: int = None):
        super().__init__(timeout=None)
        if applicant_id:
            self.children[0].custom_id = f"adm_accept:{applicant_id}"
            self.children[1].custom_id = f"adm_deny:{applicant_id}"

    @ui.button(label="Zaakceptuj", style=discord.ButtonStyle.success, emoji="✅", custom_id="adm_accept:init")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        if ADMIN_ROLE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
        await interaction.response.defer()
        applicant_id = int(button.custom_id.split(":")[1])
        await wygraj_rekrutacje(interaction.guild, interaction.channel, applicant_id)

    @ui.button(label="Odrzuć", style=discord.ButtonStyle.danger, emoji="❌", custom_id="adm_deny:init")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        if ADMIN_ROLE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
        await interaction.response.defer()
        applicant_id = int(button.custom_id.split(":")[1])
        await przegraj_rekrutacje(interaction.guild, interaction.channel, applicant_id)

async def wygraj_rekrutacje(guild, channel, applicant_id):
    applicant = guild.get_member(applicant_id)
    config = load_config()
    if config["role_id"] and applicant:
        role = guild.get_role(int(config["role_id"]))
        if role:
            try: await applicant.add_roles(role)
            except: pass
    if applicant:
        try: await applicant.send(f"✅ Podanie na **{config['event_name']}** zaakceptowane!")
        except: pass
    await channel.send("🟢 Zaakceptowano. Usuwanie kanału...")
    await asyncio.sleep(5)
    await channel.delete()

async def przegraj_rekrutacje(guild, channel, applicant_id):
    applicant = guild.get_member(applicant_id)
    config = load_config()
    if applicant:
        try: await applicant.send(f"❌ Podanie na **{config['event_name']}** odrzucone.")
        except: pass
    await channel.send("🔴 Odrzucono. Usuwanie kanału...")
    await asyncio.sleep(5)
    await channel.delete()

# --- FORMULARZ ---
class RecruitmentModal(ui.Modal):
    def __init__(self):
        # KRÓTKI TYTUŁ, żeby uniknąć błędu "Czynność nie powiodła się"
        super().__init__(title="Formularz Rekrutacyjny")

    q1 = ui.TextInput(label='Wiek / Premium?', style=discord.TextStyle.paragraph, required=True)
    q2 = ui.TextInput(label='Nick MC / Zasady', style=discord.TextStyle.paragraph, required=True)
    q3 = ui.TextInput(label='Czym jest RP?', style=discord.TextStyle.paragraph, required=True)
    q4 = ui.TextInput(label='Doświadczenie', style=discord.TextStyle.paragraph, required=True)
    q5 = ui.TextInput(label='Mikrofon + POV (Link)', style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id in load_applicants():
            return await interaction.response.send_message("❌ Już wysłałeś podanie!", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        selected_category = None
        for cat_id in CATEGORY_IDS:
            cat = interaction.guild.get_channel(cat_id)
            if cat and len(cat.channels) < 50:
                selected_category = cat
                break
        
        if not selected_category:
            return await interaction.followup.send("❌ Brak wolnych miejsc w kategoriach!", ephemeral=True)

        save_applicant(interaction.user.id)
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await interaction.guild.create_text_channel(
            f"podanie-{interaction.user.name}", category=selected_category, overwrites=overwrites, topic=str(interaction.user.id)
        )
        
        ans = discord.Embed(title=f"📝 Podanie: {interaction.user.name}", color=discord.Color.gold())
        ans.add_field(name="Pytanie 1", value=self.q1.value, inline=False)
        ans.add_field(name="Pytanie 2", value=self.q2.value,
