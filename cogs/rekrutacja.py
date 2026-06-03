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

# --- PANEL DECYZJI ---
class AdminDecisionView(ui.View):
    def __init__(self, applicant_id: int = None, event_name: str = ""):
        super().__init__(timeout=None)
        if applicant_id and event_name:
            self.children[0].custom_id = f"adm_accept:{applicant_id}:{event_name}"
            self.children[1].custom_id = f"adm_deny:{applicant_id}:{event_name}"

    @ui.button(label="Zaakceptuj", style=discord.ButtonStyle.success, emoji="✅", custom_id="adm_accept:init:init")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        if ADMIN_ROLE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
        await interaction.response.defer()
        parts = button.custom_id.split(":")
        await wygraj_rekrutacje(interaction.guild, interaction.channel, int(parts[1]), parts[2])

    @ui.button(label="Odrzuć", style=discord.ButtonStyle.danger, emoji="❌", custom_id="adm_deny:init:init")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        if ADMIN_ROLE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Brak uprawnień!", ephemeral=True)
        await interaction.response.defer()
        parts = button.custom_id.split(":")
        await przegraj_rekrutacje(interaction.guild, interaction.channel, int(parts[1]), parts[2])

# --- FUNKCJE POMOCNICZE ---
async def wygraj_rekrutacje(guild, channel, applicant_id, event_name):
    applicant = guild.get_member(applicant_id)
    config = load_config()
    role_id = config.get(event_name.lower())
    
    if role_id and applicant:
        role = guild.get_role(int(role_id))
        if role:
            try: await applicant.add_roles(role)
            except: pass
    if applicant:
        try: await applicant.send(f"✅ Hej twoje podanie na event **{event_name.upper()}** zostało zaakceptowane i otrzymałeś rangę na serwerze Wilo-Eventy!")
        except: pass
    await channel.send("🟢 Zaakceptowano. Kanał zostanie usunięty za 5 sekund.")
    await asyncio.sleep(5)
    await channel.delete()

async def przegraj_rekrutacje(guild, channel, applicant_id, event_name):
    applicant = guild.get_member(applicant_id)
    if applicant:
        try: await applicant.send(f"❌ Hej niestety twoje podanie na event **{event_name.upper()}** zostało odrzucone powodzenia na przyszłych eventach!")
        except: pass
    await channel.send("🔴 Odrzucono. Kanał zostanie usunięty za 5 sekund.")
    await asyncio.sleep(5)
    await channel.delete()

# --- FORMULARZ ---
class RecruitmentModal(ui.Modal):
    def __init__(self, event_name: str):
        super().__init__(title="Formularz Rekrutacyjny")
        self.event_name = event_name

    q1 = ui.TextInput(label='1. Wiek/Czas?/Czy masz mc premium?', placeholder='Ile masz lat? / Czy zagrasz cały event? / Czy masz mc premium?', style=discord.TextStyle.paragraph, required=True)
    q2 = ui.TextInput(label='2. Twój nick z mc / Zasady', placeholder='Nick z MC / Rozumiesz, że na nagrywce jest zakaz cheatów oraz zabronionych modów/txt?', style=discord.TextStyle.paragraph, required=True)
    q3 = ui.TextInput(label='3. Czym jest RP / Reakcja na Wila', placeholder='Wyjaśnij czym jest RP? / Napisz co byś zrobił gdybyś spotkał Wila na mapie', style=discord.TextStyle.paragraph, required=True)
    q4 = ui.TextInput(label='4. Doświadczenie na eventach', placeholder='Czy grałeś już na takich eventach? u kogo?', style=discord.TextStyle.paragraph, required=True)
    q5 = ui.TextInput(label='5. Link do filmu', placeholder='Wyślij link do filmu, który przedstawia twój Mikrofon+POV z gry', style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        applicants = load_applicants()
        if [interaction.user.id, self.event_name.lower()] in applicants:
            return await interaction.response.send_message(f"❌ Już wysłałeś podanie na event **{self.event_name}**!", ephemeral=True)
        
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        selected_category = None
        for cat_id in CATEGORY_IDS:
            cat = interaction.guild.get_channel(cat_id)
            if cat and len(cat.channels) < 50:
                selected_category = cat
                break
        
        if not selected_category:
            return await interaction.followup.send("❌ Wszystkie poczekalnie rekrutacyjne są obecnie pełne! Spróbuj wysłać podanie za chwilę, gdy administracja sprawdzi obecne zgłoszenia.", ephemeral=True)

        save_applicant(interaction.user.id, self.event_name)
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await interaction.guild.create_text_channel(
            f"podanie-{interaction.user.name}", 
            category=selected_category, 
            overwrites=overwrites, 
            topic=f"{interaction.user.id}:{self.event_name}"
        )
        
        ans = discord.Embed(title=f"📝 Podanie: {self.event_name.upper()} - {interaction.user.name}", color=discord.Color.gold())
        ans.add_field(name="Pytanie 1", value=self.q1.value, inline=False)
        ans.add_field(name="Pytanie 2", value=self.q2.value, inline=False)
        ans.add_field(name="Pytanie 3", value=self.q3.value, inline=False)
        ans.add_field(name="Pytanie 4", value=self.q4.value, inline=False)
        ans.add_field(name="Pytanie 5", value=self.q5.value, inline=False)
        
        view = AdminDecisionView(applicant_id=interaction.user.id, event_name=self.event_name)
        await channel.send(f"🛡️ **Panel Decyzji dla:** {interaction.user.mention}\nMożesz kliknąć przycisk lub pisać **TAK** / **NIE**\nEvent: **{self.event_name}**", view=view)
        await channel.send(embed=ans)
        await interaction.followup.send(f"✅ Wysłano! Sprawdź kanał: {channel.mention}", ephemeral=True)

# --- PRZYCISK STARTOWY ---
class StartRecruitmentView(ui.View):
    def __init__(self, event_name: str = ""):
        super().__init__(timeout=None)
        if event_name:
            self.children[0].custom_id = f"persistent_start_rec:{event_name}"

    @ui.button(label="Złóż podanie", style=discord.ButtonStyle.primary, custom_id="persistent_start_rec:default")
    async def start_rec_callback(self, interaction: discord.Interaction, button: ui.Button):
        event_name = button.custom_id.split(":")[1]
        await interaction.response.send_modal(RecruitmentModal(event_name=event_name))

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
        if message.author.bot: return
        if message.channel.category and message.channel.category.id in CATEGORY_IDS and message.channel.name.startswith("podanie-"):
            if ADMIN_ROLE_ID not in [role.id for role in message.author.roles]: return
            
            text = message.content.strip().upper()
            if not message.channel.topic: return
            
            try:
                parts = message.channel.topic.split(":")
                applicant_id = int(parts[0])
                event_name = parts[1]
            except: return

            if text == "TAK": await wygraj_rekrutacje(message.guild, message.channel, applicant_id, event_name)
            elif text == "NIE": await przegraj_rekrutacje(message.guild, message.channel, applicant_id, event_name)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx, ranga_id: int, *, nazwa: str):
        save_config(nazwa, ranga_id)
        clear_applicants_for_event(nazwa)
        
        # Przywrócona kamera z oryginalnego kodu
        embed = discord.Embed(
            title=f"🎥 REKRUTACJA: {nazwa.upper()}", 
            description="Kliknij przycisk poniżej!", 
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed, view=StartRecruitmentView(event_name=nazwa))
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
