# TaskCreatorBot 

С помощью данного бота можно ставить задачи в Битрикс24 из голосовых и текстовых сообщений с префиксом.

Реализован на модели распознавания речи Yandex Speechkit.

## Bot.py:
В боте реализованы обработчики команд и сообщений.
### Обработчик команды /start
### **@bot.message_handler(commands=['start'])**
В данном обработчике идет подключение к базе данных, проверяется наличие пользователя в базе, если пользователь найдет по chat_id, то будет отправлено приветственное сообщение.
Если пользователь не найдет в базе данных, то он будет сохранен в неё.
Далее администратор бота должен сопоставить в базе данных пользователя телеграм с пользователем Битрикс24 (id пользователя портала), чтобы далее по этому id ставить задачи на портале.

### Обработчик команды /help
### **@bot.message_handler(commands=['help'])**
Выводится пояснение по взаимодействию с ботом.

