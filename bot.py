import os
import asyncio
import pathlib
import logging
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, Command
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, WebAppInfo, Message
from aiohttp import web
import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

WEB_APP_URL = os.getenv('WEB_APP_URL')
if not WEB_APP_URL:
    railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
    WEB_APP_URL = f"https://{railway_domain}/index.html" if railway_domain else "https://your-app.up.railway.app/index.html"

# --- PostgreSQL ---
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    PGHOST = os.getenv('PGHOST')
    PGDATABASE = os.getenv('PGDATABASE')
    PGUSER = os.getenv('PGUSER')
    PGPASSWORD = os.getenv('PGPASSWORD')
    PGPORT = os.getenv('PGPORT', '5432')
    if all([PGHOST, PGDATABASE, PGUSER, PGPASSWORD]):
        DATABASE_URL = f"postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}"

if not DATABASE_URL:
    raise ValueError("No database connection string found")

db_pool = None

async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL)
    async with db_pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                score INTEGER DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        logger.info("Database initialized")

async def get_top_scores(limit=10):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch('''
            SELECT username, score FROM scores
            ORDER BY score DESC
            LIMIT $1
        ''', limit)
        return rows

async def update_score(user_id: int, username: str, score: int):
    async with db_pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO scores (user_id, username, score, updated_at)
            VALUES ($1, $2, $3, CURRENT_TIMESTAMP)
            ON CONFLICT (user_id) DO UPDATE
            SET score = EXCLUDED.score, username = EXCLUDED.username, updated_at = CURRENT_TIMESTAMP
        ''', user_id, username, score)

async def get_user_score(user_id: int):
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow('SELECT score FROM scores WHERE user_id = $1', user_id)
        return row['score'] if row else 0

# --- Бот ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or f"user_{user_id}"
    current_score = await get_user_score(user_id)
    web_app_button = KeyboardButton(
        text="✨ Открыть игру ✨",
        web_app=WebAppInfo(url=WEB_APP_URL)
    )
    keyboard = ReplyKeyboardMarkup(keyboard=[[web_app_button]], resize_keyboard=True)
    await message.answer(
        f"Добро пожаловать в кликер ФЭМ!\nТвой текущий счёт: {current_score}\nНажимай на логотип!",
        reply_markup=keyboard
    )

@dp.message(Command('top'))
async def top_command(message: Message):
    top = await get_top_scores()
    if not top:
        await message.answer("Пока нет ни одного игрока. Будь первым!")
        return
    text = "🏆 *Топ игроков* 🏆\n\n"
    for i, row in enumerate(top, 1):
        username = row['username'] or "Аноним"
        score = row['score']
        text += f"{i}. {username} — {score} 💥\n"
    await message.answer(text, parse_mode="Markdown")

# --- Веб-сервер ---
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

async def handle_score(request):
    try:
        data = await request.json()
        user_id = data.get('user_id')
        username = data.get('username')
        score = data.get('score')
        if user_id is None or score is None:
            return web.Response(status=400, text="Missing fields")
        await update_score(user_id, username, score)
        return web.Response(status=200, text="OK")
    except Exception as e:
        logger.error(f"Error updating score: {e}")
        return web.Response(status=500, text=str(e))

async def handle_get_score(request):
    user_id = request.query.get('user_id')
    if not user_id:
        return web.Response(status=400, text="Missing user_id")
    try:
        user_id = int(user_id)
        score = await get_user_score(user_id)
        return web.json_response({'score': score})
    except Exception as e:
        return web.Response(status=500, text=str(e))

async def handle_top(request):
    try:
        top = await get_top_scores(limit=10)
        top_list = [{'username': row['username'], 'score': row['score']} for row in top]
        return web.json_response({'top': top_list})
    except Exception as e:
        logger.error(f"Error fetching top: {e}")
        return web.json_response({'error': str(e)}, status=500)

async def start_bot():
    await init_db()
    await dp.start_polling(bot, drop_pending_updates=True)

async def on_startup(app):
    logger.info("=== Files in /app ===")
    for f in pathlib.Path('.').iterdir():
        logger.info(f"  {f.name}")
    logger.info("=====================")
    asyncio.create_task(start_bot())

def main():
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/index.html', handle_index)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/{filename}', handle_static)
    app.router.add_post('/api/score', handle_score)
    app.router.add_get('/api/score', handle_get_score)
    app.router.add_get('/api/top', handle_top)
    app.on_startup.append(on_startup)
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting server on port {port}")
    web.run_app(app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()