import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
# Railway автоматически даст домен, но мы пропишем позже переменную окружения
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://your-app.up.railway.app')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message_handler(commands=['start'])
async def start_command(message: types.Message):
    web_app_button = KeyboardButton(
        text="✨ Открыть игру ✨",
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[web_app_button]],
        resize_keyboard=True
    )
    await message.answer(
        "Добро пожаловать в кликер факультета экономики и менеджмента!\n\n"
        "Нажимай на логотип ФЭМ, зарабатывай очки и становись лучшим!",
        reply_markup=keyboard
    )

async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())