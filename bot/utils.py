import asyncio
import re
import html
from telegram import constants, InlineKeyboardMarkup, InlineKeyboardButton


# Pre-compile regex patterns for performance
_REGEX_HTML_TAGS = re.compile(r"<[^>]+>")
_REGEX_WHITESPACE = re.compile(r"\s+")

MODALITY_EMOJIS = {
    "Remoto": "🏠",
    "Presencial": "🏢",
    "Híbrido": "🌓",
}


async def send_jobs(bot, channel_id, jobs):
    for job in jobs:
        # Obtener roles y tags
        score_details = job.get("score_details", {})
        roles_list = score_details.get("roles", [])
        tags_list = score_details.get("tags", [])

        # Formatear para mostrar
        roles_display = ", ".join(roles_list) if roles_list else "No especificado"
        tags_display = ", ".join(tags_list) if tags_list else "No especificado"

        published_at = job.get("published_at")
        date_str = ""
        if hasattr(published_at, "strftime"):
            date_str = f"📅 Publicado: {published_at.strftime('%d/%m/%Y')}\n"
        elif isinstance(published_at, str):
            date_str = f"📅 Publicado: {html.escape(clean_text(published_at))}\n"

        modality = clean_text(job.get("modality", "N/A"))
        modality_emoji = MODALITY_EMOJIS.get(modality, "🧭")

        text = (
            f"🌐 Fuente: <b>{html.escape(clean_text(job.get('source', 'N/A')))}</b>\n"
            f"💼 <b>{html.escape(clean_text(job.get('title', 'N/A')))}</b>\n"
            f"{modality_emoji} Modalidad: {html.escape(modality)}\n"
            f"🏢 Empresa: {html.escape(clean_text(job.get('company', 'N/A')))}\n"
            f"{date_str}"
            f"✨ Roles: <code>{html.escape(roles_display)}</code>\n"
            f"🏷️ Tags: <code>{html.escape(tags_display)}</code>\n"
        )

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text=f"🚀 Aplicar en {clean_text(job.get('source', 'N/A'))}",
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
    # Use pre-compiled regex patterns
    text = _REGEX_HTML_TAGS.sub("", text)
    text = _REGEX_WHITESPACE.sub(" ", text).strip()
    return text
