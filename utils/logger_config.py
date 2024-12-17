import logging
import os
from datetime import datetime

from utils.config import settings

LOG_LEVEL = settings.LOG_LEVEL
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


# 로거 초기화 함수
def init_logger():
    logger = logging.getLogger()
    logger.setLevel(LOG_LEVEL)

    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 파일 핸들러 (logs 디렉토리가 없는 경우 생성)
    if not os.path.exists("logs"):
        os.makedirs("logs")
    today = datetime.today().strftime("%Y%m%d")
    file_handler = logging.FileHandler(f"logs/{today}-bot.log", encoding="utf-8")
    file_handler.setLevel(LOG_LEVEL)
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    return logger


logger = init_logger()
