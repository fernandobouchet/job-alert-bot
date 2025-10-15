import os
import sys
import asyncio
from dotenv import load_dotenv
from telegram import Bot as TelegramBot
from telegram.ext import Application, CommandHandler
from bot.bot import Bot
from sources.getonboard_fetcher import fetch_getonboard
from sources.educacionit_fetcher import fetch_educacionit
from sources.jobspy_fetcher import fetch_jobspy
from utils import scrape

load_dotenv()

TELE_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

SOURCES = [fetch_educacionit, fetch_getonboard, fetch_jobspy]

def main():
    if "--scraper" in sys.argv:
        bot = TelegramBot(TELE_TOKEN)
        asyncio.run(scrape(SOURCES, CHAT_ID, bot))
    else:
        bot_instance = Bot(admin_user_id=ADMIN_USER_ID, chat_id=CHAT_ID, sources=SOURCES)
        application = Application.builder().token(TELE_TOKEN).build()

        application.add_handler(CommandHandler("fetch", bot_instance.fetch_command))
        application.add_handler(CommandHandler("delete", bot_instance.delete_command))

        print("🤖 Bot iniciado. Escuchando comandos...")
        application.run_polling()

if __name__ == "__main__":
    main()