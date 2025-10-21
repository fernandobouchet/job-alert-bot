import os
import sys
import asyncio
from dotenv import load_dotenv
from telegram import Bot as TelegramBot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from bot.bot import Bot
from sources.getonboard_fetcher import fetch_getonboard
from sources.educacionit_fetcher import fetch_educacionit
from sources.jobspy_fetcher import fetch_jobspy
from utils import scrape

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")
PUBLIC_CHAT_ID = os.getenv("PUBLIC_CHAT_ID", None)

CHAT_IDS = [chat_id for chat_id in [ADMIN_CHAT_ID, PUBLIC_CHAT_ID] if chat_id]

SOURCES = [fetch_educacionit, fetch_getonboard, fetch_jobspy]


def main():
    if "--scraper" in sys.argv:
        bot = TelegramBot(BOT_TOKEN)
        asyncio.run(scrape(SOURCES, CHAT_IDS, bot, ADMIN_CHAT_ID))
    else:
        bot_instance = Bot(
            admin_user_id=ADMIN_USER_ID,
            admin_chat_id=ADMIN_CHAT_ID,
            chat_ids=CHAT_IDS,
            sources=SOURCES,
        )
        application = Application.builder().token(BOT_TOKEN).build()

        application.add_handler(CommandHandler("fetch", bot_instance.fetch_command))
        application.add_handler(CommandHandler("delete", bot_instance.delete_command))

        application.add_handler(
            CallbackQueryHandler(bot_instance.delete_prompt, pattern="^delete_prompt_")
        )
        application.add_handler(
            CallbackQueryHandler(
                bot_instance.delete_confirm, pattern="^delete_confirm_"
            )
        )
        application.add_handler(
            CallbackQueryHandler(bot_instance.delete_cancel, pattern="^delete_cancel_")
        )

        print("🤖 Bot iniciado. Escuchando comandos...")
        application.run_polling()


if __name__ == "__main__":
    main()
