from datetime import datetime, timezone, timedelta
import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot, constants
from sources.getonboard_fetcher import fetch_getonboard
from sources.educacionit_fetcher import fetch_educacionit
from sources.jobspy_fetcher import fetch_jobspy
from utils import clean_text, extract_tags
from update_json import update_json
import pandas as pd


load_dotenv()

TELE_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
bot = Bot(TELE_TOKEN)

SOURCES = [fetch_educacionit, fetch_getonboard, fetch_jobspy]


async def send_jobs(bot, chat_id, jobs):
    for job in jobs:
        text = (
            f"💼 <b>{clean_text(job['title'])}</b>\n"
            f"--- \n"
            f"🏢 Empresa: {clean_text(job['company'])}\n"
            f"💰 Salario: {clean_text(job['salary'])}\n\n"
            f"🏢 Fuente: {clean_text(job['source'])}\n"
            f"📝 Descripción:\n"
            f"{clean_text(job['description'])[:200]}...\n\n"
            f"🔗 <a href='{clean_text(job['url'])}'>Ver detalles</a>"
        )
        try:
            await bot.send_message(
                chat_id=chat_id, text=text, parse_mode=constants.ParseMode.HTML
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

    # Crea una clave única para identificar trabajos duplicados entre fuentes.
    df["dedupe_key"] = (
        df["title"].str.lower().str.strip()
        + " "
        + df["company"].str.lower().str.strip()
    )
    df.drop_duplicates(subset=["dedupe_key"], inplace=True)
    df.drop(columns=["dedupe_key"], inplace=True)

    # 4️⃣ Normalizar fechas y filtrar últimos 24h
    FILTER_HOURS = 24
    cutoff = datetime.now(timezone.utc) - timedelta(hours=FILTER_HOURS)

    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")

    df = df[df["published_at"] >= cutoff].copy()

    if df.empty:
        print("No hay trabajos recientes o únicos para procesar.")
        return

    print(f"Total de jobs únicos y recientes: {len(df)}")

    # 5️⃣ Extraer tags (keywords) de título y descripción

    df["tags"] = df.apply(
        lambda row: extract_tags(row["title"], row["description"]), axis=1
    )

    current_time_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    df["date_scraped"] = current_time_iso

    # 6️⃣ Convertir a lista de dicts para enviar
    df["published_at"] = df["published_at"].dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    recent_jobs = df.to_dict(orient="records")

    # 7️⃣ Actualizar JSON con trabajos nuevos y enviar
    new_jobs = update_json(recent_jobs)

    if new_jobs:
        print(f"✅ Se encontraron {len(new_jobs)} jobs nuevos para enviar.")
        await send_jobs(bot, CHAT_ID, new_jobs)
    else:
        print("No hay jobs nuevos para enviar.")


if __name__ == "__main__":
    asyncio.run(run_bot())
