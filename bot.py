import os
import asyncpg
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

# ---------- Конфигурация ----------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
PUBLIC_DOMAIN = os.getenv("RAILWAY_PUBLIC_DOMAIN", "game-zhelezkin.up.railway.app")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"https://{PUBLIC_DOMAIN}{WEBHOOK_PATH}"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
db_pool = None

# ---------- База данных ----------
async def init_db():
    global db_pool
    db_pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                score INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT NOW()
            )
        """)
    print("✅ Database initialized")

async def get_user_score(user_id: int) -> int:
    async with db_pool.acquire() as conn:
        row = await conn.fetchrow("SELECT score FROM users WHERE user_id = $1", user_id)
        return row["score"] if row else 0

async def set_user_score(user_id: int, username: str, first_name: str, score: int):
    """Устанавливает точное значение счёта (для веб-приложения)"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username, first_name, score, last_updated)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (user_id) DO UPDATE
            SET score = EXCLUDED.score,
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_updated = NOW()
        """, user_id, username, first_name, score)

async def increment_user_score(user_id: int, username: str, first_name: str, delta: int):
    """Увеличивает счёт на delta (для команд бота)"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO users (user_id, username, first_name, score, last_updated)
            VALUES ($1, $2, $3, $4, NOW())
            ON CONFLICT (user_id) DO UPDATE
            SET score = users.score + $4,
                username = EXCLUDED.username,
                first_name = EXCLUDED.first_name,
                last_updated = NOW()
        """, user_id, username, first_name, delta)

async def get_top_users(limit: int = 10):
    async with db_pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT username, first_name, score
            FROM users
            ORDER BY score DESC
            LIMIT $1
        """, limit)
        return [{"username": r["username"] or "Anonymous", "first_name": r["first_name"], "score": r["score"]} for r in rows]

# ---------- Команды Telegram ----------
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Это кликер-игра для FEM.\n"
        "🔹 Нажми /click — заработай очко.\n"
        "🔹 /top — показать топ игроков.\n"
        "🔹 /profile — твой счёт.\n\n"
        "🎮 Также ты можешь играть через веб-приложение (кнопка ниже)."
    )

@dp.message(Command("click"))
async def cmd_click(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or ""
    await increment_user_score(user_id, username, first_name, 1)
    new_score = await get_user_score(user_id)
    await message.answer(f"➕ +1 очко! Теперь у тебя {new_score} очков.")

@dp.message(Command("profile"))
async def cmd_profile(message: types.Message):
    score = await get_user_score(message.from_user.id)
    await message.answer(f"📊 Твой счёт: {score} очков.")

@dp.message(Command("top"))
async def cmd_top(message: types.Message):
    top = await get_top_users(10)
    if not top:
        await message.answer("Пока ни одного игрока. Нажми /click, чтобы начать!")
        return
    text = "🏆 Топ-10 игроков:\n\n"
    for i, user in enumerate(top, 1):
        name = user["first_name"] or user["username"]
        text += f"{i}. {name} — {user['score']} очков\n"
    await message.answer(text)

# ---------- Веб-обработчики (статический сайт + API) ----------
async def handle_index(request):
    return web.FileResponse("index.html")

async def handle_script(request):
    return web.FileResponse("script.js")

async def handle_style(request):
    return web.FileResponse("style.css")

async def handle_logo(request):
    return web.FileResponse("fem_logo.png")

async def handle_api_top(request):
    top = await get_top_users(10)
    return web.json_response(top)

# === НОВЫЕ ОБРАБОТЧИКИ ДЛЯ ВЕБ-ПРИЛОЖЕНИЯ ===
async def handle_get_score(request):
    """GET /api/score?user_id=123 -> возвращает текущий счёт пользователя"""
    user_id_str = request.query.get('user_id')
    if not user_id_str:
        return web.json_response({'error': 'user_id required'}, status=400)
    try:
        user_id = int(user_id_str)
    except ValueError:
        return web.json_response({'error': 'invalid user_id'}, status=400)
    score = await get_user_score(user_id)
    return web.json_response({'score': score})

async def handle_post_score(request):
    """POST /api/score принимает {user_id, username, score} и сохраняет счёт"""
    try:
        data = await request.json()
    except:
        return web.json_response({'error': 'invalid json'}, status=400)
    
    user_id = data.get('user_id')
    username = data.get('username', '')
    score = data.get('score')
    if user_id is None or score is None:
        return web.json_response({'error': 'user_id and score required'}, status=400)
    try:
        user_id = int(user_id)
        score = int(score)
    except ValueError:
        return web.json_response({'error': 'user_id and score must be integers'}, status=400)
    
    # Используем first_name = username (у Telegram Web App нет отдельного имени)
    await set_user_score(user_id, username, username, score)
    return web.json_response({'success': True})

# ---------- Жизненный цикл ----------
async def on_startup(app: web.Application):
    await init_db()
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook set to {WEBHOOK_URL}")

async def on_shutdown(app: web.Application):
    await bot.delete_webhook()
    if db_pool:
        await db_pool.close()
    print("🛑 Shutdown complete")

def main():
    app = web.Application()
    
    # Статические файлы
    app.router.add_get("/", handle_index)
    app.router.add_get("/index.html", handle_index)
    app.router.add_get("/script.js", handle_script)
    app.router.add_get("/style.css", handle_style)
    app.router.add_get("/fem_logo.png", handle_logo)
    
    # API
    app.router.add_get("/api/top", handle_api_top)
    app.router.add_get("/api/score", handle_get_score)   # <-- новый
    app.router.add_post("/api/score", handle_post_score) # <-- новый
    
    # Webhook для Telegram
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)
    
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    port = int(os.getenv("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()