import discord
from discord.ext import commands
from discord import ui

# --- FORMULARZ ---
class RecruitmentModal(ui.Modal, title='Formularz Rekrutacji'):
    def __init__(self):
        super().__init__()
    
    q1 = ui.TextInput(label='1. Wiek / Cały event / Premium?', placeholder='Wpisz tutaj...', style=discord.TextStyle.short)
    q2 = ui.TextInput(label='2. Twój nick MC?', placeholder='Twój nick...', style=discord.TextStyle.short)
    q3 = ui.TextInput(label='3. Co to RP / Scenka z Wilem?', placeholder='Opisz tutaj...', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Podanie wysłane!", ephemeral=True)

# --- WIDOK Z PRZYCISKIEM ---
class StartView(ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Bardzo ważne dla przycisków!

    @ui.button(label="Złóż podanie", style=discord.ButtonStyle.primary, custom_id="persistent_view:start_rec")
    async def button_callback(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(RecruitmentModal())

# --- KOG ---
class Rekrutacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Rejestracja widoku, żeby bot go pamiętał po restarcie
        self.bot.add_view(StartView())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx):
        embed = discord.Embed(title="🎥 REKRUTACJA", description="Kliknij przycisk poniżej, aby złożyć podanie.", color=discord.Color.green())
        await ctx.send(embed=embed, view=StartView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
