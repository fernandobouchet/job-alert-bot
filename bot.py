import os
import asyncio
from dotenv import load_dotenv
from sources.jobspy import fetch_jobspy
from telegram import Bot, constants
from sources.getonboard import fetch_getonboard
from sources.educacionit import fetch_educacionit
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
            f"💼 <b>{clean_text(job['title'])}</b>\n"
            f"🏢 {clean_text(job['company'])}\n"
            f"🏅 {clean_text(job['seniority'])}\n"
            f"💰 {clean_text(job['salary'])}\n"
            f"📝 {clean_text(job['description'])[:200]}...\n"
            f"🔗 <a href='{clean_text(job['url'])}'>Link</a>"
        )
        try:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode=constants.ParseMode.HTML)
        except Exception as e:
            print(f"No se pudo enviar '{job['title']}': {e}")

async def run_bot():
    all_jobs = []
    for source_func in SOURCES:
        jobs = source_func()
        all_jobs.extend(jobs)
        
    recent_jobs = filter_last_24h(all_jobs)
    update_json(recent_jobs)
    await send_jobs(bot, CHAT_ID, recent_jobs)

if __name__ == "__main__":
    asyncio.run(run_bot())
