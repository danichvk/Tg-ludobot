import os
import random
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    logging.error("TELEGRAM_TOKEN не найден!")
    raise ValueError("Нет токена")

GAMES = {
    "dice": {"name": "🎲 Кости", "range": (1, 6)},
    "basketball": {"name": "🏀 Баскетбол", "range": (1, 10)},
    "football": {"name": "⚽ Футбол", "range": (0, 5)},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🎲 Кости", callback_data="dice")],
        [InlineKeyboardButton("🏀 Баскетбол", callback_data="basketball")],
        [InlineKeyboardButton("⚽ Футбол", callback_data="football")],
    ]
    await update.message.reply_text(
        "🎮 *Игровой бот*\nВыбери игру:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    game = query.data
    if game not in GAMES:
        await query.edit_message_text("❌ Неизвестная игра")
        return
    
    user_score = random.randint(*GAMES[game]["range"])
    bot_score = random.randint(*GAMES[game]["range"])
    
    if user_score > bot_score:
        result = "🎉 Ты победил!"
    elif user_score < bot_score:
        result = "🤖 Бот победил!"
    else:
        result = "🤝 Ничья!"
    
    text = (
        f"{GAMES[game]['name']}\n\n"
        f"👤 Ты: {user_score}\n"
        f"🤖 Бот: {bot_score}\n\n"
        f"{result}\n\n"
        f"Нажми /start чтобы сыграть снова"
    )
    await query.edit_message_text(text)

async def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(play))
    
    logging.info("Запускаем бота...")
    await app.initialize()
    await app.start()
    
    # Простой polling без вебхуков (так проще для Render)
    await app.updater.start_polling()
    logging.info("Бот успешно запущен!")
    
    # Держим процесс живым
    await asyncio.Event().wait()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
