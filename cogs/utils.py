import discord
from discord.ext import commands
from discord import app_commands, Embed, Color
import requests
from datetime import datetime, time, timedelta
from dateutil import parser as date_parser  # pip install python-dateutil

from utils.logger_config import logger

logger = logger.getChild("cogs.utils")


class UtilsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 떠상 시간대 정의
    MERCHANT_INTERVALS = [
        (time(22, 0), time(3, 30)),  # 오후 10:00 ~ 오전 3:30
        (time(16, 0), time(21, 30)),  # 오후 4:00 ~ 오후 9:30
        (time(10, 0), time(15, 30)),  # 오전 10:00 ~ 오후 3:30
        (time(4, 0), time(9, 30)),  # 오전 4:00 ~ 오전 9:30
    ]

    def get_current_interval_start(self):
        now = datetime.now()
        current_time = now.time()

        for start_t, end_t in self.MERCHANT_INTERVALS:
            if start_t <= end_t:
                if start_t <= current_time <= end_t:
                    return datetime(
                        now.year,
                        now.month,
                        now.day,
                        start_t.hour,
                        start_t.minute,
                        start_t.second,
                    )
            else:
                # 날짜를 넘어가는 구간 (예: 22:00~03:30)
                if current_time >= start_t or current_time <= end_t:
                    start_date = now.date()
                    if current_time <= end_t:
                        start_date = (now - timedelta(days=1)).date()

                    return datetime(
                        start_date.year,
                        start_date.month,
                        start_date.day,
                        start_t.hour,
                        start_t.minute,
                        start_t.second,
                    )

        return None

    @app_commands.command(
        name="떠돌이상인", description="떠돌이상인 정보를 표시합니다."
    )
    async def show_wandering_merchant(self, interaction: discord.Interaction):
        kloa_api_url = "https://api.korlark.com/merchants?limit=15&server=1"
        response = requests.get(kloa_api_url)
        if response.status_code != 200:
            await interaction.response.send_message(
                "떠돌이 상인 정보를 불러오는 데 실패했습니다.", ephemeral=True
            )
            return

        data = response.json()
        merchants = data.get("merchants", [])

        interval_start = self.get_current_interval_start()
        if interval_start is None:
            await interaction.response.send_message(
                "현재 떠상 시간이 아닙니다.", ephemeral=True
            )
            return

        # interval_start 이후에 등록된 것만 필터링 (UTC->KST 변환: +9시간)
        filtered_merchants = []
        for m in merchants:
            created_at_str = m.get("created_at")
            if created_at_str:
                created_time = date_parser.parse(created_at_str) + timedelta(hours=9)
                if created_time >= interval_start:
                    filtered_merchants.append(m)

        if not filtered_merchants:
            await interaction.response.send_message(
                "현재 해당 시간대에 등록된 떠상이 없습니다.", ephemeral=True
            )
            return

        embed = Embed(
            title="현재 떠돌이 상인 정보",
            description=(
                f"**시작 시각**: {interval_start.strftime('%Y-%m-%d %H:%M')}"
                f"\n**종료 시각**: {interval_start + timedelta(hours=5, minutes=30)}"
            ),
            color=Color.green(),
            timestamp=datetime.now(),
        )
        embed.set_footer(text="출처: kloa.gg")
        # 필요하다면 썸네일 추가 가능
        # embed.set_thumbnail(url="https://i.imgur.com/y5BmX0T.png")

        # 대륙별로 아이템을 타입별로 분류
        # 타입별: 카드(type=0), 호감도(type=1 -> 영웅(0), 전설(1)), 기타(type=2)
        # 각 대륙별로 카드/호감도/기타를 구분해서 inline field로 표시
        continent_map = (
            {}
        )  # {continent: {'cards':[], 'heroic_likes':[], 'legendary_likes':[], 'others':[]}}

        for m in filtered_merchants:
            continent = m.get("continent", "알 수 없음")
            items_data = m.get("items", [])

            if continent not in continent_map:
                continent_map[continent] = {
                    "cards": [],
                    "heroic_likes": [],
                    "legendary_likes": [],
                    "others": [],
                }

            for it in items_data:
                it_type = it.get("type", "")
                content = it.get("content", "")
                # 타입별 분류
                if it_type == 0:  # 카드
                    # 카드명 강조
                    continent_map[continent]["cards"].append(f"{content}")
                elif it_type == 1:  # 호감도
                    if content == "0":
                        continent_map[continent]["heroic_likes"].append("영웅 호감도")
                    elif content == "1":
                        continent_map[continent]["legendary_likes"].append(
                            "**전설 호감도**"
                        )
                    else:
                        continent_map[continent]["others"].append(f"**{content}**")
                else:  # 기타 (type=2 등)
                    continent_map[continent]["others"].append(f"{content}")

        # 임베드에 대륙별 정보 추가
        for continent, items_dict in continent_map.items():
            cards = items_dict["cards"]
            heroic = items_dict["heroic_likes"]
            legendary = items_dict["legendary_likes"]
            others = items_dict["others"]

            # 중복 제거
            cards = list(set(cards))
            heroic = list(set(heroic))
            legendary = list(set(legendary))
            others = list(set(others))

            # 대륙 이름을 먼저 필드로 표시(굵게)
            # 대륙명을 제목으로 사용하고, 그 아래 inline 필드들로 카드/호감도/기타를 표시
            embed.add_field(name="", value=f"**🌏{continent}**", inline=False)

            # 카드 필드 (inline)
            if cards:
                card_str = "\n".join([f"• {c}" for c in cards])
                embed.add_field(name="카드", value=card_str, inline=True)

            # 호감도 필드 (영웅/전설 합쳐서 표시)
            if heroic or legendary:
                like_lines = []
                if heroic:
                    like_lines.extend([f"• {h}" for h in heroic])
                if legendary:
                    like_lines.extend([f"• {l}" for l in legendary])
                like_str = "\n".join(like_lines) if like_lines else "정보 없음"
                embed.add_field(name="호감도", value=like_str, inline=True)

            # 기타 아이템 필드 (inline)
            if others:
                others_str = "\n".join([f"• {o}" for o in others])
                embed.add_field(name="기타 아이템", value=others_str, inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilsCog(bot))
