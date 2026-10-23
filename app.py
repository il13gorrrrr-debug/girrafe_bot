import os
import io
import base64
import asyncio
from dotenv import load_dotenv
from PIL import Image
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

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in bot.env file!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Сдвиг для шифрования
SHIFT_KEY = 7
# 2800 байт в Base64 дают ~3750 символов, что с запасом укладывается в лимит 4096 символов
MAX_RAW_BYTES = 2800


def compress_image_to_fit(image_bytes: bytes, max_bytes: int = MAX_RAW_BYTES) -> bytes:
    """
    Автоматически пропорционально сжимает разрешение и качество,
    чтобы результат помещался ровно в одно текстовое сообщение Telegram.
    """
    img = Image.open(io.BytesIO(image_bytes))

    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")

    quality = 65
    size = (180, 180)

    while True:
        img_copy = img.copy()
        img_copy.thumbnail(size, Image.Resampling.LANCZOS)

        buffer = io.BytesIO()
        img_copy.save(buffer, format="JPEG", quality=quality, optimize=True)
        compressed_bytes = buffer.getvalue()

        if len(compressed_bytes) <= max_bytes or size[0] <= 40 or quality <= 20:
            return compressed_bytes

        size = (int(size[0] * 0.85), int(size[1] * 0.85))
        quality = max(20, quality - 10)


def encrypt_data(text: str, shift: int = SHIFT_KEY) -> str:
    """Алгоритм шифрования со сдвигом символов."""
    result = []
    for char in text:
        result.append(chr((ord(char) + shift) % 1114112))
    return "".join(result)


def decrypt_data(text: str, shift: int = SHIFT_KEY) -> str:
    """Алгоритм расшифровки со сдвигом символов."""
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
        "👋 Привет! Я бот для шифрования и дешифрования текста и изображений.\n\n"
        "Выберите действие на клавиатуре ниже:",
        reply_markup=get_main_keyboard(),
    )


# --- ТЕКСТ ---


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
    await message.answer("Отправьте фотографию:")


@dp.message(BotStates.waiting_for_image_to_encrypt, F.photo | F.document)
async def process_encrypt_image(message: types.Message, state: FSMContext):
    status_msg = await message.answer("⏳ Сжатие и шифрование изображения...")

    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id

        file_info = await bot.get_file(file_id)
        downloaded = await bot.download_file(file_info.file_path)
        raw_bytes = downloaded.read()

        # 1. Автоматическое сжатие под лимит одного сообщения
        compressed_bytes = compress_image_to_fit(raw_bytes)

        # 2. Base64
        b64_string = base64.b64encode(compressed_bytes).decode("utf-8")

        # 3. Шифрование
        encrypted_string = encrypt_data(b64_string)

        await status_msg.delete()
        # Выводится ровно одним сообщением
        await message.answer(
            f"🔒 Зашифрованный шифротекст изображения (нажмите для копирования):\n\n`{encrypted_string}`",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(),
        )

    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка при шифровании: {e}", reply_markup=get_main_keyboard())

    await state.clear()


# --- ИЗОБРАЖЕНИЕ: РАСШИФРОВКА ---


@dp.message(F.text == "📥 Расшифровать изображение")
async def start_decrypt_image(message: types.Message, state: FSMContext):
    await state.set_state(BotStates.waiting_for_image_to_decrypt)
    await message.answer("Отправьте зашифрованный текст изображения одним сообщением:")


@dp.message(BotStates.waiting_for_image_to_decrypt, F.text)
async def process_decrypt_image(message: types.Message, state: FSMContext):
    status_msg = await message.answer("⏳ Расшифровка изображения...")

    try:
        cipher_text = message.text.strip()

        # 1. Снятие шифра
        decrypted_b64 = decrypt_data(cipher_text)

        # 2. Декодирование обратно в картинку
        img_bytes = base64.b64decode(decrypted_b64)

        # 3. Отправка пользователю
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
            "❌ Не удалось расшифровать изображение. Убедитесь, что передан верный шифротекст.",
            reply_markup=get_main_keyboard(),
        )

    await state.clear()


async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
