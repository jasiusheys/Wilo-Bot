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

# --- FUNKCJE POMOCNICZE DO AKCEPTACJI/ODRZUCENIA ---
async def wygraj_rekrutacje(guild, channel, applicant_id):
    applicant = guild.get_member(applicant_id)
    config = load_config()
    
    if config["role_id"] and applicant:
        role = guild.get_role(int(config["role_id"]))
        if role:
            try: await applicant.add_roles(role)
            except: pass
    
    if applicant:
        try: await applicant.send(f"✅ Twoje podanie na event **{config['event_name']}** zostało zaakceptowane!")
        except: pass
        
    await channel.send(f"🟢 Zaakceptowano podanie tekstem/przyciskiem. Kanał zostanie usunięty za 5 sekund.")
    await asyncio.sleep(5)
    await channel.delete()

async def przegraj_rekrutacje(guild, channel, applicant_id):
    applicant = guild.get_member(applicant_id)
    config = load_config()
    
    if applicant:
        try: await applicant.send(f"❌ Twoje podanie na event **{config['event_name']}** zostało odrzucone.")
        except: pass
        
    await channel.send(f"🔴 Odrzucono podanie tekstem/przyciskiem. Kanał zostanie usunięty za 5 sekund.")
    await asyncio.sleep(5)
    await channel.delete()

# --- FORMULARZ ---
class RecruitmentModal(ui.Modal):
    def __init__(self, title_name):
        super().__init__(title=f"Rekrutacja: {title_name}"[:45])

    q1 = ui.TextInput(label='1. Ile masz lat? / Czy zagrasz cały event? / Czy masz mc premium?', placeholder='Wiek, Tak, Tak', style=discord.TextStyle.short)
    q2 = ui.TextInput(label='2. Nick MC / Zakaz cheatów?', placeholder='Nick, zgadzam się', style=discord.TextStyle.short)
    q3 = ui.TextInput(label='3. Co to RP? + Scenka z Wilem?', placeholder='Opisz tutaj...', style=discord.TextStyle.paragraph)
    q4 = ui.TextInput(label='4. Doświadczenie u kogo?', placeholder='Tak (u kogo) / Nie', style=discord.TextStyle.short)
    q5 = ui.TextInput(label='5. Link do filmu (Mikro+POV)', placeholder='Link do filmu', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id in load_applicants():
            return await interaction.response.send_message("❌ Już wysłałeś podanie!", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        save_applicant(interaction.user.id)
        
        category = interaction.guild.get_channel(CATEGORY_ID)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await interaction.guild.create_text_channel(
            f"podanie-{interaction.user.name}", 
            category=category, 
            overwrites=overwrites,
            topic=str(interaction.user.id) # Zapisujemy tu ID, żeby on_message wiedział do kogo należy kanał
        )
        
        view = AdminDecisionView(applicant_id=interaction.user.id)

        
        ans = discord.Embed(title=f"📝 Podanie - {interaction.user.name}", color=discord.Color.gold())
        ans.add_field(name="Pytanie 1", value=self.q1.value, inline=False)
        ans.add_field(name="Pytanie 2", value=self.q2.value, inline=False)
        ans.add_field(name="Pytanie 3", value=self.q3.value, inline=False)
        ans.add_field(name="Pytanie 4", value=self.q4.value, inline=False)
        ans.add_field(name="Pytanie 5", value=self.q5.value, inline=False)
        
        await channel.send(embed=ans)
        await interaction.followup.send(f"✅ Wysłano! Sprawdź kanał: {channel.mention}", ephemeral=True)

# --- WIDOK PRZYCISKU STARTOWEGO ---
class StartRecruitmentView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Złóż podanie", style=discord.ButtonStyle.primary, custom_id="persistent_start_rec")
    async def start_rec_callback(self, interaction: discord.Interaction, button: ui.Button):
        cfg = load_config()
        await interaction.response.send_modal(RecruitmentModal(cfg["event_name"]))

# --- KOG ---
class Rekrutacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(StartRecruitmentView())
        self.bot.add_view(AdminDecisionView())

    @commands.Cog.listener()
    async def on_message(self, message):
        # Ignorujemy boty
        if message.author.bot:
            return

        # Sprawdzamy czy to kanał podania (szukamy po nazwie i kategorii)
        if message.channel.category and message.channel.category.id == CATEGORY_ID and message.channel.name.startswith("podanie-"):
            # Sprawdzenie roli admina u piszącego
            if ADMIN_ROLE_ID not in [role.id for role in message.author.roles]:
                return

            text = message.content.strip().upper()
            
            # Pobieramy ID gracza z tematu kanału (topic)
            if not message.channel.topic:
                return
            try:
                applicant_id = int(message.channel.topic)
            except ValueError:
                return

            if text == "TAK":
                await wygraj_rekrutacje(message.guild, message.channel, applicant_id)
            elif text == "NIE":
                await przegraj_rekrutacje(message.guild, message.channel, applicant_id)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx, ranga_id: int, *, nazwa: str):
        save_config(nazwa, ranga_id)
        clear_applicants()
        
        embed = discord.Embed(title=f"🎥 REKRUTACJA: {nazwa.upper()}", description="Kliknij przycisk poniżej!", color=discord.Color.gold())
        await ctx.send(embed=embed, view=StartRecruitmentView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
