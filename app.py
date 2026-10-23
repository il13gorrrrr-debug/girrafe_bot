import os
import io
import asyncio
import random
import logging
from functools import lru_cache
from re import finditer
from math import gcd, sqrt
from dotenv import load_dotenv
from PIL import Image
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Загружаем токен из .env или bot.env
load_dotenv()
load_dotenv("bot.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==================== ОРИГИНАЛЬНЫЙ АЛГОРИТМ ШИФРОВАНИЯ (БЕЗ ИЗМЕНЕНИЙ) ====================
RUSSIAN_LOWERCASE = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
alf = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я']
num = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33']

upper_to_lower = {
    'А': 'а', 'Б': 'б', 'В': 'в', 'Г': 'г', 'Д': 'д', 'Е': 'е', 'Ё': 'ё',
    'Ж': 'ж', 'З': 'з', 'И': 'и', 'Й': 'й', 'К': 'к', 'Л': 'л', 'М': 'м',
    'Н': 'н', 'О': 'о', 'П': 'п', 'Р': 'р', 'С': 'с', 'Т': 'т', 'У': 'у',
    'Ф': 'ф', 'Х': 'х', 'Ц': 'ц', 'Ч': 'ч', 'Ш': 'ш', 'Щ': 'щ', 'Ъ': 'ъ',
    'Ы': 'ы', 'Ь': 'ь', 'Э': 'э', 'Ю': 'ю', 'Я': 'я'
}
lower_to_upper = {v: k for k, v in upper_to_lower.items()}

@lru_cache(None)
def nom(b):
    for i in range(len(alf)):
        if b == alf[i]:
            return num[i]

@lru_cache(None)
def nomer(stroka):
    s = ''
    for i in stroka:
        if i in alf:
            s += nom(i)
    return s

@lru_cache(None)
def shif_c(s):
    s_n = ''
    for bu in s:
        if bu in alf:
            nm = int(nom(bu))
            n_n = (nm - 5) % 33
            s_n += alf[n_n - 5]
        else:
            s_n += bu
    return s_n

@lru_cache(None)
def de_shif_c(s):
    s_nn = ''
    for bu in s:
        if bu in alf:
            nm = int(nom(bu))
            n_n = (nm + 4) % 33
            s_nn += alf[(n_n + 4) % 33]
        else:
            s_nn += bu
    return s_nn

@lru_cache(None)
def p(n):
    for i in range(2, int(sqrt(n) + 1)):
        if n % i == 0:
            return 0
    return n > 1

@lru_cache(None)
def e(fi):
    e_list = []
    for i in range(1, fi):
        if gcd(i, fi) == 1:
            e_list.append(i)
        if len(e_list) == 6:
            break
    return e_list[5]

@lru_cache(None)
def d(fi):
    eil = e(fi)
    for d_val in range(10**10):
        if (eil * d_val) % fi == 1:
            return d_val

@lru_cache(None)
def mx_pr(number):
    for i in range(number, 1, -1):
        if p(i):
            return i
    return 2

def sh_RSA(st):
    p_val = mx_pr(random.randint(10**2, 10**3))
    q_val = mx_pr(random.randint(10**2, 10**3))
    n = p_val * q_val
    fi = (p_val - 1) * (q_val - 1)
    eil = e(fi)
    den = d(fi)
    s = nomer(st)
    pat = '[0-9][0-9]'
    new_s = ''
    for i in finditer(pat, s):
        t = i.group()
        tt = str(pow(int(t), eil, n))
        if len(tt) < len(str(n)):
            tt = '0' * (len(str(n)) - len(tt)) + tt
        new_s += tt
    return [new_s, den, n]

def shifr(s):
    your_str_s_1 = shif_c(s)
    your_str_s_2 = sh_RSA(your_str_s_1)
    return your_str_s_2

def denom(co):
    for i in range(len(num)):
        if co == num[i]:
            return alf[i]

def de_RSA(st, d_val, n):
    c = len(str(n))
    pat = f'[0-9]{{{c}}}'
    res = ''
    for m in finditer(pat, st):
        t = int(m.group())
        de_t = pow(t, d_val, n)
        res += f"{de_t % 100:02d}"
    return res

def de_shifr(s_sa):
    s_s = s_sa[0]
    d_val = s_sa[1]
    n = s_sa[2]
    num_s = de_RSA(s_s, d_val, n)
    ch = []
    pp = '[0-9]{2}'
    for m in finditer(pp, num_s):
        ch.append(denom(m.group()))
    return de_shif_c(''.join(ch))

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ТЕКСТА ====================

def normalize_text(text):
    lower_text = ''
    char_info = []

    for ch in text:
        if ch in upper_to_lower:
            lower_text += upper_to_lower[ch]
            char_info.append({'type': 'upper', 'char': upper_to_lower[ch]})
        elif ch in alf:
            lower_text += ch
            char_info.append({'type': 'lower', 'char': ch})
        else:
            lower_text += ch
            char_info.append({'type': 'other', 'char': ch})

    return lower_text, char_info

def restore_text(decrypted_lower, char_info):
    result = ''
    letter_index = 0

    for item in char_info:
        if item['type'] == 'upper':
            if letter_index < len(decrypted_lower):
                char = decrypted_lower[letter_index]
                result += lower_to_upper.get(char, char)
                letter_index += 1
        elif item['type'] == 'lower':
            if letter_index < len(decrypted_lower):
                result += decrypted_lower[letter_index]
                letter_index += 1
        else:
            result += item['char']

    if letter_index < len(decrypted_lower):
        result += decrypted_lower[letter_index:]

    return result

def encrypt_text(text):
    lower_text, char_info = normalize_text(text)
    packet = shifr(lower_text)
    return packet, char_info

def decrypt_packet(packet, char_info=None):
    decrypted_lower = de_shifr(packet)
    if char_info:
        return restore_text(decrypted_lower, char_info)
    else:
        return decrypted_lower

# ==================== ОБРАБОТКА ИЗОБРАЖЕНИЙ ====================

BASE32_ALF = alf[:32]
CHUNK_SIZE = 3800  # Безопасный размер для сообщения в Telegram

def bytes_to_russian(data: bytes) -> str:
    bit_str = ''.join(f"{b:08b}" for b in data)
    padding = (5 - len(bit_str) % 5) % 5
    bit_str += '0' * padding
    chars = [BASE32_ALF[padding]]
    for i in range(0, len(bit_str), 5):
        val = int(bit_str[i:i+5], 2)
        chars.append(BASE32_ALF[val])
    return ''.join(chars)

def russian_to_bytes(text: str) -> bytes:
    padding = BASE32_ALF.index(text[0])
    bit_str = ''
    for ch in text[1:]:
        val = BASE32_ALF.index(ch)
        bit_str += f"{val:05b}"
    if padding > 0:
        bit_str = bit_str[:-padding]
    out = bytearray()
    for i in range(0, len(bit_str), 8):
        out.append(int(bit_str[i:i+8], 2))
    return bytes(out)

def prepare_quality_image(raw_bytes: bytes) -> bytes:
    """Масштабирует фото с сохранением чёткости (300x300, JPEG 75%)."""
    img = Image.open(io.BytesIO(raw_bytes))
    if img.mode != "RGB":
        img = img.convert("RGB")

    img.thumbnail((300, 300), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=75, optimize=True)
    return buf.getvalue()


# ==================== TELEGRAM БОТ ====================

class CryptStates(StatesGroup):
    waiting_for_encrypt = State()
    waiting_for_decrypt = State()
    waiting_for_image_encrypt = State()
    waiting_for_image_decrypt = State()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔐 Зашифровать"), KeyboardButton(text="🔓 Расшифровать")],
        [KeyboardButton(text="🖼️ Зашифровать изображение"), KeyboardButton(text="📥 Расшифровать изображение")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

user_format_info = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "🔐 *Бот шифрования Ж.И.Р.А.Ф.*\n\n"
        "Я умею шифровать и расшифровывать текст и изображения вашим алгоритмом (Цезарь + RSA).\n\n"
        "✨ *Возможности:*\n"
        "• Шифрование и расшифровка текста\n"
        "• Шифрование изображений в хорошем качестве с делением на части\n"
        "• Восстановление фотографий из сообщений\n\n"
        "Выберите действие на клавиатуре:"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_keyboard)


# --- ТЕКСТ ---

@dp.message(F.text == "🔐 Зашифровать")
async def encrypt_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📝 Введите текст для шифрования:\n"
        "*(можно использовать заглавные и строчные буквы, пробелы и знаки препинания)*",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CryptStates.waiting_for_encrypt)

