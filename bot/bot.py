import functools
from json_handler import delete_jobs_by_ids
from utils import scrape

class Bot:
    def __init__(self, admin_user_id, chat_id, sources):
        self.ADMIN_USER_ID = admin_user_id
        self.CHAT_ID = chat_id
        self.SOURCES = sources

        # Apply the admin_only decorator to the command handlers
        self.fetch_command = self.admin_only(self.fetch_command)
        self.delete_command = self.admin_only(self.delete_command)

    def admin_only(self, func):
        @functools.wraps(func)
        async def wrapped(update, context, *args, **kwargs):
            user_id = update.message.from_user.id
            if str(user_id) != self.ADMIN_USER_ID:
                await update.message.reply_text("No tienes permiso para usar este comando.")
                return
            return await func(update, context, *args, **kwargs)
        return wrapped

    async def fetch_command(self, update, context):
        await update.message.reply_text("🚀 Iniciando búsqueda de trabajos...")
        await scrape(self.SOURCES, self.CHAT_ID, context.bot)
        await update.message.reply_text("Búsqueda de trabajos completada.")

    async def delete_command(self, update, context):
        job_ids = context.args
        if not job_ids:
            await update.message.reply_text("Por favor, proporciona los IDs de los trabajos a eliminar. Ejemplo: /delete id1 id2")
            return

        deleted_count = delete_jobs_by_ids(job_ids)

        if deleted_count > 0:
            await update.message.reply_text(f"🗑️ {deleted_count} trabajos eliminados.")
        else:
            await update.message.reply_text("No se encontraron trabajos con los IDs proporcionados.")