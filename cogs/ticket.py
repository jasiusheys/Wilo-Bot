import discord
from discord import ui
from discord.ext import commands

# --- KONFIGURACJA ---
# Dodaj swoje ID kategorii dla różnych ticketów
CATEGORY_MAP = {
    "Twórca": 1471143729346904065,
    "Ogólne": 1471143729346904065,
    "Nagrywki": 1471143729346904065,
    "Wspieranie": 1471143729346904065,
    "Współpraca": 1471143729346904065
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

        # Tworzenie kanału
        channel = await guild.create_text_channel(
            name=f"ticket-{category_name}-{interaction.user.name}",
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
