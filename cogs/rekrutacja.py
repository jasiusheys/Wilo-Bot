import discord
from discord.ext import commands
from discord import ui

# --- FORMULARZ ---
class RecruitmentModal(ui.Modal, title='📝 Wypełnij podanie'):
    q1 = ui.TextInput(label='1. Wiek / Czy zagrasz cały event?', placeholder='Wiek / Tak', style=discord.TextStyle.short)
    q2 = ui.TextInput(label='2. Twój nick MC?', placeholder='Twój nick', style=discord.TextStyle.short)
    q3 = ui.TextInput(label='3. Co to RP / Scenka z Wilem?', placeholder='Opisz tutaj...', style=discord.TextStyle.paragraph)
    q4 = ui.TextInput(label='4. Doświadczenie?', placeholder='Tak/Nie', style=discord.TextStyle.short)
    q5 = ui.TextInput(label='5. Link do filmu', placeholder='Wklej link', style=discord.TextStyle.short)

    async def on_submit(self, interaction: discord.Interaction):
        # 1. Defer, żeby Discord nie wywalał błędów
        await interaction.response.defer(ephemeral=True, thinking=True)
        
        # 2. Tworzymy kanał (ticket)
        guild = interaction.guild
        channel = await guild.create_text_channel(f"podanie-{interaction.user.name}")
        
        # 3. Wysyłamy treść do nowego kanału
        embed = discord.Embed(title=f"📥 Podanie od {interaction.user.name}", color=discord.Color.gold())
        embed.add_field(name="1. Wiek/Event", value=self.q1.value, inline=False)
        embed.add_field(name="2. Nick", value=self.q2.value, inline=False)
        embed.add_field(name="3. RP/Scenka", value=self.q3.value, inline=False)
        embed.add_field(name="4. Doświadczenie", value=self.q4.value, inline=False)
        embed.add_field(name="5. Link", value=self.q5.value, inline=False)
        
        await channel.send(embed=embed)
        await channel.send(f"✅ Ticket utworzony dla {interaction.user.mention}")
        
        # 4. Potwierdzenie dla usera
        await interaction.followup.send(f"✅ Twoje podanie zostało wysłane do kanału: {channel.mention}", ephemeral=True)

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
        # Usuń stare śmieci
        async for message in ctx.channel.history(limit=50):
            if message.author == self.bot.user:
                await message.delete()

        embed = discord.Embed(title=f"🎥 REKRUTACJA: {nazwa.upper()}", description="Kliknij przycisk poniżej, aby złożyć podanie.", color=discord.Color.blue())
        await ctx.send(embed=embed, view=StartView())

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
