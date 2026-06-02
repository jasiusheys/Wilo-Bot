import discord
from discord.ext import commands
from discord import ui
import json
import os

# --- KONFIGURACJA ---
CATEGORY_ID = 1511466087278051410
CONFIG_FILE = "config_rekrutacja.json"

def load_config():
    if not os.path.exists(CONFIG_FILE): return {"event_name": "Rekrutacja"}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)

# --- FORMULARZ (Wypełniany w tickecie) ---
class ShortRecruitmentModal(ui.Modal, title='📝 Wypełnij swoje zgłoszenie'):
    q1 = ui.TextInput(label='Pytanie 1', placeholder='Czy cały event / wiek / premium?', style=discord.TextStyle.short)
    q2 = ui.TextInput(label='Pytanie 2', placeholder='Twój nick MC i zgoda na zasady?', style=discord.TextStyle.short)
    q3 = ui.TextInput(label='Pytanie 3', placeholder='Co to RP i scenka z Wilem?', style=discord.TextStyle.paragraph)
    q4 = ui.TextInput(label='Pytanie 4', placeholder='Doświadczenie na innych eventach?', style=discord.TextStyle.short)
    q5 = ui.TextInput(label='Pytanie 5', placeholder='Link do filmu (mikrofon + POV)', style=discord.TextStyle.paragraph)

    async def on_submit(self, interaction: discord.Interaction):
        # Wysyłamy embed z odpowiedziami do kanału
        embed = discord.Embed(title=f"✅ Zgłoszenie użytkownika: {interaction.user.name}", color=discord.Color.green())
        fields = ["1. Event/Wiek/Premium", "2. Nick/Zasady", "3. RP/Scenka", "4. Doświadczenie", "5. Dowody"]
        ans = [self.q1.value, self.q2.value, self.q3.value, self.q4.value, self.q5.value]
        for i in range(5): embed.add_field(name=fields[i], value=ans[i], inline=False)
        
        await interaction.channel.send(embed=embed)
        await interaction.response.send_message("✅ Odpowiedzi zostały wysłane do administracji!", ephemeral=True)

# --- WIDOK W KANALE (PRZYCISK FORMULARZA) ---
class ChannelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Wypełnij formularz", style=discord.ButtonStyle.green, custom_id="fill_form", emoji="✍️")
    async def fill(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(ShortRecruitmentModal())

# --- GŁÓWNY PRZYCISK (START) ---
class StartView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    @ui.button(label="Złóż podanie", style=discord.ButtonStyle.blurple, custom_id="start_rec", emoji="📩")
    async def button_callback(self, interaction: discord.Interaction, button: ui.Button):
        category = interaction.guild.get_channel(CATEGORY_ID)
        channel = await interaction.guild.create_text_channel(f"podanie-{interaction.user.name}", category=category)
        
        embed = discord.Embed(
            title="📥 Witaj w swoim podaniu!",
            description=(
                "**Odpowiedz na poniższe pytania:**\n\n"
                "1. Czy możesz zagrać cały event? Ile masz lat? Masz mc premium?\n"
                "2. Jaki masz nick w mc? Rozumiesz że na nagrywce nie można używać cheatów?\n"
                "3. Wyjaśnij czym jest rp/kontent. Co byś zrobił jakbyś spotkał Wila na mapie?\n"
                "4. Czy grałeś już u kogoś na podobnych eventach, jak tak to u kogo?\n"
                "5. Wyślij tutaj link do filmu w którym słychać twój mikrofon oraz widać fov z gry.\n\n"
                "Kliknij przycisk poniżej, aby zacząć wypełnianie."
            ),
            color=discord.Color.gold()
        )
        await channel.send(embed=embed, view=ChannelView())
        await interaction.response.send_message(f"✅ Utworzono Twój ticket: {channel.mention}", ephemeral=True)

# --- KOG ---
class Rekrutacja(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(StartView())
        self.bot.add_view(ChannelView())
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def nowy_event(self, ctx, *, nazwa: str):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f: json.dump({"event_name": nazwa}, f)
        embed = discord.Embed(title=f"🎥 REKRUTACJA: {nazwa}", description="Kliknij przycisk, aby złożyć podanie!", color=discord.Color.blue())
        await ctx.send(embed=embed, view=StartView())
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
