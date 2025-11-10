import asyncio
import re
from telegram import constants, InlineKeyboardMarkup, InlineKeyboardButton


async def send_jobs(bot, channel_id, jobs):
    for job in jobs:
        tags_dict = job.get("tags", {})
        tags_list = []
        if isinstance(tags_dict, dict):
            tags_list = [tag for tag_group in tags_dict.values() for tag in tag_group]

        tags_display = ", ".join(sorted(list(set(tags_list))))

        text = (
            f"🌐 Fuente: <b>{clean_text(job.get('source', 'N/A'))}</b>\n"
            f"💼 <b>{clean_text(job.get('title', 'N/A'))}</b>\n"
            f"🧭 Modalidad: {clean_text(job.get('modality', 'N/A'))}\n"
            f"🏢 Empresa: {clean_text(job.get('company', 'N/A'))}\n"
            f"🏷️ Tags: <code>{tags_display}</code>\n"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=f"Ver detalles en {clean_text(job.get('source', 'N/A'))}",
                        url=clean_text(job.get("url", "#")),
                    )
                ]
            ]
        )

        try:
            await bot.send_message(
                chat_id=channel_id,
                text=text,
                parse_mode=constants.ParseMode.HTML,
                disable_web_page_preview=True,
                reply_markup=keyboard,
            )
            await asyncio.sleep(1.0)
        except Exception as e:
            print(f"No se pudo enviar '{job['title']}' a {channel_id}: {e}")


def clean_text(text):
    """Elimina HTML y exceso de espacios."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
