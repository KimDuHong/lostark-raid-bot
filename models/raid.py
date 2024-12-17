from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    TIMESTAMP,
    func,
    Enum,
    Boolean,
    DateTime,
    Text,
    Float,
)
from sqlalchemy.orm import relationship, declarative_base
import enum
from . import Base


class Raid(Base):
    """
    레이드 기본 정보 테이블.
    예: 발탄, 비아키스, 쿠크세이튼 등의 레이드명.
    """

    __tablename__ = "raids"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)  # 레이드 이름 예: 발탄

    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    # 하나의 Raid에 여러 RaidType(노말, 하드 등)이 존재할 수 있음
    raid_types = relationship("RaidType", back_populates="raid")


class RaidType(Base):
    """
    레이드 종류: 레이드와 난이도를 포함한 구체적 유형(예: 발탄 노말, 발탄 하드)
    여기서 Raid를 참조하여 어떤 레이드인지, 어떤 난이도인지 구분
    """

    class DifficultyLevel(enum.Enum):
        NORMAL = "normal"
        HARD = "hard"
        EXTREME = "extreme"  # 필요에 따라 확장

    __tablename__ = "raid_types"
    id = Column(Integer, primary_key=True, autoincrement=True)
    raid_id = Column(Integer, ForeignKey("raids.id"), nullable=False)
    difficulty = Column(
        Enum(DifficultyLevel), nullable=False, default=DifficultyLevel.NORMAL
    )  # 난이도
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    raid = relationship("Raid", back_populates="raid_types")

    # 관문별 정보를 참조하는 관계
    gates = relationship("RaidGate", back_populates="raid_type")

    recruitments = relationship("RaidRecruitment", back_populates="raid_type")


class RaidGate(Base):
    """
    각 레이드 타입의 관문별 정보 테이블.
    gate_number: 관문 번호 (1관문, 2관문, ...)
    gold: 해당 관문 클리어 시 획득 골드
    """

    __tablename__ = "raid_gates"
    id = Column(Integer, primary_key=True, autoincrement=True)
    raid_type_id = Column(Integer, ForeignKey("raid_types.id"), nullable=False)
    gate_number = Column(Integer, nullable=False)  # 관문 번호
    gold = Column(Integer, nullable=False)  # 해당 관문 획득 골드
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    raid_type = relationship("RaidType", back_populates="gates")


class RaidRecruitment(Base):
    """
    특정 레이드 타입(예: 발탄 노말)에 대한 실제 모집 방(파티).
    """

    class RecruitmentStatus(enum.Enum):
        OPEN = "open"  # 모집 중
        CLOSED = "closed"  # 모집 완료
        CANCELLED = "cancelled"  # 모집 취소

    __tablename__ = "raid_recruitments"
    id = Column(Integer, primary_key=True, autoincrement=True)
    raid_type_id = Column(Integer, ForeignKey("raid_types.id"), nullable=False)
    status = Column(
        Enum(RecruitmentStatus), nullable=False, default=RecruitmentStatus.OPEN
    )
    min_item_level = Column(Integer, nullable=True)  # 참가 조건(최소 아이템 레벨)
    end_time = Column(DateTime, nullable=True)  # 모집 마감 시간
    max_participants = Column(Integer, nullable=True)  # 최대 참가 인원
    description = Column(Text, nullable=True)  # 모집 방에 대한 설명
    is_deleted = Column(Boolean, default=False, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    participants = relationship("RaidParticipant", back_populates="raid_recruitment")
    raid_type = relationship("RaidType", back_populates="recruitments")


class RaidParticipant(Base):
    """
    레이드 모집에 참가한 참가자들 정보.
    """

    __tablename__ = "raid_participants"
    id = Column(Integer, primary_key=True, autoincrement=True)
    raid_recruitment_id = Column(
        Integer, ForeignKey("raid_recruitments.id"), nullable=False
    )
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    is_deleted = Column(Boolean, default=False, nullable=False)
    joined_at = Column(TIMESTAMP, server_default=func.current_timestamp())

    is_deal = Column(Boolean, default=False, nullable=False)  # 딜러 여부
    is_support = Column(Boolean, default=False, nullable=False)  # 힐러 여부
    character_name = Column(String, nullable=False)  # 캐릭터명
    item_level = Column(Integer, nullable=False)  # 아이템 레벨
    character_class = Column(String, nullable=False)  # 직업

    raid_recruitment = relationship("RaidRecruitment", back_populates="participants")
    user = relationship("User", back_populates="raid_participations")
