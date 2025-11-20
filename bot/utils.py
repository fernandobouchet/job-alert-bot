import asyncio
import re
from telegram import constants, InlineKeyboardMarkup, InlineKeyboardButton


async def send_jobs(bot, channel_id, jobs):
    for job in jobs:
        # Obtener roles y tags
        score_details = job.get("score_details", {})
        roles_list = score_details.get("roles", [])
        tags_list = score_details.get("tags", [])

        # Formatear para mostrar
        roles_display = ", ".join(roles_list) if roles_list else "No especificado"
        tags_display = ", ".join(tags_list) if tags_list else "No especificado"

        text = (
            f"🌐 Fuente: <b>{clean_text(job.get('source', 'N/A'))}</b>\n"
            f"💼 <b>{clean_text(job.get('title', 'N/A'))}</b>\n"
            f"🧭 Modalidad: {clean_text(job.get('modality', 'N/A'))}\n"
            f"🏢 Empresa: {clean_text(job.get('company', 'N/A'))}\n"
            f"✨ Roles: <code>{roles_display}</code>\n"
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
