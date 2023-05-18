import telebot, requests, os, datetime
from datetime import datetime
from dotenv import load_dotenv
from yandex_speechkit import auth_iam_token, auth_access_key, yandex_uploadfile, auth_speechkit, delete_file

load_dotenv()


TOKEN = os.getenv('token')
bot = telebot.TeleBot(TOKEN)


# Создаем обработчик для голосовых сообщений
@bot.message_handler(content_types=['voice'])
def repeat_all_message(message: telebot.types.Message):
    bot.send_message(message.chat.id, "Голосовое сообщение принято, ожидайте ответа")
    file_info = bot.get_file(message.voice.file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(TOKEN, file_info.file_path))

    # Сохраняем аудиофайл локально
    path_file = f"voices/voice{message.chat.id}_{datetime.now():%d-%m-%Y_%H-%M}.ogg"
    with open(path_file, 'wb') as f:
        f.write(file.content)

    IAM_TOKEN = auth_iam_token() # Получаем IAM_TOKEN
    s3 = auth_access_key(IAM_TOKEN) # Получаем сессию s3
    filelink = yandex_uploadfile(path_file, s3) # Загружаем аудиофайл на облако
    text = auth_speechkit(filelink, IAM_TOKEN) # Сохраняем распознанную речь в переменную

    bot.send_message(message.chat.id, f"<b>Распознанная речь:</b> \n\n{text}", parse_mode='HTML')
    print(f"Создан файл: {path_file}, распознанный текст: {text}")

    delete_file(path_file, s3) # Удаляем ранее загруженный аудиофайл из облака
    os.remove(path_file) # Удаляем локальный аудиофайл


# Создаем обработчик для текстовых сообщений
@bot.message_handler(content_types=['text'])
def send_welcome(message):
    bot.send_message(message.chat.id, f"Этот бот умеет обрабатывать только голосовое сообщение")


bot.polling(none_stop=True)
