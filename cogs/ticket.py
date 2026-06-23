import discord
from discord import ui
from discord.ext import commands

# --- KONFIGURACJA ---
# Twoje ID kategorii
CATEGORY_MAP = {
    "Twórca": 1503873245064200234,
    "Ogólne": 1503873389771882606,
    "Nagrywki": 1503873359849590795,
    "Wspieranie": 1503873164315332699,
    "Współpraca": 1503873125434134648
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
        
        # Tworzenie nazwy kanału w formacie małych liter (wymagane przez Discord)
        channel_name = f"ticket-{category_name.lower()}-{interaction.user.name.lower()}"

        # SPRAWDZANIE CZY UŻYTKOWNIK JUŻ MA TEN TICKET
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
        await interaction.response.send_message(f"✅ Utworzono ticket: {channel.mention}", ephemeral=True)
        await channel.send(f"Witaj {interaction.user.mention}! Wybrałeś kategorię: **{category_name}**. Czekamy na wiadomość.")

class TicketPanel(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())

class TicketSystem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Rejestrujemy widok, żeby przyciski działały po restarcie bota
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
