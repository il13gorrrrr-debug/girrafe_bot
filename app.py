import os
import io
import base64
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    BufferedInputFile,
)

load_dotenv("bot.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Сдвиг для шифрования методом Цезаря / полиалфавитного шифра
SHIFT_KEY = 7


def encrypt_data(text: str, shift: int = SHIFT_KEY) -> str:
    """Алгоритм шифрования символов со сдвигом."""
    result = []
    for char in text:
        result.append(chr((ord(char) + shift) % 1114112))
    return "".join(result)


def decrypt_data(text: str, shift: int = SHIFT_KEY) -> str:
    """Алгоритм расшифровки со сдвигом."""
    result = []
    for char in text:
        result.append(chr((ord(char) - shift) % 1114112))
    return "".join(result)


class BotStates(StatesGroup):
    waiting_for_text_to_encrypt = State()
    waiting_for_text_to_decrypt = State()
    waiting_for_image_to_encrypt = State()
    waiting_for_image_to_decrypt = State()


def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🔒 Зашифровать текст"),
                KeyboardButton(text="🔓 Расшифровать текст"),
            ],
            [
                KeyboardButton(text="🖼️ Зашифровать изображение"),
                KeyboardButton(text="📥 Расшифровать изображение"),
            ],
        ],
        resize_keyboard=True,
    )


@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "👋 Привет! Выберите действие на клавиатуре ниже:",
        reply_markup=get_main_keyboard(),
    )


# --- ТЕКСТ: ШИФРОВАНИЕ И РАСШИФРОВКА ---


@dp.message(F.text == "🔒 Зашифровать текст")
async def start_encrypt_text(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_text_to_encrypt)
    await message.answer("Отправьте текст, который требуется зашифровать:")


@dp.message(BotStates.waiting_for_text_to_encrypt, F.text)
async def process_encrypt_text(message: types.Message, state: FSMContext):
    encrypted = encrypt_data(message.text)
    await message.answer(f"🔒 Зашифрованный текст:\n\n`{encrypted}`", parse_mode="Markdown")
    await state.clear()


@dp.message(F.text == "🔓 Расшифровать текст")
async def start_decrypt_text(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_text_to_decrypt)
    await message.answer("Отправьте текст для расшифровки:")


@dp.message(BotStates.waiting_for_text_to_decrypt, F.text)
async def process_decrypt_text(message: types.Message, state: FSMContext):
    try:
        decrypted = decrypt_data(message.text)
        await message.answer(f"🔓 Расшифрованный текст:\n\n{decrypted}")
    except Exception:
        await message.answer("❌ Произошла ошибка при расшифровке. Проверьте правильность строки.")
    await state.clear()


# --- ИЗОБРАЖЕНИЕ: ШИФРОВАНИЕ ---


@dp.message(F.text == "🖼️ Зашифровать изображение")
async def start_encrypt_image(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_image_to_encrypt)
    await message.answer("Отправьте фотографию (как фото или как файл):")


@dp.message(BotStates.waiting_for_image_to_encrypt, F.photo | F.document)
async def process_encrypt_image(message: types.Message, state: FSMContext):
    status_msg = await message.answer("⏳ Обработка и шифрование изображения...")

    # Скачивание файла
    if message.photo:
        file_id = message.photo[-1].file_id
    else:
        file_id = message.document.file_id

    file_info = await bot.get_file(file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    image_bytes = downloaded_file.read()

    # 1. Байты изображения переводятся в строку Base64
    b64_string = base64.b64encode(image_bytes).decode("utf-8")

    # 2. Строка шифруется тем же алгоритмом
    encrypted_string = encrypt_data(b64_string)

    # 3. Из-за размера результат упаковывается в текстовый файл
    file_bytes = encrypted_string.encode("utf-8")
    output_doc = BufferedInputFile(file_bytes, filename="encrypted_image.txt")

    await status_msg.delete()
    await message.answer_document(
        document=output_doc,
        caption="🔒 Изображение успешно зашифровано! Файл содержит шифротекст.",
        reply_markup=get_main_keyboard(),
    )
    await state.clear()


# --- ИЗОБРАЖЕНИЕ: РАСШИФРОВКА ---


@dp.message(F.text == "📥 Расшифровать изображение")
async def start_decrypt_image(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_image_to_decrypt)
    await message.answer(
        "Отправьте зашифрованный файл (.txt) или зашифрованный текст в сообщении:"
    )


@dp.message(BotStates.waiting_for_image_to_decrypt, F.document | F.text)
async def process_decrypt_image(message: types.Message, state: FSMContext):
    status_msg = await message.answer("⏳ Расшифровка изображения...")

    encrypted_content = ""
    if message.document:
        doc = await bot.get_file(message.document.file_id)
        downloaded = await bot.download_file(doc.file_path)
        encrypted_content = downloaded.read().decode("utf-8")
    elif message.text:
        encrypted_content = message.text.strip()

    try:
        # 1. Расшифровка строки
        decrypted_b64 = decrypt_data(encrypted_content)

        # 2. Декодирование из Base64 обратно в бинарные данные картинки
        img_bytes = base64.b64decode(decrypted_b64)

        # 3. Отправка пользователю восстановленной фотографии
        photo_file = BufferedInputFile(img_bytes, filename="decrypted_image.jpg")
        await status_msg.delete()
        await message.answer_photo(
            photo=photo_file,
            caption="🔓 Изображение успешно расшифровано!",
            reply_markup=get_main_keyboard(),
        )
    except Exception:
        await status_msg.delete()
        await message.answer(
            "❌ Не удалось расшифровать изображение. Убедитесь, что передан верный шифротекст/файл.",
            reply_markup=get_main_keyboard(),
        )

    await state.clear()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
