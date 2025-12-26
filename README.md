# Telegram Bot для проверки API партнёра

Этот бот на aiogram 3.x предназначен для минимального тестирования API партнёра. Он принимает фото, отправляет их на сервер партнёра, получает task_id, позволяет проверять статус и принимает вебхуки.

## Установка и локальный запуск

1. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```

2. Создайте .env файл и заполните переменные:
   - `BOT_TOKEN`: токен бота от @BotFather
   - `PARTNER_API_BASE_URL`: базовый URL API партнёра (https://api.grtkniv.net)
   - `API_KEY`: API ключ партнёра
   - `PARTNER_WEBHOOK_URL`: публичный URL для вебхуков от партнёра (например, https://your-app.onrender.com/webhook)

3. Запустите бота:
   ```
   python main.py
   ```

Бот запустится с вебхуками. Сервер вебхуков будет слушать на порту 8081 (или PORT из переменной окружения).

## Деплой на Render.com (бесплатный)

1. Создайте публичный репозиторий на GitHub и загрузите код:
   ```
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/your-username/your-repo.git
   git push -u origin master
   ```

2. Зарегистрируйтесь на [render.com](https://render.com).

3. Создайте новый **Web Service**:
   - Подключите ваш GitHub репозиторий.
   - **Runtime**: Python 3.
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`

4. В разделе **Environment** добавьте переменные окружения:
   - `BOT_TOKEN`
   - `PARTNER_API_BASE_URL`
   - `API_KEY`
   - `PARTNER_WEBHOOK_URL` (URL вашего Render аппа, например https://your-app.onrender.com/webhook)

5. Нажмите **Create Web Service**. Render автоматически задеплоит и даст постоянный URL.

Бот будет работать 24/7, вебхуки стабильны.

## Тестирование

- Отправьте /start боту в Telegram.
- Отправьте фото — бот загрузит его на API партнёра и вернёт task_id.
- Используйте /check <task_id> для проверки статуса.
- Результаты приходят через вебхук от партнёра.

## Структура кода

- `main.py`: основной код бота и сервера вебхуков.
- `.env`: локальная конфигурация (не в git).
- `requirements.txt`: зависимости.
- `.gitignore`: игнорируемые файлы.
