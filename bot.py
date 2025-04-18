import asyncio
import logging
import json
import os
from datetime import datetime
import requests

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

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



WEB_APP_URL = "https://sajt-dmtr317744.amvera.io"


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
    web_app_url = (f"{WEB_APP_URL}"
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

    # keyboard = InlineKeyboardMarkup(inline_keyboard=[
    #     [InlineKeyboardButton(text="Открыть регистрацию", web_app=web_app)]
    # ])
    
    # await message.answer(
    #     "Добро пожаловать! Нажмите кнопку для регистрации:",
    #     reply_markup=keyboard
    # )


@dp.message(F.content_type == ContentType.WEB_APP_DATA)
async def handle_web_app_data(message: types.Message):
    try:
        data = json.loads(message.web_app_data.data)
        print(data)
        
        res = {
                    "type": "examples_data",
                    "data": "examples"
                }
        
            
    
        # await message.answer(json.dumps(data))

        # await message.answer(response, parse_mode=ParseMode.HTML)
        
    except Exception as e:
        await message.answer(f"Ошибка обработки данных: {str(e)}")




async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)





if __name__ == "__main__":
    asyncio.run(main())


