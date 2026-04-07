import os
import asyncio
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from starlette.applications import Starlette
from starlette.responses import JSONResponse, PlainTextResponse
from starlette.routing import Route
import uvicorn

# --- НАСТРОЙКИ ---
TOKEN = os.environ["TELEGRAM_TOKEN"]  # Сюда Render подставит токен
PORT = int(os.getenv("PORT", 8000))
# Эту ссылку Render сам даст боту, ничего вписывать не надо
WEBHOOK_URL = os.environ["RENDER_EXTERNAL_URL"] + "/webhook"

logging.basicConfig(level=logging.INFO)

# --- ВСЯ ТВОЯ ЛОГИКА ИГР (она остается без изменений) ---
GAME_RULES = {
    "dice": {"emoji": "🎲", "range": (1, 6)},
    "basketball": {"emoji": "🏀", "range": (1, 10)},
    "football": {"emoji": "⚽", "range": (0, 5)},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 Кости", callback_data="game_dice"),
         InlineKeyboardButton("🏀 Баскетбол", callback_data="game_basketball")],
        [InlineKeyboardButton("🤖 С ботом", callback_data="mode_bot"),
         InlineKeyboardButton("👥 С другом", callback_data="mode_player")]
    ]
    await update.message.reply_text("Выбери игру:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("game_"):
        game = data.split("_")[1]
        context.user_data['game'] = game
        await query.edit_message_text(f"Игра {GAME_RULES[game]['emoji']}. Режим?")
    elif data == "mode_bot":
        game = context.user_data.get('game', 'dice')
        user_result = random.randint(*GAME_RULES[game]['range'])
        bot_result = random.randint(*GAME_RULES[game]['range'])
        winner = "Ты победил!" if user_result > bot_result else "Бот победил!"
        await query.edit_message_text(f"{GAME_RULES[game]['emoji']} Твой ход: {user_result}\nБот: {bot_result}\n{winner}")
    else:
        await query.edit_message_text("Игра с другом в разработке...")

# --- ЗАПУСК ВЕБ-СЕРВЕРА (вот это мы добавили) ---
telegram_app = None

async def start_bot():
    global telegram_app
    telegram_app = Application.builder().token(TOKEN).build()
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CallbackQueryHandler(handle_callback))
    await telegram_app.initialize()
    await telegram_app.start()
    # Говорим Telegram: "Все сообщения шли на этот адрес"
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook set to {WEBHOOK_URL}")

async def stop_bot():
    if telegram_app:
        await telegram_app.stop()
        await telegram_app.shutdown()

async def webhook(request):
    """Сюда Telegram будет присылать обновления"""
    if request.method == "POST":
        update = Update.de_json(await request.json(), telegram_app.bot)
        await telegram_app.process_update(update)
        return JSONResponse({"status": "ok"})
    return JSONResponse({"error": "Method not allowed"}, status_code=405)

async def healthcheck(request):
    """Просто чтобы Render не ругался, что порт молчит"""
    return PlainTextResponse("OK")

# Создаем веб-приложение Starlette
starlette_app = Starlette(routes=[
    Route("/webhook", webhook, methods=["POST"]),
    Route("/health", healthcheck, methods=["GET"]),
])

async def main():
    await start_bot()
    config = uvicorn.Config(starlette_app, host="0.0.0.0", port=PORT, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
