import threading, uvicorn, time, os
from fastapi import FastAPI
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackContext,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

TOKEN = os.environ['TOKEN']
BOT_OPTIONS = {'start': False}

MENU, INFO = range(2)

async def start(update: Update, context: CallbackContext) -> int:
    keyboard = [
        [InlineKeyboardButton("Start Trading!", web_app=WebAppInfo(url="https://www.exness.global/webterminal/"))],
        [InlineKeyboardButton("Learn More", callback_data="info")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Welcome to the Exness Telegram WebTerminal!\n\nTrade on the most popular trading platform right from Telegram.\n\nSelect MT4 or MT5, then sign in your Exness server and start trading.\n\nThis web-app is maintained by Exness and will have fast execution times, but first time logins could be slow depending on your selected server.", reply_markup=reply_markup
    )
    return MENU

# Button click handler
async def button(update: Update, context: CallbackContext) -> int:
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data == "info":
        keyboard = [
            [InlineKeyboardButton("Start Trading!", web_app=WebAppInfo(url="https://www.exness.global/webterminal/"))],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await send(user_id, "Ever want to trade signals without having to jump from app to app?\n\nOr perhaps trade while chatting with friends?\n\nHere you'll get access to the Exness MetaTrader from within Telegram!\n\n(This web-app is a wrapper around the Exness APIs and not affiliated with the Exness team.\n\nBut it is completely private, secure, and does not save your credentials or have any telemetry.)", reply_markup=reply_markup)
        return INFO
    else:
        await query.edit_message_text(text="Unknown option selected.")
        return MENU

# Cancel handler
async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

async def send(chat, msg, reply_markup):
    await Bot(TOKEN).sendMessage(chat_id=chat, text=msg, reply_markup=reply_markup)

# Main function to start the bot
def telegram_thread():
    application = (
        ApplicationBuilder()
        .token(TOKEN)
        .read_timeout(10)
        .write_timeout(10)
        .concurrent_updates(True)
        .build()
    )

    # ConversationHandler to handle the state machine
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MENU: [CallbackQueryHandler(button)],
            INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, cancel)],
        },
        fallbacks=[CommandHandler("start", start)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

# Start FastAPI server to run the program serverless on Render
def start_server():
    app = FastAPI()

    @app.get("/")
    def home():
        return {"Info": "A telegram wrapper for https://www.exness.global/webterminal/"}
    
    # Render tends to have multiple deployments running at the same time
    # Which can cause the program to crash if there are multiple bots requesting updates
    # A work-around, is to activate the bot manually after the deployment is successful
    @app.get("/start")
    def start():
        BOT_OPTIONS['start'] = True
        return {"Log": "Starting bot."}
    
    # Instantiate with uvicorn
    # Allows to run fastapi without using 'fastapi' CLI
    uvicorn.run(app, port=8080, host='0.0.0.0')
    
if __name__ == "__main__":
    # Run server as a thread so it doesn't block the Telegram loop
    server_thread = threading.Thread(target=start_server)

    # Set thread as daemon so it dies on main program exit
    server_thread.daemon = True
    server_thread.start()

    # Run if /start is requested
    while True:
        if BOT_OPTIONS['start']:            
            telegram_thread()
        # Cool down
        time.sleep(5)



