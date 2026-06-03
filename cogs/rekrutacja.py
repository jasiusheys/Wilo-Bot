import discord
from discord.ext import commands
from discord import ui
import json
import os
import asyncio

# --- KONFIGURACJA ---
ADMIN_ROLE_ID = 1511396320173359144
MOD_ACCESS_ROLE_ID = 1511727936515080252  # TWOJA NOWA ROLA DOSTĘPU
CONFIG_FILE = "config_rekrutacja.json"
DATA_FILE = "podania.json"

# LISTA TWOICH TRZECH KATEGORII
CATEGORY_IDS = [
    1511466087278051410,
    1511687027727401010,
    1511687075601317948
]

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_config(event_name, role_id):
    config = load_config()
    config[event_name.lower()] = role_id
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def load_applicants():
    if not os.path.exists(DATA_FILE): return []
    try:
        with open(DATA_FILE, "r") as f: return json.load(f)
    except: return []

def save_applicant(user_id, event_name):
    applicants = load_applicants()
    entry = [user_id, event_name.lower()]
    if entry not in applicants:
        applicants.append(entry)
        with open(DATA_FILE, "w") as f:
            json.dump(applicants, f)

def clear_applicants_for_event(event_name):
    applicants = load_applicants()
    applicants = [x for x in applicants if isinstance(x, list) and x[1] != event_name.lower()]
    with open(DATA_FILE, "w") as f:
        json.dump(applicants, f)

# FUNKCJA SPRAWDZAJĄCA UPRAWNIENIA (Admin lub Nowa Rola)
def has_mod_perms(user):
    user_role_ids = [role.id for role in user.roles]
    return ADMIN_ROLE_ID in user_role_ids or MOD_ACCESS_ROLE_ID in user_role_ids

# --- PANEL DECYZJI ---
class AdminDecisionView(ui.View):
    def __init__(self, applicant_id: int = None, event_name: str = ""):
        super().__init__(timeout=None)
        if applicant_id and event_name:
            self.children[0].custom_id = f"adm_accept:{applicant_id}:{event_name}"
            self.children[1].custom_id = f"adm_deny:{applicant_id}:{event_name}"

    @ui.button(label="Zaakceptuj", style=discord.ButtonStyle.success, emoji="✅", custom_id="adm_accept:init:init")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        if not has_mod_perms(interaction.user):
            return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
        await interaction.response.defer()
        parts = button.custom_id.split(":")
        await wygraj_rekrutacje(interaction.guild, interaction.channel, int(parts[1]), parts[2])

    @ui.button(label="Odrzuć", style=discord.ButtonStyle.danger, emoji="❌", custom_id="adm_deny:init:init")
    async def deny(
