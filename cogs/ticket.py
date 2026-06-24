import discord
from discord import ui
from discord.ext import commands

# --- KONFIGURACJA ---
CATEGORY_MAP = {
    "Twórca": 1503873245064200234,
    "Ogólne": 1503873389771882606,
    "Nagrywki": 1503873359849590795,
    "Wspieranie": 1503873164315332699,
    "Współpraca": 1503873125434134648
}

ROLE_MAP = {
    "Twórca": 1503899819935137884,
    "Ogólne": 1503899874758754334,
    "Nagrywki": 1503899930861895730,
    "Wspieranie": 1503899965234352309,
    "Współpraca": 1503899819935137884 # Ta sama rola co dla Twórcy
}

ROLE_TO_GIVE = {
    "Wspieranie": 1168276108559523840,
    "Twórca": 1148317718311862302
}

WELCOME_MESSAGES = {
    "Twórca": "Siemka {user}! Jeżeli chcesz odebrać range twórca wyślij tutaj link do swojego kanału na youtubie i czekaj na weryfikacje!",
    "Ogólne": "Siemka {user}! Napisz jaki masz problem i czekaj na odpowiedź!",
    "Nagrywki": "Siemka {user}! Napisz jaki masz problem i czekaj na odpowiedź!",
    "Wspieranie": "Siemka {user}! Jeżeli chcesz odebrac rangę wyślij zrzut ekranu w potwierdzeniem że wspierasz kanał Wila.",
    "Współpraca": "Siemka {user}! Masz jakąś propozycje wspołpracy? Napisz ją tutaj!."
}

LOG_CHANNEL_ID = 1503875231289311282

# --- FUNKCJA LOGUJĄCA ---
async def log_to_channel(guild, title, color, author, category, channel=None, closer=None, action="Utworzono"):
    log_channel = guild.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        embed = discord.Embed(title=f"📁 {title}", color=color)
        embed.add_field(name="Użytkownik", value=author.mention, inline=True)
        embed.add_field(name="Kategoria", value=category, inline=True)
        if channel:
            embed.add_field(name="Kanał", value=channel.mention, inline=False)
        if closer:
            embed.add_field(name="Zamknięte przez", value=closer.mention, inline=True)
        embed.add_field(name="Akcja", value=action, inline=False)
        await log_channel.send(embed=embed)

# --- PRZYCISKI ---
class CategoryTicketView(ui.View):
    def __init__(self, category_name, author: discord.Member):
        super().__init__(timeout=None)
        self.category_name = category_name
        self.author = author

    async def check_perms(self, interaction: discord.Interaction):
        # Administrator ma zawsze dostęp
        if interaction.user.guild_permissions.administrator:
            return True
        
        # Sprawdzamy rolę przypisaną do kategorii
        role_id = ROLE_MAP.get(self.category_name)
        role = interaction.guild.get_role(role_id)
        
        return role is not None and role in interaction.user.roles

    @ui.button(label="🔒 Zamknij", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_perms(interaction):
            return await interaction.response.send_message("❌ Nie masz uprawnień!", ephemeral=True)
        
        await interaction.response.send_message("Zamykanie kanału...", ephemeral=True)
        await log_to_channel(interaction.guild, "Ticket Zamknięty", discord.Color.red(), self.author, self.category_name, closer=interaction.user, action="Ręczne zamknięcie")
        await interaction.channel.delete()

    @ui.button(label="✅ Nadaj rolę", style=discord.ButtonStyle.success, custom_id="give_role")
    async def give(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_perms(interaction):
            return await interaction.response.send_message("❌ Nie masz uprawnień!", ephemeral=True)
        
        role_id = ROLE_TO_GIVE.get(self.category_name)
        role = interaction.guild.get_role(role_id)
        if role:
            await self.author.add_roles(role)
            await log_to_channel(interaction.guild, "Ticket Rozwiązany", discord.Color.green(), self.author, self.category_name, closer=interaction.user, action=f"Nadano rolę: {role.name}")
            await interaction.response.send_message(f"✅ Nadano rolę {role.mention} i zamykam.", ephemeral=True)
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Brak roli do nadania!", ephemeral=True)

class TicketCategorySelect(ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Twórca", description="Wymagania dla twórców", emoji="🎥"),
            discord.SelectOption(label="Ogólne", description="Inne pytania", emoji="⚙️"),
            discord.SelectOption(label="Nagrywki", description="Pytania dotyczące nagrywek", emoji="🎙️"),
            discord.SelectOption(label="Wspieranie", description="Problemy i odbiór rangi", emoji="💎"),
            discord.SelectOption(label="Współpraca", description="Propozycje współpracy", emoji="🤝"),
        ]
        super().__init__(placeholder="Select a category", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat_name = self.values[0]
        guild = interaction.guild
        role = guild.get_role(ROLE_MAP.get(cat_name))
        
        channel_name = f"ticket-{cat_name.lower()}-{interaction.user.name.lower()}"
        if discord.utils.get(guild.text_channels, name=channel_name):
            return await interaction.response.send_message("❌ Masz już otwarty ticket!", ephemeral=True)

        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), 
                      interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=channel_name, category=guild.get_channel(CATEGORY_MAP.get(cat_name)), overwrites=overwrites)
        
        await log_to_channel(guild, "Nowy Ticket", discord.Color.blue(), interaction.user, cat_name, channel=channel, action="Utworzono kanał")
        
        view = CategoryTicketView(cat_name, interaction.user)
        if cat_name not in ROLE_TO_GIVE: view.remove_item(view.give)
            
        await channel.send(WELCOME_MESSAGES.get(cat_name).replace("{user}", interaction.user.mention), view=view)
        await interaction.response.send_message(f"✅ Utworzono: {channel.mention}", ephemeral=True)

class TicketPanel(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(TicketCategorySelect())

class TicketSystem(commands.Cog):
    def __init__(self, bot): self.bot = bot
    @commands.Cog.listener()
    async def on_ready(self): self.bot.add_view(TicketPanel())
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def panel_ticketow(self, ctx):
        embed = discord.Embed(
            title="📥 CENTRUM POMOCY - Wilo Eventy",
            description="Wybierz odpowiednią kategorię z menu poniżej, aby otworzyć nowego ticketa.\n\nPostaramy się pomóc tak szybko, jak to możliwe!\nPingowanie administracji oraz bezpodstawne tickety będą karane!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=TicketPanel())

async def setup(bot): await bot.add_cog(TicketSystem(bot))