@dp.message(CryptStates.waiting_for_encrypt)
async def encrypt_process(message: types.Message, state: FSMContext):
    text = message.text
    has_russian = any(ch in alf or ch in upper_to_lower for ch in text)

    if not has_russian:
        await message.answer("❌ Текст должен содержать русские буквы!", reply_markup=main_keyboard)
        await state.clear()
        return

    try:
        packet, char_info = encrypt_text(text)
        user_id = message.from_user.id
        user_format_info[user_id] = char_info

        response = (
            f"✅ *Зашифровано успешно!*\n\n"
            f"```\n{packet}\n```\n\n"
            f"📋 *Скопируйте этот пакет для расшифровки.*"
        )
        await message.answer(response, parse_mode="Markdown", reply_markup=main_keyboard)
    except Exception as e:
        await message.answer(f"❌ Ошибка при шифровании: {e}", reply_markup=main_keyboard)

    await state.clear()

@dp.message(F.text == "🔓 Расшифровать")
async def decrypt_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📋 Вставьте пакет для расшифровки:\n"
        "*(в формате ['зашифрованная_строка_из_цифр', d, n])*",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CryptStates.waiting_for_decrypt)

@dp.message(CryptStates.waiting_for_decrypt)
async def decrypt_process(message: types.Message, state: FSMContext):
    try:
        packet = eval(message.text)
        user_id = message.from_user.id
        char_info = user_format_info.get(user_id)

        decrypted = decrypt_packet(packet, char_info)

        if user_id in user_format_info:
            del user_format_info[user_id]

        await message.answer(
            f"✅ *Расшифровано:*\n\n`{decrypted}`",
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )
    except SyntaxError:
        await message.answer(
            "❌ *Неверный формат пакета!*\n\nПакет должен быть в формате:\n`['строка_цифр', число, число]`",
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка при расшифровке: {e}", reply_markup=main_keyboard)

    await state.clear()


# --- ИЗОБРАЖЕНИЕ: ШИФРОВАНИЕ ---

@dp.message(F.text == "🖼️ Зашифровать изображение")
async def img_encrypt_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📷 Отправьте фотографию для шифрования:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CryptStates.waiting_for_image_encrypt)

