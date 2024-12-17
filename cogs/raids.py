import logging
import os
import discord
from discord.ext import commands
from discord import app_commands
from utils.database import Database

logger = logging.getLogger(__name__)


class RaidControlView(discord.ui.View):
    def __init__(self, db: Database, raid_id: int):
        super().__init__(timeout=None)
        self.db = db
        self.raid_id = raid_id

    @discord.ui.button(label="참가", style=discord.ButtonStyle.green)
    async def join_raid(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        success = self.db.add_participant(self.raid_id, interaction.user.id)
        if success:
            logger.info(f"{interaction.user} joined raid {self.raid_id}")
            await interaction.response.send_message(
                f"{interaction.user.mention}님이 레이드에 참가했습니다!", ephemeral=True
            )
        else:
            logger.info(f"{interaction.user} already in raid {self.raid_id}")
            await interaction.response.send_message(
                "이미 참가한 상태입니다.", ephemeral=True
            )

    @discord.ui.button(label="취소", style=discord.ButtonStyle.red)
    async def leave_raid(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        self.db.remove_participant(self.raid_id, interaction.user.id)
        logger.info(f"{interaction.user} left raid {self.raid_id}")
        await interaction.response.send_message(
            f"{interaction.user.mention}님이 레이드 참가를 취소했습니다.",
            ephemeral=True,
        )


class RaidCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database()

    @app_commands.command(name="레이드추가", description="새로운 레이드를 추가합니다.")
    async def add_raid(self, interaction: discord.Interaction, name: str, gold: int):
        logger.info(f"Attempting to add raid {name} with gold {gold}")
        raid_id = self.db.add_raid(name, gold)
        if raid_id:
            view = RaidControlView(self.db, raid_id)
            logger.info(f"Raid {name} ({raid_id}) added successfully.")
            await interaction.response.send_message(
                f"레이드 **{name}**가 추가되었습니다!", view=view
            )
        else:
            logger.warning(f"Raid {name} already exists.")
            await interaction.response.send_message(
                f"레이드 **{name}**는 이미 존재합니다.", ephemeral=True
            )

    @app_commands.command(
        name="레이드목록", description="현재 참여 가능한 레이드 목록을 확인합니다."
    )
    async def list_raids(self, interaction: discord.Interaction):
        # raids = self.db.get_raids()
        # if not raids:
        #     logger.info("No active raids available.")
        #     await interaction.response.send_message("현재 참여 가능한 레이드가 없습니다.", ephemeral=True)
        #     return
        #
        # description = "\n".join([f"ID: {raid.id} | **{raid.name}** | 골드: {raid.gold} | 생성일: {raid.created_at}" for raid in raids])
        # logger.info(f"Listed {len(raids)} raids.")
        await interaction.response.send_message(
            f"**참여 가능한 레이드 목록**", ephemeral=True
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(RaidCog(bot))
