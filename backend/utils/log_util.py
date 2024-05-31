from os import path, getcwd, mkdir
from time import strftime
from loguru import logger

log_path = path.join(getcwd(), 'logs')
if not path.exists(log_path):
    mkdir(log_path)

log_path_error = path.join(log_path, f'{strftime("%Y-%m-%d")}_error.log')

logger.add(log_path_error, rotation="50MB", encoding="utf-8", enqueue=True, compression="zip")
