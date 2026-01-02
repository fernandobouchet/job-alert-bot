
import asyncio
from unittest.mock import AsyncMock
import pandas as pd
import re
from telegram import constants, InlineKeyboardMarkup, InlineKeyboardButton

# Copying clean_text here to be self-contained or I can import it
def clean_text(text):
    """Elimina HTML y exceso de espacios."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

# Modified send_jobs to just print text instead of sending
async def print_jobs(jobs):
    for job in jobs:
        # Obtener roles y tags
        score_details = job.get("score_details", {})
        roles_list = score_details.get("roles", [])
        tags_list = score_details.get("tags", [])

        # Formatear para mostrar
        roles_display = ", ".join(roles_list) if roles_list else "No especificado"
        tags_display = ", ".join(tags_list) if tags_list else "No especificado"

        # PROPOSED CHANGE HERE (commented out to see "before" state first, or I can implement it in the file directly)
        # But this script is to VERIFY the change after I apply it to the real file.
        # So I will Import send_jobs from bot.utils
        pass

from bot.utils import send_jobs

async def test():
    # Mock bot
    bot = AsyncMock()
    async def print_msg(chat_id, text, parse_mode, disable_web_page_preview, reply_markup):
        print(f"--- MSG to {chat_id} ---")
        print(text)
        print("-----------------------")

    bot.send_message = print_msg

    # Create sample job
    job = {
        "source": "Test Source",
        "title": "Senior Python Developer",
        "modality": "Remote",
        "company": "Tech Corp",
        "score_details": {"roles": ["Backend"], "tags": ["Python", "Django"]},
        "published_at": pd.Timestamp("2023-10-27 10:00:00")
    }

    print("Testing send_jobs...")
    try:
        await send_jobs(bot, "123", [job])
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test())
