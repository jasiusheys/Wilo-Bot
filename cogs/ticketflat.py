import discord
from discord.ext import commands, tasks
from discord import ui
import asyncio
from datetime import datetime, timezone, timedelta

# --- KONFIGURACJA ---
ADMIN_ROLE_ID = 1503899965234352309
MOD_ROLE_ID = 1503899874758754334  # Ogólne + Flat
FLAT_SMP_ROLE_ID = 1471242368312279317
YT_ROLE_ID = 1168276108559523840
CATEGORY_ID = 1471143729346904065
GUILD_ID = 1083799097766596689

class AdminTicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        # Sprawdza czy użytkownik ma rolę Admina LUB Ogólne+Flat
        allowed_roles = [ADMIN_ROLE_ID, MOD_ROLE_ID]
        if not any(role.id in allowed_roles for role in interaction.user.roles):
            await interaction.response.send_message("❌ Nie masz uprawnień do zarządzania tym ticketem!", ephemeral=True)
            return False
        return True

    @ui.button(label="Nadaj FLATA", style=discord.ButtonStyle.green, custom_id="btn_flat")
    async def add_flat(self, interaction: discord.Interaction, button: ui.Button):
        # Tylko admin może nadawać rangi (zgodnie z życzeniem)
        if ADMIN_ROLE_ID not in [role.id for role in interaction.user.roles]:
            await interaction.response.send_message("❌ Tylko administrator może nadawać rangi!", ephemeral=True)
            return
        
        role = interaction.guild.get_role(FLAT_SMP_ROLE_ID)
        user_id = int(interaction.channel.topic.split(": ")[1])
        member = interaction.guild.get_member(user_id)
        if member:
            await member.add_roles(role)
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
            
        role_flat = interaction.guild.get_role(FLAT_SMP_ROLE_ID)
        role_yt = interaction.guild.get_role(YT_ROLE_ID)
        user_id = int(interaction.channel.topic.split(": ")[1])
        member = interaction.guild.get_member(user_id)
        if member:
            await member.add_roles(role_flat, role_yt)
            await interaction.response.send_message(f"✅ Nadano obie role i zamykam ticket...")
            try: await member.send("✅ Twoje rangi zostały nadane! Sprawdź kanały na Discordzie Wilo-Eventy i baw się dobrze!")
            except: pass
            await asyncio.sleep(3)
            await interaction.channel.delete()

    @ui.button(label="Zamknij", style=discord.ButtonStyle.danger, custom_id="btn_close")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        user_id = int(interaction.channel.topic.split(": ")[1])
        member = interaction.guild.get_member(user_id)
        if member:
            try: await member.send("❌ Twoje zgłoszenie zostało zamknięte. Pamiętaj: aby odebrać rangę musisz posiadać wspierającego na kanale YT Wila lub dać boosta na Discordzie Wilo-Eventy.")
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
        category = guild.get_channel(CATEGORY_ID)
        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            topic=f"User ID: {interaction.user.id}",
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.get_role(MOD_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True),
                guild.get_role(ADMIN_ROLE_ID): discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )
        await interaction.response.send_message(f"✅ Utworzono: {channel.mention}", ephemeral=True)
        await channel.send(f"{interaction.user.mention} Siemka! Wyślij pełny zrzut ekranu, na którym widać że wspierasz Wila. Gdy sprawdzimy dowód, nadamy rangę.", view=AdminTicketView())

class TicketFlat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_inactive_tickets.start()

    def cog_unload(self):
        self.check_inactive_tickets.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketView())
        self.bot.add_view(AdminTicketView())

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.premium_since is None and after.premium_since is not None:
            role = after.guild.get_role(FLAT_SMP_ROLE_ID)
            if role:
                try:
                    await after.add_roles(role)
                    await after.send("✨ Dziękuję za boosta! Otrzymałeś rangę FLAT SMP. Baw się dobrze!")
                except: pass

    @tasks.loop(minutes=10)
    async def check_inactive_tickets(self):
        guild = self.bot.get_guild(GUILD_ID)
        if not guild: return
        category = guild.get_channel(CATEGORY_ID)
        if not category: return
        for channel in category.text_channels:
            if channel.name.startswith("ticket-"):
                messages = [m async for m in channel.history(limit=50, oldest_first=True)]
                try:
                    user_id = int(channel.topic.split(": ")[1])
                    user_has_responded = any(msg.author.id == user_id for msg in messages)
                    if not user_has_responded and datetime.now(timezone.utc) - channel.created_at > timedelta(hours=5):
                        member = guild.get_member(user_id)
                        if member:
                            await member.timeout(timedelta(hours=24), reason="Brak dowodu wsparcia w tickecie po 5h")
                            await member.send("Twój ticket został zamknięty z powodu braku odpowiedzi. Otrzymujesz 24 godziny przerwy na serwerze.")
                        await channel.delete()
                except: continue

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def panel_flat(self, ctx):
        embed = discord.Embed(title="🌌 FLAT SMP - Odbiór wejściówek", description="Kliknij przycisk poniżej!", color=discord.Color.purple())
        await ctx.send(embed=embed, view=TicketView())

async def setup(bot):
    await bot.add_cog(TicketFlat(bot))
