import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiohttp import web
import pathlib

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
WEB_APP_URL = os.getenv('WEB_APP_URL', 'https://your-app.up.railway.app')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(commands=['start'])
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

# ---------- Веб-сервер для отдачи статических файлов (HTML, CSS, JS, PNG) ----------
async def handle_html(request):
    # Отдаём index.html
    return web.FileResponse('index.html')

async def handle_static(request):
    # Отдаём остальные файлы из корня (style.css, script.js, fem_logo.png)
    filename = request.match_info['filename']
    path = pathlib.Path(filename)
    if path.exists() and path.is_file():
        return web.FileResponse(filename)
    return web.Response(status=404)

async def on_startup(app):
    # Запускаем поллинг бота в фоне
    asyncio.create_task(dp.start_polling(bot))

def main():
    app = web.Application()
    app.router.add_get('/', handle_html)
    app.router.add_get('/{filename}', handle_static)
    app.on_startup.append(on_startup)
    port = int(os.environ.get('PORT', 8080))
    web.run_app(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()