import discord
from discord.ext import commands, tasks
from discord import ui
import asyncio
from datetime import datetime, timezone, timedelta

# --- KONFIGURACJA ---
ADMIN_ROLE_ID = 1503899965234352309 # wspieranie rola 
MOD_ROLE_ID = 1503899874758754334  # Ogólne + Flat
FLAT_SMP_ROLE_ID = 1471242368312279317
YT_ROLE_ID = 1168276108559523840
CATEGORY_ID = 1471143729346904065
GUILD_ID = 1083799097766596689
LOG_CHANNEL_ID = 1518760958044930058 # Kanał logów

class AdminTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        allowed_roles = [ADMIN_ROLE_ID, MOD_ROLE_ID]
        if not any(role.id in allowed_roles for role in interaction.user.roles):
            await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania tym ticketem!", ephemeral=True)
            return False
        return True

    @ui.button(label="Nadaj FLATA", style=discord.ButtonStyle.green, custom_id="btn_flat")
    async def add_flat(self, interaction: discord.Interaction, button: ui.Button):
        if ADMIN_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Tylko administrator może nadawać rangi!", ephemeral=True)
            return
        
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        role = interaction.guild.get_role(FLAT_SMP_ROLE_ID)
        user_id = int(interaction.channel.topic.split(": ")[1])
        member = interaction.guild.get_member(user_id)
        
        if member:
            await member.add_roles(role)
            # Logowanie nadania rangi
            if log_channel:
                embed = discord.Embed(title="✅ Ranga nadana: FLAT SMP", color=discord.Color.green())
                embed.add_field(name="Użytkownik", value=f"{member.mention}", inline=True)
                embed.add_field(name="Nadane przez", value=f"{interaction.user.name}", inline=True)
                embed.set_footer(text=f"ID Użytkownika: {user_id}")
                await log_channel.send(embed=embed)
            
            await interaction.response.send_message(f"✅ Nadano {role.name} i zamykam ticket...")
            try: await member.send("✅ Twoja ranga FLAT SMP została nadana! Sprawdź kanały na Discordzie Wilo-Eventy i baw się dobrze!")
            except: pass
            await asyncio.sleep(3)
            await interaction.channel.delete()

    @ui.button(label="Nadaj FLATA + YT", style=discord.ButtonStyle.success, custom_id="btn_both")
    async def add_both(self, interaction: discord.Interaction, button: ui.Button):
        if ADMIN_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Tylko administrator może nadawać rangi!", ephemeral=True)
            return
            
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        role_flat = interaction.guild.get_role(FLAT_SMP_ROLE_ID)
        role_yt = interaction.guild.get_role(YT_ROLE_ID)
        user_id = int(interaction.channel.topic.split(": ")[1])
        member = interaction.guild.get_member(user_id)
        
        if member:
            await member.add_roles(role_flat, role_yt)
            # Logowanie nadania obu rang
            if log_channel:
                embed = discord.Embed(title="✅ Rangi nadane: FLAT SMP + YT", color=discord.Color.gold())
                embed.add_field(name="Użytkownik", value=f"{member.mention}", inline=True)
                embed.add_field(name="Nadane przez", value=f"{interaction.user.name}", inline=True)
                embed.set_footer(text=f"ID Użytkownika: {user_id}")
                await log_channel.send(embed=embed)
                
            await interaction.response.send_message(f"✅ Nadano obie role i zamykam ticket...")
            try: await member.send("✅ Twoje ranga na Flat SMP oraz wspierający została nadana ! Sprawdź kanały na Discordzie Wilo-Eventy i baw się dobrze!")
            except: pass
            await asyncio.sleep(3)
            await interaction.channel.delete()

    @ui.button(label="Zamknij", style=discord.ButtonStyle.danger, custom_id="btn_close")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        user_id = int(interaction.channel.topic.split(": ")[1])
        member = interaction.guild.get_member(user_id)
        
        if log_channel:
            embed = discord.Embed(title="📁 Logi Ticketa", color=discord.Color.blue())
            embed.add_field(name="Użytkownik", value=f"{member.mention if member else 'Nieznany'}", inline=True)
            embed.add_field(name="Zamknięte przez", value=f"{interaction.user.name}", inline=True)
            embed.set_footer(text=f"ID Użytkownika: {user_id}")
            await log_channel.send(embed=embed)

        if member:
            try: await member.send("❌ Twoje zgłoszenie zostało zamknięte. Pamiętaj, że aby odebrać rangę musisz posiadać wspierającego na YouTube u Wila albo boostera na Discordzie.")
            except: pass
        await interaction.response.send_message("🔒 Zamykam za 5s...")
        await asyncio.sleep(5)
        await interaction.channel.delete()

class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="🚀 Chcę odebrać", style=discord.ButtonStyle.primary, custom_id="ticket_flat_button")
    async def create_ticket(self, interaction: discord.Interaction, button: ui.Button):
        guild = interaction.guild
        category
