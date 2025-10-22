import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot as TelegramBot
from sources.getonboard_fetcher import fetch_getonboard
from sources.educacionit_fetcher import fetch_educacionit
from sources.jobspy_fetcher import fetch_jobspy
from utils import scrape

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

SOURCES = [fetch_educacionit, fetch_getonboard, fetch_jobspy]


def main():
    if not CHANNEL_ID:
        print(
            "⚠️ No se encontró el ID del canal en la variable de entorno TELEGRAM_CHANNEL_ID. El bot no podrá enviar notificaciones."
        )

    bot = TelegramBot(BOT_TOKEN)
    asyncio.run(scrape(SOURCES, CHANNEL_ID, bot))


if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