@dp.message(CryptStates.waiting_for_image_encrypt, F.photo | F.document)
async def img_encrypt_process(message: types.Message, state: FSMContext):
    status_msg = await message.answer("⏳ Обработка и шифрование изображения вашим алгоритмом...")

    try:
        if message.photo:
            file_id = message.photo[-1].file_id
        else:
            file_id = message.document.file_id

        file_info = await bot.get_file(file_id)
        downloaded = await bot.download_file(file_info.file_path)
        raw_bytes = downloaded.read()

        def do_work():
            compressed = prepare_quality_image(raw_bytes)
            rus_text = bytes_to_russian(compressed)
            return shifr(rus_text)

        packet = await asyncio.to_thread(do_work)
        cipher_digits = packet[0]
        d_val = packet[1]
        n_val = packet[2]

        await status_msg.delete()

        chunks = [cipher_digits[i:i + CHUNK_SIZE] for i in range(0, len(cipher_digits), CHUNK_SIZE)]
        total_parts = len(chunks)

        if total_parts == 1:
            await message.answer(
                f"✅ *Изображение зашифровано!*\n\n"
                f"```\n{packet}\n```\n\n"
                f"📋 *Нажмите на блок с кодом, чтобы скопировать его.*",
                parse_mode="Markdown",
                reply_markup=main_keyboard
            )
        else:
            await message.answer(
                f"✅ *Изображение зашифровано в высоком качестве!*\n\n"
                f"Шифр разбит на *{total_parts} сообщений* для сохранения детализации.\n"
                f"Ключи:\n"
                f"• `d` = `{d_val}`\n"
                f"• `n` = `{n_val}`\n\n"
                f"Ниже отправлены части шифра 👇",
                parse_mode="Markdown"
            )

            for idx, chunk in enumerate(chunks, 1):
                await message.answer(
                    f"📦 *Часть {idx} из {total_parts}:*\n\n"
                    f"`{chunk}`",
                    parse_mode="Markdown"
                )

            await message.answer(
                f"💡 *Инструкция для получателя:*\n"
                f"1. Нажмите кнопку «📥 Расшифровать изображение».\n"
                f"2. Перешлите или отправьте все {total_parts} сообщений с цифрами.\n"
                f"3. Затем отправьте сообщение с ключами: `{d_val} {n_val}` (два числа через пробел).",
                parse_mode="Markdown",
                reply_markup=main_keyboard
            )

    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка при шифровании изображения: {e}", reply_markup=main_keyboard)

    await state.clear()


# --- ИЗОБРАЖЕНИЕ: РАСШИФРОВКА ---

