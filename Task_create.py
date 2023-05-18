import requests, os, sqlite3, logging.handlers
from datetime import datetime
from dotenv import load_dotenv
from send_error_message import send_error_message

load_dotenv()

# Создание логгера
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Создание обработчика для записи в файл
file_handler = logging.handlers.RotatingFileHandler('log.txt', maxBytes=10000, backupCount=0)
file_handler.setLevel(logging.INFO)

# Добавление обработчика в логгер
logger.addHandler(file_handler)


# Получаем актуальные access_token и refresh_token Битрикс24
def get_access_token():
    try:
        con = sqlite3.connect("auth_b24.db")
        cursor = con.cursor()

        # Выполняем запрос и получаем ключи из БД
        cursor.execute("SELECT client_id, client_secret, refresh_token FROM auth WHERE id=1")
        client_id, client_secret, refresh_token = cursor.fetchone()

        url = "https://oauth.bitrix.info/oauth/token/?"
        params = {
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
        }

        # Отправляем get-запрос в Битрикс24 на получение access_token и новый refresh_token
        request = requests.get(url, params=params)
        request.raise_for_status()
        data = request.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # Записываем в БД новый access_token и refresh_token, также сохраним дату обновления токенов
        cursor.execute(f"UPDATE auth SET refresh_token='{refresh_token}', access_token='{access_token}', dateUpdKey='{datetime.now()}' WHERE id=1")
        con.commit()

        logger.info(f"{datetime.now():%d %B %Y %H:%M:%S}: get_access_token() - Tokens received and saved (Task_create.py)")
        return access_token

    except Exception as e:
        send_error_message(f"{datetime.now():%d %B %Y %H:%M:%S}: Error in the get_access_token (Task_create.py): {e}")
        logger.exception(f"{datetime.now():%d %B %Y %H:%M:%S}: Error in the get_access_token (Task_create.py): {e}")


# Создание новой задачи в Битрикс24, на вход получает ID пользователя и текст задачи
def create_task(user_id, title_task, access_token):
    try:
        url = f"{os.getenv('url-b24')}rest/tasks.task.add.json?auth={access_token}"
        params = {
            "fields": {
                "TITLE": title_task,
                "DESCRIPTION": title_task, # Дублируем текст задачи в описание
                "IS_MUTED": 'Y', 
                "CREATED_BY": user_id, # ID постановщика задачи
                "RESPONSIBLE_ID": user_id, # ID ответственного за задачу
            }
        }
        
        # Отправляем post-запрос на создание задачи
        response = requests.post(url, json=params)
        result = response.json()
        task_id = result["result"]

        logger.info(f"{datetime.now():%d %B %Y %H:%M:%S}: create_task() - Task created: {task_id} (Task_create.py)")
        return task_id

    except Exception as e:
        send_error_message(f"{datetime.now():%d %B %Y %H:%M:%S}: Error in the create_task (Task_create.py): {e}")
        logger.exception(f"{datetime.now():%d %B %Y %H:%M:%S}: Error in the create_task (Task_create.py): {e}")


