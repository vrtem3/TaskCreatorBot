import logging.handlers, telebot, os
from datetime import datetime


# Создание логгера
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Создание обработчика для записи в файл
file_handler = logging.handlers.RotatingFileHandler('send_error_message_log.txt', maxBytes=10000, backupCount=0)
file_handler.setLevel(logging.INFO)

# Добавление обработчика в логгер
logger.addHandler(file_handler)


# Уведомление администратору в телеграм от технического бота при появлении ошибок в функциях
def send_error_message(text):
    try:
        bot = telebot.TeleBot(token=os.getenv('notif_token'))
        text_message = f"""
<b>Приложение TaskCreatorBot</b>

{text}
    """
        bot.send_message(os.getenv('admin'), text_message, parse_mode='HTML')
        logger.info(f"{datetime.now():%d %B %Y %H:%M:%S}: send_error_message() - An error message has been sent (main.py)")

    except Exception as e:
        logger.exception(f"{datetime.now():%d %B %Y %H:%M:%S}: Error in the send_error_message (main.py): {e}")

