import discord
from discord.ext import commands
from discord import ui
import json
import os
import asyncio
from datetime import datetime

# --- KONFIGURACJA ---
ADMIN_ROLE_ID = 1511396320173359144
MOD_ACCESS_ROLE_ID = 1511727936515080252
CONFIG_FILE = "config_rekrutacja.json"
DATA_FILE = "podania.json"
ARCHIVE_FILE = "archiwum_rekrutacji.json"
BLACKLIST_FILE = "blacklist.json"

CATEGORY_IDS = [
    1511466087278051410,
    1511687027727401010,
    1511687075601317948
]

# --- OBSŁUGA PLIKÓW ---
def load_config():
    if not os.path.exists(CONFIG_FILE): return {}
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
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            if data and isinstance(data[0], list):
                converted = []
                for x in data:
                    if len(x) >= 2:
                        converted.append({"user_id": x[0], "event": x[1].lower(), "status": "OCZEKUJE"})
                return converted
            return data
        except: return []

def save_all_applicants(applicants):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(applicants, f, ensure_ascii=False, indent=4)

def save_to_archive(report):
    archive = []
    if os.path.exists(ARCHIVE_FILE):
        with open(ARCHIVE_FILE, "r", encoding="utf-8") as f:
            try: archive = json.load(f)
            except: archive = []
    archive.append(report)
    with open(ARCHIVE_FILE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=4)

def load_blacklist():
    if not os.path.exists(BLACKLIST_FILE): return {}
    with open(BLACKLIST_FILE, "r", encoding="utf-8") as f:
        try: return json.load(f)
        except: return {}

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, "w", encoding="utf-8") as f:
        json.dump(blacklist, f, ensure_ascii=False, indent=4)

def save_applicant(user_id, event_name):
    applicants = load_applicants()
    exists = any(x['user_id'] == user_id and x['event'] == event_name.lower() for x in applicants)
    if not exists:
        applicants.append({"user_id": user_id, "event": event_name.lower(), "status": "OCZEKUJE"})
        save_all_applicants(applicants)

def update_applicant_status(user_id, event_name, status):
    applicants = load_applicants()
    for x in applicants:
        if x['user_id'] == user_id and x['event'] == event_name.lower():
            x['status'] = status
            break
    save_all_applicants(applicants)

def clear_applicants_for_event(event_name):
    applicants = load_applicants()
    applicants = [x for x in applicants if x['event'] != event_name.lower()]
    save_all_applicants(applicants)

def has_mod_perms(user):
    if not hasattr(user, 'roles'): return False
    user_role_ids = [role.id for role in user.roles]
    return (ADMIN_ROLE_ID in user_role_ids) or (MOD_ACCESS_ROLE_ID in user_role_ids) or user.guild_permissions.administrator

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
            return await interaction.response.send_message("❌ Nie masz rangi sprawdzającej!", ephemeral=True)
        await interaction.response.defer()
        parts = button.custom_id.split(":")
        update_applicant_status(int(parts[1]), parts[2], "TAK")
        await wygraj_rekrutacje(interaction.guild, interaction.channel, int(parts[1]), parts[2])

    @ui.button(label="Odrzuć", style=discord.ButtonStyle.danger, emoji="❌", custom_id="adm_deny:init:init")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        if not has_mod_perms(interaction.user):
            return await interaction.response.send_message("❌ Nie masz rangi sprawdzającej!", ephemeral=True)
        await interaction.response.defer()
        parts = button.custom_id.split(":")
        update_applicant_status(int(parts[1]), parts[2], "NIE")
        await przegraj_rekrutacje(interaction.guild, interaction.channel, int(parts[1]), parts[2])

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
        try: await applicant.send(f"✅ Hej twoje podanie na event **{event_name.upper()}** zostało zaakceptowane!")
        except: pass
    await channel.send("🟢 Zaakceptowano. Usuwanie kanału...")
    await asyncio.sleep(5)
    try: await channel.delete()
    except: pass

