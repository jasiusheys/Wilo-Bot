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
    "Współpraca": 1503899819935137884
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

# --- PRZYCISKI ---
class CategoryTicketView(ui.View):
    def __init__(self, category_name, author: discord.Member):
        super().__init__(timeout=None)
        self.category_name = category_name
        self.author = author

    async def check_perms(self, interaction: discord.Interaction):
        role = interaction.guild.get_role(ROLE_MAP.get(self.category_name))
        return interaction.user.guild_permissions.administrator or (role and role in interaction.user.roles)

    @ui.button(label="🔒 Zamknij", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_perms(interaction):
            return await interaction.response.send_message("❌ Tylko moderatorzy mogą to zrobić!", ephemeral=True)
        await interaction.response.send_message("Zamykanie kanału...")
        await interaction.channel.delete()

    @ui.button(label="✅ Nadaj rolę", style=discord.ButtonStyle.success, custom_id="give_role")
    async def give(self, interaction: discord.Interaction, button: ui.Button):
        if not await self.check_perms(interaction):
            return await interaction.response.send_message("❌ Tylko moderatorzy mogą to zrobić!", ephemeral=True)
        
        role_id = ROLE_TO_GIVE.get(self.category_name)
        role = interaction.guild.get_role(role_id)
        if role:
            await self.author.add_roles(role)
            await interaction.response.send_message(f"✅ Nadano rolę {role.mention} użytkownikowi {self.author.mention} i zamykam ticket.")
            await interaction.channel.delete()
        else:
            await interaction.response.send_message("❌ Brak zdefiniowanej roli do nadania!", ephemeral=True)

class TicketCategorySelect(ui.Select):
    def __init__(self):
        options = [discord.SelectOption(label=cat, description="Otwórz zgłoszenie", emoji="📂") for cat in CATEGORY_MAP.keys()]
        super().__init__(placeholder="Select a category", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        cat_name = self.values[0]
        guild = interaction.guild
        role = guild.get_role(ROLE_MAP.get(cat_name))
        
        overwrites = {guild.default_role: discord.PermissionOverwrite(read_messages=False), 
                      interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)}
        if role: overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

        channel = await guild.create_text_channel(name=f"ticket-{cat_name.lower()}-{interaction.user.name.lower()}", 
                                                  category=guild.get_channel(CATEGORY_MAP.get(cat_name)), 
                                                  overwrites=overwrites)
        
        view = CategoryTicketView(cat_name, interaction.user)
        # Jeśli kategoria nie ma roli do nadania, usuwamy przycisk "Nadaj rolę"
        if cat_name not in ROLE_TO_GIVE:
            view.remove_item(view.give)
            
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
        await ctx.send(embed=discord.Embed(title="📥 CENTRUM POMOCY", color=discord.Color.blue()), view=TicketPanel())

async def setup(bot): await bot.add_cog(TicketSystem(bot))
