from typing import List
from sqlalchemy.orm import Session

from schemas.expedition import ExpeditionSchema
from schemas.user import DiscordUserSchema
from models.user import User
from models.expedition import Expedition, ExpeditionCharacter


class ExpeditionRepository:
    def __init__(self, session_factory):
        # session_factory는 session을 제공하는 callble, 예: session_factory = sessionmaker(bind=engine)
        self.session_factory = session_factory

    def upsert_expedition(
        self, user: DiscordUserSchema, expedition_list: List[ExpeditionSchema]
    ):
        with self.session_factory() as session:  # SessionContext
            # 유저 확인 또는 생성
            db_user = (
                session.query(User).filter(User.discord_id == user.discord_id).first()
            )
            if not db_user:
                db_user = User(
                    discord_id=user.discord_id,
                    discord_name=user.discord_name,
                    discord_avatar=user.discord_avatar,
                )
                session.add(db_user)
                session.flush()

            user_expeditions = (
                session.query(Expedition).filter(Expedition.user_id == db_user.id).all()
            )
            for expedition in user_expeditions:
                session.delete(expedition)
            session.flush()
            for expedition_data in expedition_list:
                # 해당 유저에 맞는 Expedition 조회
                db_expedition = (
                    session.query(Expedition)
                    .filter(
                        Expedition.user_id == db_user.id,
                        Expedition.server_name == expedition_data.server_name,
                    )
                    .first()
                )

                if db_expedition:
                    # 업데이트
                    db_expedition.expedition_level = expedition_data.expedition_level
                    # 캐릭터 정보는 전부 새로 넣기 위해 기존 것 삭제
                    session.query(ExpeditionCharacter).filter_by(
                        expedition_id=db_expedition.id
                    )
                else:
                    # 신규 생성
                    db_expedition = Expedition(
                        user_id=db_user.id,
                        server_name=expedition_data.server_name,
                        expedition_level=expedition_data.expedition_level,
                    )
                    session.add(db_expedition)
                    session.flush()

                # 캐릭터 정보 추가
                for char_data in expedition_data.characters:
                    db_char = ExpeditionCharacter(
                        expedition_id=db_expedition.id,
                        character_name=char_data.character_name,
                        character_class=char_data.character_class,
                        item_level=char_data.item_level,
                        server_name=char_data.server_name,
                    )
                    session.add(db_char)

            session.commit()
