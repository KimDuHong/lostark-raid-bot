from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(Integer, unique=True, nullable=False)
    discord_name = Column(String, nullable=False)
    discord_avatar = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

class Raid(Base):
    __tablename__ = 'raids'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    gold = Column(Integer, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    participants = relationship("RaidParticipant", back_populates="raid", cascade="all, delete-orphan")

class RaidParticipant(Base):
    __tablename__ = 'raid_participants'
    id = Column(Integer, primary_key=True, autoincrement=True)
    raid_id = Column(Integer, ForeignKey('raids.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(Integer, nullable=False)
    joined_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    raid = relationship("Raid", back_populates="participants")

    # raid_id, user_id 쌍에 대한 UniqueConstraint는 모델 내에서가 아닌 DB Migration 시 가능.
    # 혹은 Base.metadata.create_all 후에 CREATE UNIQUE INDEX 등으로 추가 가능.

class Expedition(Base):
    __tablename__ = 'expeditions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False)         # 디스코드 유저 ID
    expedition_name = Column(String, nullable=False)  # 원정대 이름 (API 응답에 따라 다를 수 있음)
    server_name = Column(String, nullable=False)
    expedition_level = Column(Integer, nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    # 원정대 내 캐릭터들
    characters = relationship("ExpeditionCharacter", back_populates="expedition", cascade="all, delete-orphan")

class ExpeditionCharacter(Base):
    __tablename__ = 'expedition_characters'
    id = Column(Integer, primary_key=True, autoincrement=True)
    expedition_id = Column(Integer, ForeignKey('expeditions.id', ondelete='CASCADE'), nullable=False)
    character_name = Column(String, nullable=False)
    character_class = Column(String, nullable=True)
    item_level = Column(Integer, nullable=True)
    server_name = Column(String, nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.current_timestamp(), onupdate=func.current_timestamp())

    expedition = relationship("Expedition", back_populates="characters")
