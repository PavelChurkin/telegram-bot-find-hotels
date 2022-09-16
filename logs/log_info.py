from loguru import logger


def info_only(record):
    return record['level'].name == 'INFO'


def debug_only(record):
    return record['level'].name == 'DEBUG' or 'WARNING'


my_logger = logger
my_logger.add('logs/logs_info.log', level='INFO', format="{time} {message}", filter=info_only)
my_logger.add('logs/logs_debug.log', level='DEBUG', format="{time} {message}", filter=debug_only)
