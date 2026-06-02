import discord
from discord.ext import commands
from discord import ui
import json
import os
import asyncio

# --- STAŁA KONFIGURACJA ---
ADMIN_ROLE_ID = 1511396320173359144  # Twoje ID rangi administracyjnej

CONFIG_FILE = "config_rekrutacja.json"
DATA_FILE = "podania.json"

# --- SYSTEM ZAPISU DANYCH ---
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"event_name": "Rekrutacja na Event", "role_id": None}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(event_name, role_id):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump({"event_name": event_name, "role_id": role_id}, f, ensure_ascii=False, indent=4)

def load_applicants():
    if not os.path.exists(DATA_FILE): return []
    with open(DATA_FILE, "r") as f: return json.load(f)

def save_applicant(user_id):
    applicants = load_applicants()
    if user_id not in applicants:
        applicants.append(user_id)
        with open(DATA_FILE, "w") as f:
            json.dump(applicants, f)

def clear_applicants():
    with open(DATA_FILE, "w") as f:
        json.dump([], f)

# --- PANEL PRZYCISKÓW W TICKETACH ---
class AdminDecisionView(ui.View):
    def __init__(self, applicant):
        super().__init__(timeout=None)
        self.applicant = applicant

    @ui.button(label="Zaakceptuj", style=discord.ButtonStyle.success, emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        if ADMIN_ROLE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Nie masz uprawnień do akceptacji podań!", ephemeral=True)

        config = load_config()
        if config["role_id"]:
            role = interaction.guild.get_role(int(config["role_id"]))
            if role: await self.applicant.add_roles(role)
        
        try:
            await self.applicant.send(f"✅ Gratulacje! Twoje podanie na event **{config['event_name']}** u Wila zostało **ZAAKCEPTOWANE**.")
        except: pass

        await interaction.response.send_message("🟢 Podanie zaakceptowane. Usuwam kanał za 5 sekund...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

    @ui.button(label="Odrzuć", style=discord.ButtonStyle.danger, emoji="❌")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        if ADMIN_ROLE_ID not in [role.id for role in interaction.user.roles]:
            return await interaction.response.send_message("❌ Nie masz uprawnień do odrzucania podań!", ephemeral=True)

        config = load_config()
        try:
            await self.applicant.send(f"❌ Niestety, Twoje podanie na event **{config['event_name']}** zostało **ODRZUCONE**.")
        except: pass

        await interaction.response.send_message("🔴 Podanie odrzucone. Usuwam kanał za 5 sekund...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

# --- FORMULARZ (MODAL) ---
class RecruitmentModal(ui.Modal):
    def __init__(self, title_name):
        super().__init__(title=f"Rekrutacja: {title_name}"[:45])

 q1 = ui.TextInput(label='1. Czy zagrasz cały event, ile masz lat i premium?', placeholder='Tak, 16 lat, Tak', style=discord.TextStyle.short)
    q2 = ui.TextInput(label='2. Twój nick MC oraz zgoda na zakaz cheatów', placeholder='Nick: ..., Zgadzam się na zakaz cheatów', style=discord.TextStyle.short)
    q3 = ui.TextInput(label='3. Co to RP? + Co zrobisz jak spotkasz Wila?', placeholder='RP to..., Gdy spotkam Wila na mapie to...', style=discord.TextStyle.paragraph)
    q4 = ui.TextInput(label='4. Grałeś już na takich eventach? U kogo?', placeholder='Np. Tak, grałem u X, albo Nie grałem', style=discord.TextStyle.short)
    q5 = ui.TextInput(label='5. Link do filmu (Mikrofon + POV z gry)', placeholder='Wstaw link do YT/Medal/Dysk Google', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        if interaction.user.id in load_applicants():
            return await interaction.response.send_message("❌ Już wysłałeś podanie na ten konkretny event!", ephemeral=True)

        save_applicant(interaction.user.id)
        await interaction.response.send_message("✅ Wysłano! Sprawdź listę kanałów - stworzyłem dla Ciebie ticket.", ephemeral=True)

        config = load_config()
        category = discord.utils.get(interaction.guild.categories, name="REKRUTACJA")
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        channel = await interaction.guild.create_text_channel(
            f"podanie-{interaction.user.name}", 
            category=category, 
            overwrites=overwrites,
            topic=str(interaction.user.id)
        )

        embed_admin = discord.Embed(
            title="🛡️ DECYZJA ADMINISTRACJI", 
            description=f"Kandydat: {interaction.user.mention}\nEvent: **{config['event_name']}**\n\nNapisz **tak** / **nie** lub użyj przycisków.", 
            color=discord.Color.dark_red()
        )
        await channel.send(embed=embed_admin, view=AdminDecisionView(interaction.user))

        ans = discord.Embed(title=f"📝 TREŚĆ PODANIA - {interaction.user.name}", color=discord.Color.gold())
        ans.add_field(name="Q1: Szybkie pytania", value=self.q1.value, inline=False)
        ans.add_field(name="Q2: Dane", value=self.q2.value, inline=False)
        ans.add_field(name="Q3: RP i Scenka", value=self.q3.value, inline=False)
        ans.add_field(name="Q4: Historia", value=self.q4.value, inline=False)
        ans.add_field(name="Q5: Dowody (Linki)", value=self.q5.value, inline=False)
        await channel.send(embed=ans)

# --- COG ---
class Rekrutacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.channel.name.startswith("podanie-"): return
        
        text = message.content.lower().strip()
        if text not in ["tak", "nie"]: return

        try:
            applicant_id = int(message.channel.topic)
            applicant = message.guild.get_member(applicant_id)
        except: return

        if message.author.id == applicant_id: return
        if ADMIN_ROLE_ID not in [role.id for role in message.author.roles]: return
        if not applicant: return

        config = load_config()

        if text == "tak":
            if config["role_id"]:
                role = message.guild.get_role(int(config["role_id"]))
                if role: await applicant.add_roles(role)
            try: await applicant.send(f"✅ Twoje podanie na event **{config['event_name']}** zostało zaakceptowane!")
            except: pass
            await message.channel.send("🟢 Zaakceptowano słownie. Zamykam kanał...")

        elif text == "nie":
            try: await applicant.send(f"❌ Twoje podanie na event **{config['event_name']}** zostało odrzucone.")
            except: pass
            await message.channel.send("🔴 Odrzucono słownie. Zamykam kanał...")

        await asyncio.sleep(5)
        await message.channel.delete()

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx, ranga_id: int, *, nazwa: str):
        save_config(nazwa, ranga_id)
        clear_applicants()
        
        view = ui.View(timeout=None)
        btn = ui.Button(label="Złóż podanie na event", style=discord.ButtonStyle.primary, custom_id="start_rec")
        
        async def callback(interaction):
            cfg = load_config()
            if interaction.user.id in load_applicants():
                return await interaction.response.send_message("❌ Już wysłałeś podanie na ten event!", ephemeral=True)
            await interaction.response.send_modal(RecruitmentModal(cfg["event_name"]))
            
        btn.callback = callback
        view.add_item(btn)
        
        embed = discord.Embed(
            title=f"🎥 NOWA REKRUTACJA: {nazwa.upper()}", 
            description="Kliknij przycisk poniżej, aby wysłać formularz. Powodzenia!", 
            color=discord.Color.gold()
        )
        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
