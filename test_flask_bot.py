import asyncio
from threading import Thread
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import os
from dotenv import load_dotenv
load_dotenv()

# Инициализация Flask приложения
app = Flask(__name__)

@app.route('/')
def home():
    return "Flask server is running!"



@app.route('/register', methods=['POST'])
def register():
    # Проверяем авторизацию через Telegram WebApp
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"status": "error", "message": "Unauthorized"}), 401
    
    init_data = auth_header[7:]  # Убираем 'Bearer '
    
    # Здесь должна быть проверка initData (пропущена для краткости)
    # Реальная проверка требует подписи данных с помощью токена бота
    
    # Получаем данные регистрации
    data = request.get_json()
    print(data)
    
    
    # Валидация данных
    if not all(key in data for key in ['type', 'user_id', 'full_name', 'email']):
        return jsonify({"status": "error", "message": "Invalid data format"}), 400
    
    # Здесь должна быть логика сохранения в базу данных
    print("Received registration data:", data)
    
    # Возвращаем успешный ответ
    return jsonify({
        "status": "success",
        "message": "User registered successfully",
        "user_id": data['user_id']
    })
    
    
    

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BACKEND = "https://c17cec26e2744fd97428a693a546c2c5.serveo.net"

# Инициализация Telegram бота
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Привет! Я бот, работающий вместе с Flask!")

async def run_bot():
    await dp.start_polling(bot)

def run_flask():
    app.run(host='127.0.0.1', port=4444)

if __name__ == '__main__':
    # Создаем и запускаем поток для Flask
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    
    # Запускаем бота в основном потоке
    asyncio.run(run_bot())