@dp.message(F.text == "📥 Расшифровать изображение")
async def img_decrypt_start(message: types.Message, state: FSMContext):
    await state.set_state(CryptStates.waiting_for_image_decrypt)
    await state.update_data(accumulated_cipher="")

    guide_text = (
        "📋 *Инструкция по расшифровке изображения:*\n\n"
        "🔹 *Если шифр разбит на несколько сообщений:*\n"
        "1. Отправьте сюда все сообщения с цифрами шифра по очереди.\n"
        "2. В конце отправьте ключи через пробел: `d n` (например: `250433 427099`) или команду `/done d n`.\n\n"
        "🔹 *Если шифр цельным пакетом:*\n"
        "Отправьте пакет целиком: `['строка_цифр', d, n]`.\n\n"
        "Жду данные для расшифровки..."
    )
    await message.answer(guide_text, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())


@dp.message(CryptStates.waiting_for_image_decrypt, F.text)
async def img_decrypt_process(message: types.Message, state: FSMContext):
    raw_text = message.text.strip()
    data = await state.get_data()
    acc_cipher = data.get("accumulated_cipher", "")

    # Проверка на цельный пакет: ['...', d, n]
    if raw_text.startswith("[") and raw_text.endswith("]"):
        try:
            packet = eval(raw_text)
            if isinstance(packet, (list, tuple)) and len(packet) == 3:
                await _perform_decrypt_and_send(message, str(packet[0]), int(packet[1]), int(packet[2]), state)
                return
        except Exception:
            pass

    # Проверка на строку ключей "d n" или "/done d n"
    parts = raw_text.replace("/done", "").strip().split()
    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
        d_val = int(parts[0])
        n_val = int(parts[1])
        if not acc_cipher:
            await message.answer("⚠️ Ключи получены, но цифры шифра ещё не были отправлены. Сначала отправьте сообщения с цифрами:")
            return
        await _perform_decrypt_and_send(message, acc_cipher, d_val, n_val, state)
        return

    # Накопление цифр
    clean_digits = "".join(ch for ch in raw_text if ch.isdigit())
    if clean_digits:
        acc_cipher += clean_digits
        await state.update_data(accumulated_cipher=acc_cipher)
        await message.answer(
            f"📥 Принята часть шифра (накоплено цифр: {len(acc_cipher)}).\n\n"
            f"Отправьте следующую часть ИЛИ пришлите ключи через пробел: `d n`, чтобы начать восстановление фото.",
            parse_mode="Markdown"
        )
    else:
        await message.answer(
            "⚠️ Сообщение не распознано. Отправьте цифры шифра или пару ключей `d n` через пробел.",
            parse_mode="Markdown"
        )


async def _perform_decrypt_and_send(message: types.Message, cipher_str: str, d_val: int, n_val: int, state: FSMContext):
    status_msg = await message.answer("⏳ Расшифровываю изображение алгоритмом RSA...")
    try:
        def do_restore():
            packet = [cipher_str, d_val, n_val]
            rus_text = de_shifr(packet)
            return russian_to_bytes(rus_text)

        img_bytes = await asyncio.to_thread(do_restore)
        photo_file = BufferedInputFile(img_bytes, filename="decrypted_hd.jpg")

        await status_msg.delete()
        await message.answer_photo(
            photo=photo_file,
            caption="🔓 Изображение успешно расшифровано в хорошем качестве!",
            reply_markup=main_keyboard
        )
        await state.clear()
    except Exception as e:
        await status_msg.delete()
        await message.answer(
            f"❌ Ошибка расшифровки: {e}\n\n"
            "Убедитесь, что все части шифра и значения d и n переданы верно.",
            reply_markup=main_keyboard
        )
        await state.clear()


@dp.message(F.text == "❓ Помощь")
async def help_command(message: types.Message):
    help_text = (
        "🔐 *Справка по боту Ж.И.Р.А.Ф.*\n\n"
        "• *Шифрование текста*: Нажмите «🔐 Зашифровать», введите русский текст, получите цифровой пакет.\n"
        "• *Шифрование картинок*: Нажмите «🖼️ Зашифровать изображение» и отправьте фото. Бот сохраняет чёткость и разбивает RSA-шифр на сообщения.\n"
        "• *Расшифровка картинок*: Нажмите «📥 Расшифровать изображение», отправьте сообщения с цифрами по очереди, затем введите ключи `d n` через пробел."
    )
    await message.answer(help_text, parse_mode="Markdown", reply_markup=main_keyboard)


async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
