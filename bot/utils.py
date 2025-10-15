import asyncio
import re
from telegram import constants


async def send_jobs(bot, chat_id, jobs):
    for job in jobs:
        tags_display = ", ".join(job.get("tags", []))

        text = (
            f"💼 <b>{clean_text(job.get('title', 'N/A'))}</b> ({clean_text(job.get('modality', 'N/A'))})\n"
            f"--- \n"
            f"🏢 Empresa: {clean_text(job.get('company', 'N/A'))}\n"
            f"💰 Salario: {clean_text(job.get('salary', 'No especificado'))}\n"
            f"🏷️ Tags: <code>{tags_display}</code>\n\n"
            f"🆔 ID: <code>{job.get('id', 'N/A')}</code>\n"
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


def clean_text(text):
    """Elimina HTML y exceso de espacios."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
