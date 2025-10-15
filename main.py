import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot, constants
from sources.getonboard_fetcher import fetch_getonboard
from sources.educacionit_fetcher import fetch_educacionit
from sources.jobspy_fetcher import fetch_jobspy
from utils import clean_text, filter_jobs, updateDataFrame
from update_json import update_json
import pandas as pd


load_dotenv()

TELE_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(TELE_TOKEN)

SOURCES = [fetch_educacionit, fetch_getonboard, fetch_jobspy]


async def send_jobs(bot, chat_id, jobs):
    for job in jobs:
        tags_display = ", ".join(job.get("tags", []))

        text = (
            f"💼 <b>{clean_text(job.get('title', 'N/A'))}</b> ({clean_text(job.get('modality', 'N/A'))})\n"
            f"--- \n"
            f"🏢 Empresa: {clean_text(job.get('company', 'N/A'))}\n"
            f"💰 Salario: {clean_text(job.get('salary', 'No especificado'))}\n"
            f"🏷️ Tags: <code>{tags_display}</code>\n\n"
            f"🏢 Fuente: {clean_text(job.get('source', 'N/A'))}\n"
            f"📝 Descripción:\n"
            f"{clean_text(job.get('description', ''))[:200]}...\n\n"
            f"🔗 <a href='{clean_text(job.get('url', '#'))}'>Ver detalles</a>"
        )
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=constants.ParseMode.HTML,
                disable_web_page_preview=True,
            )
            await asyncio.sleep(1.0)
        except Exception as e:
            print(f"No se pudo enviar '{job['title']}': {e}")


async def run_bot():
    tasks = [asyncio.to_thread(source_func) for source_func in SOURCES]
    results = await asyncio.gather(*tasks)

    all_jobs = [job for result in results for job in result]

    if not all_jobs:
        print("No se obtuvieron trabajos de ninguna fuente.")
        return

    # Crear DataFrame
    df = pd.DataFrame(all_jobs)

    # Filtrar DataFrame
    df_filtered = filter_jobs(df)

    if df_filtered.empty:
        return

    # Actualizar DataFrame
    recent_jobs = updateDataFrame(df_filtered)

    if not recent_jobs:
        return

    # Actualizar JSON
    new_jobs = update_json(recent_jobs)

    if new_jobs:
        print(f"✅ Se encontraron {len(new_jobs)} jobs nuevos para enviar.")
        await send_jobs(bot, CHAT_ID, new_jobs)
    else:
        print("No hay jobs nuevos para enviar.")


if __name__ == "__main__":
    asyncio.run(run_bot())