async def przegraj_rekrutacje(guild, channel, applicant_id, event_name):
    applicant = guild.get_member(applicant_id)
    if applicant:
        try: await applicant.send(f"❌ Hej niestety twoje podanie na event **{event_name.upper()}** zostało odrzucone!")
        except: pass
    await channel.send("🔴 Odrzucono. Usuwanie kanału...")
    await asyncio.sleep(5)
    try: await channel.delete()
    except: pass

class RecruitmentModal(ui.Modal):
    def __init__(self, event_name: str):
        super().__init__(title="Formularz Rekrutacyjny")
        self.event_name = event_name

    q1 = ui.TextInput(label='1. Wiek/Czas?/Czy masz mc premium?', placeholder='Ile masz lat? / Czy zagrasz cały event?', style=discord.TextStyle.paragraph, required=True)
    q2 = ui.TextInput(label='2. Twój nick z mc / Zasady', placeholder='Nick z MC / Czy akceptujesz brak cheatów?', style=discord.TextStyle.paragraph, required=True)
    q3 = ui.TextInput(label='3. Czym jest RP / Reakcja na Wila', placeholder='Wyjaśnij czym jes RP? / Co byś zrobił?', style=discord.TextStyle.paragraph, required=True)
    q4 = ui.TextInput(label='4. Doświadczenie na eventach', placeholder='Czy grałeś już na takich eventach?', style=discord.TextStyle.paragraph, required=True)
    q5 = ui.TextInput(label='5. Link do filmu', placeholder='Link do filmu z mikrofonem i pov', style=discord.TextStyle.paragraph, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        applicants = load_applicants()
        if any(x['user_id'] == interaction.user.id and x['event'] == self.event_name.lower() for x in applicants):
            return await interaction.response.send_message("❌ Już wysłałeś podanie!", ephemeral=True)
        await interaction.response.defer(ephemeral=True, thinking=True)
        selected_category = None
        for cat_id in CATEGORY_IDS:
            cat = interaction.guild.get_channel(cat_id)
            if cat and len(cat.channels) < 50:
                selected_category = cat; break
        if not selected_category:
            return await interaction.followup.send("❌ Brak miejsca!", ephemeral=True)

        save_applicant(interaction.user.id, self.event_name)
        mod_role = interaction.guild.get_role(MOD_ACCESS_ROLE_ID)
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        if mod_role: overwrites[mod_role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        channel = await interaction.guild.create_text_channel(f"podanie-{interaction.user.name}", category=selected_category, overwrites=overwrites, topic=f"{interaction.user.id}:{self.event_name}")
        ans = discord.Embed(title=f"📝 Podanie: {self.event_name.upper()} - {interaction.user.name}", color=discord.Color.gold())
        ans.add_field(name="Odpowiedzi", value=f"1. {self.q1.value}\n2. {self.q2.value}\n3. {self.q3.value}\n4. {self.q4.value}\n5. {self.q5.value}")
        await channel.send(f"🛡️ **Panel Zarządzania**", view=AdminDecisionView(applicant_id=interaction.user.id, event_name=self.event_name))
        await channel.send(embed=ans)
        await interaction.followup.send(f"✅ Wysłano! {channel.mention}", ephemeral=True)

class StartRecruitmentView(ui.View):
    def __init__(self, event_name: str = ""):
        super().__init__(timeout=None)
        if event_name: self.children[0].custom_id = f"persistent_start_rec:{event_name}"

    @ui.button(label="Złóż podanie", style=discord.ButtonStyle.primary, custom_id="persistent_start_rec:default")
    async def start_rec_callback(self, interaction: discord.Interaction, button: ui.Button):
        blacklist = load_blacklist()
        if str(interaction.user.id) in blacklist:
            return await interaction.response.send_message(f"❌ Zostałeś zablokowany.\n**Powód:** {blacklist[str(interaction.user.id)]}", ephemeral=True)
        event_name = button.custom_id.split(":")[1]
        await interaction.response.send_modal(RecruitmentModal(event_name=event_name))

class Rekrutacja(commands.Cog):
    def __init__(self, bot): self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(StartRecruitmentView())
        self.bot.add_view(AdminDecisionView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def ban_rekrutacja(self, ctx, members: commands.Greedy[discord.Member], *, powod: str = "Brak podanego powodu"):
        if not members: return await ctx.send("❌ Musisz oznaczyć przynajmniej jedną osobę!")
        try:
            blacklist = load_blacklist()
            applicants = load_applicants()
            zbanowani = []
            for member in members:
                blacklist[str(member.id)] = powod
                applicants = [x for x in applicants if x['user_id'] != member.id]
                for channel in ctx.guild.channels:
                    if isinstance(channel, discord.TextChannel) and channel.topic and str(member.id) in channel.topic:
                        try: await channel.delete()
                        except: pass
                zbanowani.append(member.mention)
            save_blacklist(blacklist)
            save_all_applicants(applicants)
            embed = discord.Embed(title="✅ Zablokowano użytkowników", color=discord.Color.red())
            embed.add_field(name="Osoby", value=", ".join(zbanowani), inline=False)
            embed.add_field(name="Powód", value=powod, inline=False)
            await ctx.send(embed=embed)
        except Exception as e: await ctx.send(f"⚠️ Wystąpił błąd: {e}")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unban_rekrutacja(self, ctx, members: commands.Greedy[discord.Member]):
        if not members: return await ctx.send("❌ Musisz oznaczyć przynajmniej jedną osobę!")
        blacklist = load_blacklist()
        odbanowani = []
        for member in members:
            if str(member.id) in blacklist:
                del blacklist[str(member.id)]
                odbanowani.append(member.mention)
        save_blacklist(blacklist)
        if odbanowani: await ctx.send(f"✅ Odblokowano: {', '.join(odbanowani)}.")
        else: await ctx.send("ℹ️ Żaden z oznaczonych użytkowników nie był na liście.")

    @commands.command()
    async def blacklista(self, ctx):
        blacklist = load_blacklist()
        if not blacklist: return await ctx.send("ℹ️ Blacklista jest pusta.")
        embed = discord.Embed(title="🚫 Blacklista Rekrutacji", color=discord.Color.dark_red())
        text = ""
        for user_id, powod in blacklist.items():
            user = self.bot.get_user(int(user_id))
            name = user.name if user else f"ID: {user_id}"
            text += f"• **{name}**: {powod}\n"
        embed.description = text
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx, ranga_id: int, *, nazwa: str):
        try: await ctx.message.delete()
        except: pass
        save_config(nazwa, ranga_id)
        clear_applicants_for_event(nazwa)
        embed = discord.Embed(title=f"🎥 REKRUTACJA: {nazwa.upper()}", color=discord.Color.gold())
        await ctx.send(embed=embed, view=StartRecruitmentView(event_name=nazwa))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def koniec_eventu(self, ctx, *, nazwa: str):
        try: await ctx.message.delete()
        except: pass
        applicants = load_applicants()
        event_data = [x for x in applicants if x['event'] == nazwa.lower()]
        if not event_data: return await ctx.send(f"❌ Brak podań dla: **{nazwa.upper()}**", delete_after=10)
        total = len(event_data)
        acc = len([x for x in event_data if x['status'] == "TAK"])
        den = len([x for x in event_data if x['status'] == "NIE"])
        rate = round((acc / total) * 100) if total > 0 else 0
        report = {"data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "event": nazwa.upper(), "suma": total, "zaakceptowani": acc, "odrzuceni": den, "skutecznosc": f"{rate}%"}
        save_to_archive(report)
        clear_applicants_for_event(nazwa)
        embed = discord.Embed(title=f"🏁 KONIEC REKRUTACJI: {nazwa.upper()}", color=discord.Color.red() if rate < 50 else discord.Color.green())
        embed.add_field(name="📋 Statystyki końcowe", value=f"👥 Suma: `{total}`, ✅: `{acc}`, ❌: `{den}`, 📊: `{rate}%`", inline=False)
        await ctx.send(embed=embed)

async def setup(bot): await bot.add_cog(Rekrutacja(bot))
