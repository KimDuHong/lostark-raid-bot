from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship
from . import Base


class Expedition(Base):
    __tablename__ = "expeditions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    server_name = Column(String, nullable=False)
    expedition_level = Column(Integer, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    user = relationship("User", back_populates="expeditions")
    characters = relationship("ExpeditionCharacter", back_populates="expedition")


class ExpeditionCharacter(Base):
    __tablename__ = "expedition_characters"

    id = Column(Integer, primary_key=True, autoincrement=True)
    expedition_id = Column(Integer, ForeignKey("expeditions.id"), nullable=False)
    character_name = Column(String, nullable=False)
    character_class = Column(String, nullable=False)
    item_level = Column(Integer, nullable=False)
    server_name = Column(String, nullable=False)
    main_character = Column(Boolean, default=False, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False)
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    expedition = relationship("Expedition", back_populates="characters")
