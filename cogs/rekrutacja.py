
        super().__init__(timeout=None)
        self.applicant = ap
            await interaction.response.send_modal(RecruitmentModal(cfg["event_name"]))
            
        btn.callback = callback
        view.add_item(btn)
        
        embed = discord.Embed(title=f"🎥 REKRUTACJA: {nazwa.upper()}", description="Kliknij przycisk poniżej!", color=discord.Color.gold())
        await ctx.send(embed=embed, view=view)
        await ctx.message.delete()

async def setup(bot):
    await bot.add_cog(Rekrutacja(bot))
