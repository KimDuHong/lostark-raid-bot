import logging
import os
import discord
from discord.ext import commands
from discord import app_commands, Embed, Color
from discord.ui import View, Button

from schemas.user import DiscordUserSchema
from schemas.expedition import ExpeditionSchema
from service.expedition import ExpeditionService
from utils.database import Database
from utils.logger_config import logger

logger = logger.getChild("cogs.expedition")


class ExpeditionNavigator(View):
    def __init__(self, embeds: list[Embed]):
        super().__init__(timeout=None)
        self.embeds = embeds
        self.index = 0
        self.update_buttons()

    def update_buttons(self):
        self.prev_button.disabled = self.index == 0
        self.next_button.disabled = self.index == len(self.embeds) - 1

    @discord.ui.button(label="이전", style=discord.ButtonStyle.gray)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        self.index -= 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embeds[self.index], view=self
        )

    @discord.ui.button(label="다음", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        self.index += 1
        self.update_buttons()
        await interaction.response.edit_message(
            embed=self.embeds[self.index], view=self
        )


def format_expeditions_to_embeds(
    msg: str, expeditions: list[ExpeditionSchema]
) -> list[Embed]:
    """ExpeditionSchema 리스트를 Embed 리스트로 변환하는 공용 함수."""
    embeds = []
    for exp in expeditions:
        embed = Embed(
            title=f"**{exp.server_name}** 원정대 정보",
            description=f"> {msg}\n",
            color=Color.blue(),
        )
        # 대표 캐릭터 이미지
        if exp.character_image:
            embed.set_thumbnail(url=exp.character_image)

        # 원정대 레벨 정보
        embed.add_field(
            name="원정대 레벨", value=f"**{exp.expedition_level}**", inline=True
        )
        embed.add_field(name="서버", value=f"**{exp.server_name}**", inline=True)

        # 캐릭터 목록 정리
        chars_info_lines = []
        for char in exp.characters:
            main_char_label = "⭐" if char.main_character else ""
            chars_info_lines.append(
                f"{main_char_label} **{char.character_name}**\n"
                f"└ {char.character_class}, {char.item_level} \n"
            )

        if chars_info_lines:
            chars_info = "\n".join(chars_info_lines)
        else:
            chars_info = "등록된 캐릭터가 없습니다."

        # 캐릭터 정보 필드 추가
        embed.add_field(name="캐릭터 목록", value=chars_info, inline=False)

        embeds.append(embed)

    return embeds


class ExpeditionCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = Database()

    @app_commands.command(
        name="원정대검색",
        description="특정 캐릭터명을 기반으로 원정대 정보를 검색하고 표시합니다.",
    )
    async def search_expedition(
        self, interaction: discord.Interaction, character_name: str
    ):
        # 검색은 결과를 모두가 볼 수 있게 ephemeral=False로 설정
        process_message = f"{character_name} : 원정대 정보를 불러오는 중입니다."
        await interaction.response.send_message(process_message, ephemeral=False)
        async with interaction.channel.typing():
            # register=False 로 호출하면 검색 결과를 반환
            msg, expeditions = ExpeditionService().get_and_save_expedition(
                DiscordUserSchema(
                    discord_id=interaction.user.id,
                    discord_name=interaction.user.display_name,
                    discord_avatar=(
                        str(interaction.user.avatar.url)
                        if interaction.user.avatar
                        else None
                    ),
                ),
                character_name,
                register=False,
            )

            if not expeditions or len(expeditions) == 0:
                await interaction.followup.send(msg, ephemeral=False)
                return

            embeds = format_expeditions_to_embeds(msg, expeditions)

            if len(embeds) > 1:
                view = ExpeditionNavigator(embeds)
                await interaction.followup.send(
                    embed=embeds[0], view=view, ephemeral=False
                )
            else:
                await interaction.followup.send(embed=embeds[0], ephemeral=False)

    @app_commands.command(
        name="원정대등록",
        description="특정 캐릭터명을 기반으로 원정대 정보를 DB에 저장합니다. (본인만 확인 가능)",
    )
    async def register_expedition(
        self, interaction: discord.Interaction, character_name: str
    ):
        # 등록은 본인만 볼 수 있게 ephemeral=True
        process_message = f"{character_name} : 원정대 정보를 등록/갱신중..."
        await interaction.response.send_message(process_message, ephemeral=True)
        async with interaction.channel.typing():
            # register=True 로 호출하면 저장만 수행 후 메시지 반환
            msg, expeditions = ExpeditionService().get_and_save_expedition(
                DiscordUserSchema(
                    discord_id=interaction.user.id,
                    discord_name=interaction.user.display_name,
                    discord_avatar=(
                        str(interaction.user.avatar.url)
                        if interaction.user.avatar
                        else None
                    ),
                ),
                character_name,
                register=True,
            )
            await interaction.followup.send(
                f"원정대 정보가 등록되었습니다. ({msg})", ephemeral=True
            )

    @app_commands.command(
        name="내원정대",
        description="DB에 저장된 나의 원정대 정보를 확인합니다. (본인만 확인 가능)",
    )
    async def my_expeditions(self, interaction: discord.Interaction):
        # 내원정대 정보는 본인만 확인 가능하므로 ephemeral=True
        logger.info(f"Fetching saved expeditions for user {interaction.user.id}")
        expeditions = self.db.get_expeditions(interaction.user.id)

        if not expeditions:
            logger.info("No saved expeditions found")
            await interaction.response.send_message(
                "저장된 원정대 정보가 없습니다.", ephemeral=True
            )
            return

        msg = "저장된 원정대 정보 조회 완료"
        embeds = format_expeditions_to_embeds(msg, expeditions)

        if len(embeds) > 1:
            view = ExpeditionNavigator(embeds)
            await interaction.response.send_message(
                embed=embeds[0], view=view, ephemeral=True
            )
        else:
            await interaction.response.send_message(embed=embeds[0], ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ExpeditionCog(bot))
