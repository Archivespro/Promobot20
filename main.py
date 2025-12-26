import asyncio
import os
import uuid
import json
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# Команда /start: приветственное сообщение
@dp.message(Command('start'))
async def start_command(message: types.Message):
    await message.reply("Отправьте фото")

# Обработка фото: принимаем только изображения
@dp.message(lambda message: message.photo)
async def handle_photo(message: types.Message):
    print("Фото получено от пользователя")
    # Получаем самое большое фото
    photo = message.photo[-1]
    # Скачиваем файл
    file = await bot.download(photo.file_id)
    # Сохраняем временно
    with open('temp_photo.jpg', 'wb') as f:
        f.write(file.read())
    print("Фото сохранено, отправляю на API партнёра")

    # Генерируем уникальный id_gen
    id_gen = str(uuid.uuid4())
    # URL для загрузки на API партнёра: /api/imageGenerations/undress
    partner_url = os.getenv('PARTNER_API_BASE_URL') + '/api/imageGenerations/undress'
    headers = {'Authorization': os.getenv('API_KEY')}
    async with aiohttp.ClientSession() as session:
        # Отправляем как multipart/form-data
        with open('temp_photo.jpg', 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('id_gen', id_gen)
            data.add_field('image', f, filename='photo.jpg')
            data.add_field('webhook', os.getenv('PARTNER_WEBHOOK_URL'))
            async with session.post(partner_url, data=data, headers=headers) as resp:
                # Ожидаем JSON ответ: {"queueNumber": 1, "apiBalance": 100, "id_gen": "gen_...", "queueTime": 30}
                response_json = await resp.json()
                task_id = response_json.get('id_gen')
                await message.reply(f"Фото загружено. Task ID: {task_id}")

                # Сохраняем task_id -> chat_id
                tasks = {}
                if os.path.exists('tasks.json'):
                    with open('tasks.json', 'r') as f:
                        tasks = json.load(f)
                tasks[task_id] = message.chat.id
                with open('tasks.json', 'w') as f:
                    json.dump(tasks, f)

    # Удаляем временный файл
    os.remove('temp_photo.jpg')

# Команда /check <task_id>: проверка статуса задачи
@dp.message(Command('check'))
async def check_command(message: types.Message):
    # Разбираем аргументы
    args = message.text.split()
    if len(args) < 2:
        await message.reply("Использование: /check <task_id>")
        return
    task_id = args[1]
    # POST запрос на /api/imageGenerations/position для проверки очереди
    partner_url = os.getenv('PARTNER_API_BASE_URL') + '/api/imageGenerations/position'
    headers = {'Authorization': os.getenv('API_KEY')}
    async with aiohttp.ClientSession() as session:
        data = aiohttp.FormData()
        data.add_field('id_gen', task_id)
        async with session.post(partner_url, data=data, headers=headers) as resp:
            # Ожидаем JSON ответ: {"queueNumber": 0} (0 - готово)
            response_json = await resp.json()
            queue = response_json.get('queueNumber', 'unknown')
            await message.reply(f"Позиция в очереди: {queue}. Если 0 - готово (результат в webhook).")

# Игнорируем другие сообщения
@dp.message()
async def ignore_other(message: types.Message):
    await message.reply("Пожалуйста, отправь только фото.")

# Обработчик вебхуков от партнёра: принимает POST multipart/form-data с undressingId, image, video, error
async def partner_webhook(request):
    # Получаем данные из формы
    data = await request.post()
    undressingId = data.get('undressingId')
    image = data.get('image')  # file
    video = data.get('video')  # file
    error = data.get('error')
    # Логируем в консоль
    print(f"Получен вебхук от партнёра: task_id={undressingId}, image={bool(image)}, video={bool(video)}, error={error}")

    # Отправляем результат пользователю
    if undressingId:
        if os.path.exists('tasks.json'):
            with open('tasks.json', 'r') as f:
                tasks = json.load(f)
            chat_id = tasks.get(undressingId)
            if chat_id:
                if image:
                    # Сохраняем файл
                    with open('result_image.jpg', 'wb') as f:
                        f.write(image.file.read())
                    await bot.send_photo(chat_id, types.FSInputFile('result_image.jpg'), caption="Готово!")
                    os.remove('result_image.jpg')
                if video:
                    with open('result_video.mp4', 'wb') as f:
                        f.write(video.file.read())
                    await bot.send_video(chat_id, types.FSInputFile('result_video.mp4'), caption="Готово!")
                    os.remove('result_video.mp4')
                if error:
                    await bot.send_message(chat_id, f"Ошибка обработки: {error}")

    return web.Response(text="OK")

async def main():
    # Запуск aiohttp сервера для обработки вебхуков от партнёра на порту 8080
    app = web.Application()
    app.router.add_post('/webhook', partner_webhook)
    runner = web.AppRunner(app, client_max_size=100*1024*1024)  # 100MB for large files
    await runner.setup()
    port = int(os.getenv('PORT', 8081))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print("Сервер вебхуков запущен на http://0.0.0.0:8081")

    # Удаляем webhook, если был установлен
    await bot.delete_webhook()
    print("Webhook удалён")

    # Запуск бота в режиме polling
    print("Запуск бота в режиме polling")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
