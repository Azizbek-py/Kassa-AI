import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters
)
from settings import *
from details.handlers import start, text, photo, handle_album



app = Application.builder().token(BOT_TOKEN).build()



app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(~filters.COMMAND & ~filters.PHOTO, text))
app.add_handler(MessageHandler(filters.PHOTO, photo))

if __name__ == "__main__":
    print("Pooling ishlayapti...")
    app.run_polling(
    drop_pending_updates=True,
    )