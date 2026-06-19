# support_bot/app.py
import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import asyncio

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("SUPPORT_BOT_TOKEN")  # токен для @AI_English_Support_bot
if not BOT_TOKEN:
    raise ValueError("SUPPORT_BOT_TOKEN не задан")

ADMIN_ID = int(os.getenv("ADMIN_ID", 123456789))  # ваш ID

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Состояние для ожидания сообщения от пользователя (необязательно)
class SupportStates(StatesGroup):
    waiting_for_message = State()

@dp.message(Command("start"))
async def support_start(message: Message):
    user_id = message.from_user.id
    text = (
        "<b>Доброго времени суток!</b>\n\n"
        "Вы обратились в поддержку <b>AI English US</b>.\n\n"
        "🕒 <b>Время работы:</b> пн-пт 8:00 – 17:00 (по МСК)\n\n"
        "В сообщении <b>детально укажите</b>, в чём возникла проблема или вопрос.\n"
        "По возможности, прикрепите скриншоты.\n\n"
        "Свяжемся с вами как можно быстрее!\n\n"
    )
    # Кнопка для отмены (опционально)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_support")]
    ])
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    # Сохраняем состояние, чтобы знать, что пользователь начал диалог
    # но можно просто пересылать любые сообщения после /start

@dp.message()
async def handle_user_message(message: Message, state: FSMContext):
    # Пересылаем сообщение администратору
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    full_name = message.from_user.full_name or ""

    # Формируем текст для администратора
    forward_text = (
        f"📩 <b>Новое сообщение от пользователя</b>\n"
        f"👤 <b>ID:</b> <code>{user_id}</code>\n"
        f"👤 <b>Имя:</b> {full_name}\n"
        f"👤 <b>Username:</b> @{username}\n\n"
        f"📝 <b>Текст сообщения:</b>\n{message.text}"
    )

    # Отправляем администратору
    await bot.send_message(ADMIN_ID, forward_text, parse_mode="HTML")

    # Отправляем пользователю подтверждение
    await message.answer(
        "✅ Ваше сообщение передано оператору.\n"
        "Мы ответим вам в ближайшее время (в рабочие часы)."
    )

    # Если есть фото/документы, также пересылаем их администратору
    if message.photo:
        # Пересылаем фото
        await bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=f"Фото от пользователя {user_id}")
        await message.answer("Фото получено. Передано оператору.")
    if message.document:
        await bot.send_document(ADMIN_ID, message.document.file_id, caption=f"Документ от пользователя {user_id}")
        await message.answer("Документ получен. Передано оператору.")

@dp.callback_query(lambda c: c.data == "cancel_support")
async def cancel_support(callback_query: types.CallbackQuery):
    await callback_query.message.edit_text("❌ Диалог с поддержкой завершён. Если понадобится помощь, снова нажмите /start")
    await callback_query.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())