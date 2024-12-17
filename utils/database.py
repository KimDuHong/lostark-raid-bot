import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import logging

from utils.logger_config import logger

# DB_PATH = os.path.join(os.path.dirname(__file__), "lostark.db")
# 루트 디렉토리로 변경
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lostark.db")


class Database:
    def __init__(self):
        self.engine = create_engine(
            f"sqlite:///{DB_PATH}",
            echo=False,
            connect_args={"check_same_thread": False},
        )
        self.Session = sessionmaker(bind=self.engine)

    def create_all(self):
        logger.info("Creating all tables")
        Base.metadata.create_all(self.engine)
