import functools
from json_handler import delete_jobs_by_ids
from utils import scrape
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


class Bot:
    def __init__(self, admin_user_id, admin_chat_id, chat_ids, sources):
        self.ADMIN_USER_ID = admin_user_id
        self.admin_chat_id = admin_chat_id
        self.chat_ids = chat_ids
        self.SOURCES = sources

        # Apply the admin_only decorator to the command handlers
        self.fetch_command = self.admin_only(self.fetch_command)
        self.delete_command = self.admin_only(self.delete_command)
        self.delete_prompt = self.admin_only(self.delete_prompt, is_callback=True)
        self.delete_confirm = self.admin_only(self.delete_confirm, is_callback=True)
        self.delete_cancel = self.admin_only(self.delete_cancel, is_callback=True)

    def admin_only(self, func, is_callback=False):
        @functools.wraps(func)
        async def wrapped(update, context, *args, **kwargs):
            if is_callback:
                user_id = update.callback_query.from_user.id
                if str(user_id) != self.ADMIN_USER_ID:
                    await context.bot.answer_callback_query(
                        update.callback_query.id,
                        "No tienes permiso para hacer esto.",
                        show_alert=True,
                    )
                    return
            else:
                user_id = update.message.from_user.id
                if str(user_id) != self.ADMIN_USER_ID:
                    await update.message.reply_text(
                        "No tienes permiso para usar este comando."
                    )
                    return
            return await func(update, context, *args, **kwargs)

        return wrapped

    async def fetch_command(self, update, context):
        await update.message.reply_text("🚀 Iniciando búsqueda de trabajos...")
        await scrape(self.SOURCES, self.chat_ids, context.bot, self.admin_chat_id)
        await update.message.reply_text("Búsqueda de trabajos completada.")

    async def delete_command(self, update, context):
        job_ids = context.args
        if not job_ids:
            await update.message.reply_text(
                "Por favor, proporciona los IDs de los trabajos a eliminar. Ejemplo: /delete id1 id2"
            )
            return

        deleted_count = delete_jobs_by_ids(job_ids)

        if deleted_count > 0:
            await update.message.reply_text(f"🗑️ {deleted_count} trabajos eliminados.")
        else:
            await update.message.reply_text(
                "No se encontraron trabajos con los IDs proporcionados."
            )

    async def delete_prompt(self, update, context):
        query = update.callback_query
        await query.answer()
        job_id = query.data.split("_")[-1]

        keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "✅ Sí, eliminar", callback_data=f"delete_confirm_{job_id}"
                    ),
                    InlineKeyboardButton(
                        "❌ No", callback_data=f"delete_cancel_{job_id}"
                    ),
                ]
            ]
        )
        await query.edit_message_text(
            text=f"❓ ¿Estás seguro de que quieres eliminar el job con ID: {job_id}?",
            reply_markup=keyboard,
        )

    async def delete_confirm(self, update, context):
        query = update.callback_query
        await query.answer()
        job_id = query.data.split("_")[-1]

        deleted_count = delete_jobs_by_ids([job_id])

        if deleted_count > 0:
            await query.edit_message_text(
                text=f"🗑️ Job con ID: {job_id} eliminado correctamente."
            )
        else:
            await query.edit_message_text(
                text=f"⚠️ No se pudo eliminar el job con ID: {job_id}. Puede que ya haya sido eliminado."
            )

    async def delete_cancel(self, update, context):
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(text="🚫 Eliminación cancelada.")