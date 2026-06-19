import os
import logging
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiohttp import web

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("SUPPORT_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("SUPPORT_BOT_TOKEN не задан")

ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

class SupportStates(StatesGroup):
    waiting_for_message = State()

@dp.message(Command("start"))
async def support_start(message: Message):
    text = (
        "<b>Доброго времени суток!</b>\n\n"
        "Вы обратились в поддержку <b>AI English US</b>.\n\n"
        "🕒 <b>Время работы:</b> пн-пт 10:00 – 18:00 (по МСК)\n\n"
        "В сообщении <b>детально укажите</b>, в чём возникла проблема или вопрос.\n"
        "По возможности, прикрепите скриншоты.\n\n"
        "Свяжемся с вами как можно быстрее!\n\n"
    )
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_support")]
    ])
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message()
async def handle_user_message(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    full_name = message.from_user.full_name or ""

    forward_text = (
        f"<b>Новое сообщение от пользователя</b>\n"
        f"👤 <b>ID:</b> <code>{user_id}</code>\n"
        f"👤 <b>Имя:</b> {full_name}\n"
        f"👤 <b>Username:</b> @{username}\n\n"
        f"<b>Текст сообщения:</b>\n{message.text}"
    )

    await bot.send_message(ADMIN_ID, forward_text, parse_mode="HTML")
    await message.answer(
        "✅ Ваше сообщение передано оператору.\n"
        "Мы ответим вам в ближайшее время (в рабочие часы)."
    )

    if message.photo:
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"Фото от пользователя {user_id}")
        await message.answer("Фото получено. Передано оператору.")
    if message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id, caption=f"Документ от пользователя {user_id}")
        await message.answer("Документ получен. Передано оператору.")

@dp.callback_query(lambda c: c.data == "cancel_support")
async def cancel_support(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("Диалог с поддержкой завершён. Если понадобится помощь, снова нажмите /start")
    await callback_query.answer()

# ---------- HTTP-сервер для Render ----------
async def health_check(request):
    return web.Response(text="OK", status=200)

async def start_web_server():
    app = web.Application()
    app.router.add_get('/health', health_check)
    port = int(os.environ.get('PORT', 10000))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    await site.start()
    logging.info(f"Health check server started on port {port}")
    await asyncio.Event().wait()

async def main():
    await asyncio.gather(
        dp.start_polling(bot),
        start_web_server()
    )

if __name__ == "__main__":
    asyncio.run(main())