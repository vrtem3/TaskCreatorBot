# TaskCreatorBot 

С помощью данного бота можно ставить задачи в Битрикс24 из голосовых и текстовых сообщений с префиксом.

Реализован на модели распознавания речи Yandex Speechkit.

## Bot.py:
В боте реализованы обработчики команд и сообщений.

### Обработчик команды /start
### @bot.message_handler(commands=['start'])
В данном обработчике идет подключение к базе данных, проверяется наличие пользователя в базе, если пользователь найдет по chat_id, то будет отправлено приветственное сообщение.
Если пользователь не найдет в базе данных, то он будет сохранен в неё.
Далее администратор бота должен сопоставить в базе данных пользователя телеграм с пользователем Битрикс24 (id пользователя портала), чтобы далее по этому id ставить задачи на портале.


### Обработчик команды /help
### @bot.message_handler(commands=['help'])
Выводится пояснение по взаимодействию с ботом.


### Обработчик команды /ping
### @bot.message_handler(commands=['ping'])
Не несет смысловой нагрузки, ответом отправляет "pong". Для проверки работоспособности бота.


### Обработчик голосовых сообщений
### @bot.message_handler(content_types=['voice'])
Здесь получаем голосовое сообщение от пользователя, сохраняем его локально.
Далее происходит авторизация на Yandex Cloud, получение IAM_TOKEN и создание сессии s3.
```
yandex_uploadfile(path_file, s3)
```
Загружаем аудиофайл на облако Яндекса, чтобы далее передать ссылку на этот файл в распознавание речи Yandex Speechkit. Ответом получаем текст из голосового сообщения.
Далее из базы данных получаем id пользователя Битрикс24 по chat_id пользователя.
```
access_token = get_access_token()
```
Получаем новый токен Битрикс24 и далее создаем задачу пользователю в Битрикс24.
```
delete_file(path_file, s3) # Удаляем ранее загруженный аудиофайл из облака
os.remove(path_file) # Удаляем локальный аудиофайл
```
