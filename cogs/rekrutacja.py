import discord
from discord.ext import commands
from discord import ui
import asyncio

# --- KONFIGURACJA ---
CATEGORY_ID = 1511466087278051410
ROLE_ID_TO_GIVE = 123456789012345678  # <--- WPISZ TUTAJ ID RANGI DLA PRZYJĘTYCH

# --- PANEL DECYZJI (Akceptuj/Odrzuć) ---
class AdminDecisionView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Zaakceptuj", style=discord.ButtonStyle.success, custom_id="btn_accept", emoji="✅")
    async def accept(self, interaction: discord.Interaction, button: ui.Button):
        # Pobieramy użytkownika, który złożył podanie (jest w nazwie kanału)
        member_name = interaction.channel.name.replace("podanie-", "")
        member = discord.utils.get(interaction.guild.members, name=member_name)
        
        if member:
            role = interaction.guild.get_role(ROLE_ID_TO_GIVE)
            if role: await member.add_roles(role)
            await interaction.response.send_message(f"✅ Ranga {role.name} nadana!", ephemeral=False)
        else:
            await interaction.response.send_message("❌ Nie znaleziono użytkownika!", ephemeral=True)

    @ui.button(label="Odrzuć", style=discord.ButtonStyle.danger, custom_id="btn_deny", emoji="❌")
    async def deny(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message("🔴 Odrzucono. Kanał usuwa się...", ephemeral=False)
        await asyncio.sleep(3)
        await interaction.channel.delete()

# --- FORMULARZ ---
class RecruitmentModal(ui.Modal, title='📝 Wypełnij podanie'):
    q1 = ui.TextInput(label='1. Wiek / Czy zagrasz cały event?', style=discord.TextStyle.short)
    q2 = ui.TextInput(label='2. Nick MC?', style=discord.TextStyle.short)
    q3 = ui.TextInput(label='3. Co to RP / Scenka?', style=discord.TextStyle.paragraph)
    q4 = ui.TextInput(label='4. Doświadczenie?', style=discord.TextStyle.short)
    q5 = ui.TextInput(label='5. Link do filmu', style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        category = interaction.guild.get_channel(CATEGORY_ID)
        channel = await interaction.guild.create_text_channel(f"podanie-{interaction.user.name}", category=category)
        
        embed = discord.Embed(title=f"📥 Podanie od {interaction.user.name}", color=discord.Color.gold())
        embed.add_field(name="1. Wiek/Event", value=self.q1.value, inline=False)
        embed.add_field(name="2. Nick", value=self.q2.value, inline=False)
        embed.add_field(name="3. RP/Scenka", value=self.q3.value, inline=False)
        embed.add_field(name="4. Doświadczenie", value=self.q4.value, inline=False)
        embed.add_field(name="5. Link", value=self.q5.value, inline=False)
        
        await channel.send(embed=embed, view=AdminDecisionView())
        await interaction.followup.send(f"✅ Podanie wysłane: {channel.mention}", ephemeral=True)

# --- START ---
class StartView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Złóż podanie", style=discord.ButtonStyle.green, custom_id="persistent_view:start_rec", emoji="📩")
    async def button_callback(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RecruitmentModal())

# --- KOG ---
class Rekrutacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(StartView())
        self.bot.add_view(AdminDecisionView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx, *, nazwa: str):
        async for message in ctx.channel.history(limit=50):
            if message.author == self.bot.user: await message.delete()
        embed = discord.Embed(title=f"🎥 REKRUTACJA: {nazwa.upper()}", description="Kliknij przycisk poniżej.", color=discord.Color.blue())
        await ctx.send(embed=embed, view=StartView())

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
