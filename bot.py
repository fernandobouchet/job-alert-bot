import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot, constants
from sources.getonboard_fetcher import fetch_getonboard
from sources.educacionit_fetcher import fetch_educacionit
from sources.jobspy_fetcher import fetch_jobspy
from utils import clean_text, filter_last_24h
from update_json import update_json

load_dotenv()

TELE_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(TELE_TOKEN)

SOURCES = [fetch_getonboard, fetch_educacionit, fetch_jobspy]

async def send_jobs(bot, chat_id, jobs):
    for job in jobs:
        text = (
            f"💼 **{clean_text(job['title'])}**\n"
            f"--- \n"
            f"🏢 Empresa: {clean_text(job['company'])}\n"
            f"💰 Salario: {clean_text(job['salary'])}\n\n"
            f"📝 Descripción:\n"
            f"{clean_text(job['description'])[:200]}...\n\n"
            f"🔗 <a href='{clean_text(job['url'])}'>Ver detalles</a>"
        )
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode=constants.ParseMode.HTML)
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"No se pudo enviar '{job['title']}': {e}")

async def run_bot():
    tasks = [asyncio.to_thread(source_func) for source_func in SOURCES]
    results = await asyncio.gather(*tasks)

    all_jobs = [job for result in results for job in result]

    recent_jobs = filter_last_24h(all_jobs)
    new_jobs, _ = update_json(recent_jobs)

    if new_jobs:
        await send_jobs(bot, CHAT_ID, new_jobs)
    else:
        print("No hay jobs nuevos para enviar.")

if __name__ == "__main__":
    asyncio.run(run_bot())
