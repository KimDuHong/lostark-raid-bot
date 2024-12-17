import discord
from discord.ext import commands
from discord import app_commands, Embed, Color
import requests
from datetime import datetime, time, timedelta
from dateutil import parser as date_parser
import pytz
from utils.logger_config import logger

logger = logger.getChild("cogs.utils")


class UtilsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    MERCHANT_INTERVALS = [
        (time(22, 0), time(3, 30)),
        (time(16, 0), time(21, 30)),
        (time(10, 0), time(15, 30)),
        (time(4, 0), time(9, 30)),
    ]

    def get_current_interval_start(self):

        kst_tz = pytz.timezone("Asia/Seoul")
        now = datetime.now(kst_tz)
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
                "아래는 현재 떠상 시간대 내에 등록된 정보입니다.\n"
                f"**시작 시각 (KST)**: {interval_start.strftime('%Y-%m-%d %H:%M')}"
            ),
            color=Color.green(),
            timestamp=datetime.now(),
        )
        embed.set_footer(text="출처: kloa.gg")

        continent_map = {}

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
                logger.info(f"Item type: {it_type}")

                if it_type == 0:  # 카드
                    continent_map[continent]["cards"].append(f"**{content}**")
                elif it_type == 1:  # 호감도
                    if content == "0":
                        continent_map[continent]["heroic_likes"].append("영웅 호감도")
                    elif content == "1":
                        continent_map[continent]["legendary_likes"].append(
                            "**전설 호감도**"
                        )
                    else:
                        continent_map[continent]["others"].append(f"**{content}**")
                else:  # 기타
                    continent_map[continent]["others"].append(f"**{content}**")

        # 대륙별로 하나의 필드만 추가
        for continent, items_dict in continent_map.items():
            cards = list(set(items_dict["cards"]))
            heroic = list(set(items_dict["heroic_likes"]))
            legendary = list(set(items_dict["legendary_likes"]))
            others = list(set(items_dict["others"]))

            # 각 카테고리별 내용 정리
            parts = []
            if cards:
                cards_str = "\n".join([f"• {c}" for c in cards])
                parts.append(f"**[카드]**\n{cards_str}")
            if heroic or legendary:
                # 호감도 묶어서 표현
                like_lines = []
                if heroic:
                    like_lines.extend([f"• {h}" for h in heroic])
                if legendary:
                    like_lines.extend([f"• {l}" for l in legendary])
                if like_lines:
                    parts.append(f"**[호감도]**\n" + "\n".join(like_lines))
            if others:
                others_str = "\n".join([f"• {o}" for o in others])
                parts.append(f"**[기타 아이템]**\n{others_str}")

            field_value = "\n\n".join(parts) if parts else "정보 없음"
            embed.add_field(name=f"🌏 {continent}", value=field_value, inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(UtilsCog(bot))
