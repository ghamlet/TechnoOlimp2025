import asyncio
import logging
import json
import os
from datetime import datetime

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import WebAppInfo
from aiogram.filters import CommandStart
from aiogram.enums.parse_mode import ParseMode
from aiogram.enums.content_type import ContentType

from dotenv import load_dotenv
from pymongo import MongoClient
import pytz

from database import register_user

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(token=os.getenv("TELEGRAM_BOT_TOKEN"))
dp = Dispatcher()






@dp.message(CommandStart())
async def start(message: types.Message):
    # Регистрируем пользователя
    is_existing =  register_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name or ""
    )
    
    # Формируем URL с параметром в зависимости от статуса пользователя
    web_app_url = (f"https://sajt-dmtr317744.amvera.io"
                   f"?user_id={message.from_user.id}"
                   f"&existing={str(is_existing).lower()}")
    
    web_app = WebAppInfo(url=web_app_url)
    
    # Отправляем сообщение с кнопкой, открывающей Mini App
    await message.answer(
        "Добро пожаловать! Открываю приложение...",
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="Открыть приложение", web_app=web_app)]
            ],
            resize_keyboard=True
        )
    )



@dp.message(F.content_type == ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        print("Received data:", data)
        
        if data.get("type") == "registration":
            # Обработка регистрации без ответа, чтобы не закрывать Mini App
            response = {
                "type": "registration_success",
                "user_id": data["user_id"],
                "status": "success"
            }
            # Отправляем ответ в Mini App через WebApp
            await message.answer(
                text="Регистрация завершена",
                reply_markup=types.ReplyKeyboardMarkup(
                    keyboard=[[
                        types.KeyboardButton(
                            text="Открыть приложение",
                            web_app=WebAppInfo(url=f"https://sajt-dmtr317744.amvera.io?user_id={data['user_id']}&existing=true")
                        )
                    ]],
                    resize_keyboard=True
                )
            )
            
        elif data.get("type") == "action":
            # Обработка действий из главного меню
            action = data.get("action")
            user_id = data.get("user_id")
            
            if action == "test_prompts":
                response = {
                    "type": "test_prompts_data",
                    "data": "Данные для тестирования промтов"
                }
            elif action == "examples":
                response = {
                    "type": "examples_data",
                    "data": "Примеры промтов"
                }
            # ... другие действия
            
            await message.answer(json.dumps(response))
            
    except Exception as e:
        logging.error(f"Error processing web app data: {e}")
        await message.answer(json.dumps({"error": str(e)}))



async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)



def fetch_test_prompts():
   
    return "test_prompts"


if __name__ == "__main__":
    asyncio.run(main())


