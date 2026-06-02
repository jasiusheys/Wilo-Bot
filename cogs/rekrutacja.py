import discord
from discord.ext import commands
from discord import ui

# --- FORMULARZ ---
class RecruitmentModal(ui.Modal, title='📝 Podanie na Event'):
    q1 = ui.TextInput(label='1. Wiek / Czy zagrasz cały event?', placeholder='Np. 16 lat, Tak', style=discord.TextStyle.short)
    q2 = ui.TextInput(label='2. Twój nick MC?', placeholder='Twój nick', style=discord.TextStyle.short)
    q3 = ui.TextInput(label='3. Co to RP / Scenka z Wilem?', placeholder='Opisz tutaj...', style=discord.TextStyle.paragraph)
    q4 = ui.TextInput(label='4. Doświadczenie na eventach?', placeholder='Tak/Nie', style=discord.TextStyle.short)
    q5 = ui.TextInput(label='5. Link do filmu (mikro+fov)', placeholder='Wklej link tutaj', style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("✅ Twoje podanie zostało przyjęte!", ephemeral=True)

# --- PRZYCISK ---
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

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx, *, nazwa: str):
        # 1. Usuwamy wszystkie stare wiadomości na tym kanale, żeby był porządek
        async for message in ctx.channel.history(limit=50):
            if message.author == self.bot.user:
                await message.delete()

        # 2. Tworzymy elegancki Embed
        embed = discord.Embed(
            title=f"🎥 REKRUTACJA: {nazwa.upper()}",
            description="Witaj w procesie rekrutacji! Kliknij przycisk poniżej, aby wypełnić formularz zgłoszeniowy.",
            color=discord.Color.gold()
        )
        embed.set_footer(text="Wilo BOT | System Rekrutacji")
        
        await ctx.send(embed=embed, view=StartView())

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
