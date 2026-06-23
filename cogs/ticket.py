import discord
from discord import ui
from discord.ext import commands

# --- KONFIGURACJA ---
# ID Kategorii
CATEGORY_MAP = {
    "Twórca": 1503873245064200234,
    "Ogólne": 1503873389771882606,
    "Nagrywki": 1503873359849590795,
    "Wspieranie": 1503873164315332699,
    "Współpraca": 1503873125434134648
}

# Wiadomości powitalne dla każdej kategorii
WELCOME_MESSAGES = {
    "Twórca": "Siemka {user}! Jeżeli chcesz odebrać range twórca wyślij tutaj link do swojego kanału na youtubie i czekaj na weryfikacje!",
    "Ogólne": "Siemka {user}! Napisz jaki masz problem i czekaj na odpowiedź!",
    "Nagrywki": "Siemka {user}! Napisz jaki masz problem i czekaj na odpowiedź!",
    "Wspieranie": "Siemka {user}! Jeżeli chcesz odebrac rangę wyślij zrzut ekranu w potwierdzeniem że wspierasz kanał Wila. ",
    "Współpraca": "Siemka {user}! Masz jakąś propozycje wspołpracy? Napisz ją tutaj!."
}

class TicketCategorySelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Twórca", description="Wymagania dla twórców", emoji="🎥"),
            discord.SelectOption(label="Ogólne", description="Inne pytania", emoji="⚙️"),
            discord.SelectOption(label="Nagrywki", description="Rekrutacja do nagrywek", emoji="🎙️"),
            discord.SelectOption(label="Wspieranie", description="Problemy i odbiór rangi", emoji="💎"),
            discord.SelectOption(label="Współpraca", description="Propozycje współpracy", emoji="🤝"),
        ]
        super().__init__(placeholder="Select a category", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        category_name = self.values[0]
        category_id = CATEGORY_MAP.get(category_name)
        guild = interaction.guild
        category = guild.get_channel(category_id)
        
        # Nazwa kanału (małe litery wymagane przez Discord)
        channel_name = f"ticket-{category_name.lower()}-{interaction.user.name.lower()}"

        # Sprawdzenie czy użytkownik nie ma już ticketa
        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message(f"❌ Masz już otwarty ticket w tej kategorii: {existing_channel.mention}", ephemeral=True)
            return

        # Tworzenie kanału
        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites={
                guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
        )
        
        # Pobranie odpowiedniej wiadomości i wstawienie wzmianki użytkownika
        welcome_text = WELCOME_MESSAGES.get(category_name, "Witaj {user}! Czekamy na wiadomość.").replace("{user}", interaction.user.mention)
        
        await interaction.response.send_message(f"✅ Utworzono ticket: {channel.mention}", ephemeral=True)
        await channel.send(welcome_text)

class TicketPanel(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(TicketPanel())

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def panel_ticketow(self, ctx):
        embed = discord.Embed(
            title="📥 CENTRUM POMOCY",
            description="Wybierz odpowiednią kategorię z menu poniżej, aby otworzyć nowego ticketa.\n\nPostaramy się pomóc tak szybko, jak to możliwe!\nPingowanie administracji oraz bezpodstawne tickety będą karane!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=TicketPanel())

async def setup(bot):
    await bot.add_cog(TicketSystem(bot))
