import telebot, requests, os, datetime, sqlite3
from dotenv import load_dotenv
from datetime import datetime
from yandex_speechkit import auth_iam_token, s3_session, yandex_uploadfile, auth_speechkit, delete_file
from Task_create import create_task, get_access_token

load_dotenv()

TOKEN = os.getenv('token') # Не удалять, переменная используется в коде
bot = telebot.TeleBot(TOKEN)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start_handler(message):
    # Устанавливаем соединение с базой данных
    con = sqlite3.connect("users.db")
    cursor = con.cursor()
    # Добавляем строку в таблицу users с данными пользователя telegram
    # Предварительно проверим на наличие ранее записанного username
    cursor.execute("SELECT chat_id FROM users WHERE chat_id = ?", (message.chat.id,))
    row = cursor.fetchone()

    if row:
        pass
    else:
        cursor.execute("INSERT INTO users (chat_id, username, first_name, last_name) VALUES (?, ?, ?, ?)", 
                       (message.chat.id, message.chat.username, message.chat.first_name, message.chat.last_name)
                       )
        con.commit()

    start_text = f"""
Привет! Я бот для постановки задач в Битрикс24 с помощью голоса и текста

<b>Для предварительной настройки напишите администратору бота {os.getenv("login_admin")}</b>
"""
    bot.send_message(message.chat.id, start_text, parse_mode="HTML")


# Обработчик команды /help
@bot.message_handler(commands=['help'])
def help_handler(message):
    help_text = """
Чтобы поставить задачу в Битрикс24, вы можете отправить мне голосовое сообщение.

Также задачу можно поставить с помощью текстового сообщения, для этого в начале текста задачи напишите префикс:
<b>ЗАДАЧА</b> ...  <i>(текст задачи)</i>
"""
    bot.send_message(message.chat.id, help_text, parse_mode="HTML")


# Обработчик команды /ping
@bot.message_handler(commands=['ping'])
def ping_pong_handler(message):
    text = "pong"
    bot.send_message(message.chat.id, text, parse_mode="HTML")


# Обработчик голосовых сообщений
@bot.message_handler(content_types=['voice'])
def voice_handler(message: telebot.types.Message):
    bot.send_message(message.chat.id, "Голосовое сообщение принято, ожидайте ответа")
    file_info = bot.get_file(message.voice.file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path))

    # Сохраняем аудиофайл локально
    path_file = f"voices/voice{message.chat.id}_{datetime.now():%d-%m-%Y_%H-%M}.ogg"
    with open(path_file, 'wb') as f:
        f.write(file.content)

    # Авторизуемся в Yandex Cloud, загружаем файл в облако и получаем ссылку, передаем ссылку в speechkit
    IAM_TOKEN = auth_iam_token() # Получаем IAM_TOKEN
    s3 = s3_session() # Получаем сессию s3
    filelink = yandex_uploadfile(path_file, s3) # Загружаем аудиофайл на облако
    text = auth_speechkit(filelink, IAM_TOKEN) # Сохраняем распознанную речь

    # Получаем id_b24 пользователя из базы данных
    # Устанавливаем соединение с базой данных и получаем id_b24
    con = sqlite3.connect("users.db")
    cursor = con.cursor()
    cursor.execute(f"SELECT id_b24 FROM users WHERE chat_id = ?", (message.chat.id,))
    row = cursor.fetchone()
    id_b24 = row[0]

    # Получаем access_token bitrix24
    access_token = get_access_token()

    # Создаем новую задачу, в описание добавляем распознанный текст
    task = create_task(id_b24, text, access_token)
    task_id = task["task"]["id"]

    # Отправляем сообщение пользователю в Телеграм
    message_text = f"""
<b>Задача создана (id: {task_id}):</b>

{text}

<b>Ссылка на задачу:</b> {os.getenv('url-b24')}company/personal/user/{id_b24}/tasks/task/view/{task_id}/
    """

    bot.send_message(message.chat.id, message_text, parse_mode="HTML")

    # Удаляем загруженные аудиофайлы
    delete_file(path_file, s3) # Удаляем ранее загруженный аудиофайл из облака
    os.remove(path_file) # Удаляем локальный аудиофайл


# Обработчик текстовых сообщений, если содержит "ЗАДАЧА" - поставить задачу в Б24
@bot.message_handler(content_types=['text'])
def send_welcome(message):
    message_text = message.text # Сохраняем текст сообщения для его обработки
    # Если текст сообщения содержит префикс "ЗАДАЧА", то ставим задачу с этим текстом
    if message_text.startswith("ЗАДАЧА"):
        message_text = message_text.replace("ЗАДАЧА", "", 1) # Удалим префикс из текста задачи
        # Получаем id_b24 пользователя из базы данных
        # Устанавливаем соединение с базой данных и получаем id_b24
        con = sqlite3.connect("users.db")
        cursor = con.cursor()
        cursor.execute(f"SELECT id_b24 FROM users WHERE chat_id = ?", (message.chat.id,))
        row = cursor.fetchone()
        id_b24 = row[0]

        # Получаем access_token bitrix24
        access_token = get_access_token()

        # Создаем новую задачу
        task = create_task(id_b24, message_text, access_token)
        task_id = task["task"]["id"]

        # Отправляем сообщение пользователю в Телеграм
        message_text = f"""
<b>Задача создана (id: {task_id}):</b>

{message_text}

<b>Ссылка на задачу:</b> {os.getenv('url-b24')}company/personal/user/{id_b24}/tasks/task/view/{task_id}/
"""
        bot.send_message(message.chat.id, message_text, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, f"Для постановки задачи ботом отправьте ему голосовое сообщение или отправьте текстовое сообщение с префиксом <b>'ЗАДАЧА'</b>.", 
                         parse_mode="HTML")


bot.polling(none_stop=True)