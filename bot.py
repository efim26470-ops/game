import os
import asyncio
import pathlib
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo
from aiohttp import web

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in environment")

WEB_APP_URL = os.getenv('WEB_APP_URL')
if not WEB_APP_URL:
    railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    WEB_APP_URL = f"https://{railway_domain}" if railway_domain else "https://your-app.up.railway.app"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_command(message: types.Message):
    web_app_button = KeyboardButton(
        text="✨ Открыть игру ✨",
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    keyboard = ReplyKeyboardMarkup(keyboard=[[web_app_button]], resize_keyboard=True)
    await message.answer("Добро пожаловать в кликер ФЭМ!\nНажимай на логотип!", reply_markup=keyboard)

# --- Обработчики веб-сервера ---
async def handle_root(request):
    return web.FileResponse('index.html')

async def handle_index(request):
    return web.FileResponse('index.html')

async def handle_health(request):
    return web.Response(text="OK")

async def handle_static(request):
    filename = request.match_info['filename']
    if '..' in filename or filename.startswith('/'):
        return web.Response(status=403)
    p = pathlib.Path(filename)
    if p.exists() and p.is_file():
        return web.FileResponse(filename)
    return web.Response(status=404)

async def on_startup(app):
    # Выводим список файлов для отладки
    print("=== Files in /app ===")
    for f in pathlib.Path('.').iterdir():
        print(f"  {f.name}")
    print("=====================")
    asyncio.create_task(dp.start_polling(bot, drop_pending_updates=True))

def main():
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/index.html', handle_index)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/{filename}', handle_static)
    app.on_startup.append(on_startup)
    port = int(os.environ.get('PORT', 8080))
    print(f"Starting server on port {port}")
    web.run_app(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()