import logging
from schemas.expedition import CharacterSchema, ExpeditionSchema
from schemas.user import DiscordUserSchema
from utils.config import settings
import requests

from repositories.expedition_repository import ExpeditionRepository
from utils.database import Database
from utils.logger_config import logger


class ExpeditionService:
    def __init__(self):
        self.db = Database()
        self.expedition_repository = ExpeditionRepository(self.db.Session)

    def get_and_save_expedition(
        self, user: DiscordUserSchema, character_name: str, register: bool = False
    ):
        logger.info(f"Fetching expedition info for {character_name}")

        url = f"https://developer-lostark.game.onstove.com/characters/{character_name}/siblings"
        headers = {
            "accept": "application/json",
            "authorization": f"Bearer {settings.LOSTARK_API_KEY}",
        }

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logger.warning(
                f"Failed to fetch siblings for {character_name}, status {response.status_code}"
            )
            return "원정대 정보를 불러오는 데 실패했습니다.", None
        try:
            data = response.json()
        except Exception as e:
            logger.error(f"Error parsing expedition data: {e}")
            return "원정대 정보를 불러오는 데 실패했습니다.", None
        print("*" * 50)
        print(data)
        print("*" * 50)
        if not isinstance(data, list) or len(data) == 0:
            logger.info(f"No expedition data for {character_name}")
            return "유효한 원정대 정보를 찾을 수 없습니다.", None

        try:
            server_list = list({char["ServerName"] for char in data})
            expedition_list = []
            for server in server_list:
                charater_list = []
                for char in data:
                    if char["ServerName"] == server:
                        charater = CharacterSchema(
                            character_name=char["CharacterName"],
                            character_class=char["CharacterClassName"],
                            item_level=int(
                                float(char["ItemAvgLevel"].replace(",", ""))
                            ),
                            server_name=char["ServerName"],
                        )
                        charater_list.append(charater)

                # 메인 캐릭터 지정
                charater_list.sort(key=lambda c: c.item_level, reverse=True)
                charater_list[0].main_character = True
                main_char_name = charater_list[0].character_name

                # 메인 캐릭터 프로필 조회
                profile_url = f"https://developer-lostark.game.onstove.com/armories/characters/{main_char_name}?filters=cards%2Bprofiles"
                profile_headers = {
                    "accept": "application/json",
                    "authorization": f"Bearer {settings.LOSTARK_API_KEY}",
                }
                profile_response = requests.get(profile_url, headers=profile_headers)
                if profile_response.status_code == 200:
                    profile_data = profile_response.json()
                    if not profile_data:
                        continue
                    armory_profile = profile_data.get("ArmoryProfile", {})
                    main_profile = armory_profile.get("CharacterImage", "")
                    expedition_level = armory_profile.get("ExpeditionLevel", 0)
                else:
                    logger.warning(f"Failed to fetch profile for {main_char_name}")
                    main_profile = ""
                    expedition_level = 0

                expedition = ExpeditionSchema(
                    character_image=main_profile,
                    server_name=server,
                    expedition_level=expedition_level,
                    characters=charater_list,
                )
                expedition_list.append(expedition)

            if register:
                self.expedition_repository.upsert_expedition(user, expedition_list)

            logger.info(
                f"Fetched expedition info for {character_name}, {len(expedition_list)} expeditions found."
            )
            return (
                f"**{character_name}**의 원정대 정보를 불러왔습니다.",
                expedition_list,
            )

        except Exception as e:
            logger.exception("Error processing expedition data")
            return "원정대 정보를 가공하는 데 실패했습니다.", None
