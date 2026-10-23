import os
import io
import math
import struct
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

load_dotenv()
load_dotenv("bot.env")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==================== ОРИГИНАЛЬНЫЙ АЛГОРИТМ ШИФРОВАНИЯ ТЕКСТА ====================
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
    while q_val == p_val:
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
    return ''

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
    s_s = str(s_sa[0])
    d_val = int(s_sa[1])
    n = int(s_sa[2])
    num_s = de_RSA(s_s, d_val, n)
    ch = []
    pp = '[0-9]{2}'
    for m in finditer(pp, num_s):
        decoded_char = denom(m.group())
        if decoded_char:
            ch.append(decoded_char)
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


# ==================== ШИФРОВАНИЕ И ДЕШИФРОВАНИЕ КАРТИНОК ====================

MAGIC_HEADER = b'GIRF'

def encrypt_image_to_cipher_image(raw_bytes: bytes) -> bytes:
    shift = 7
    p_val = mx_pr(random.randint(10**2, 10**3))
    q_val = mx_pr(random.randint(10**2, 10**3))
    while q_val == p_val:
        q_val = mx_pr(random.randint(10**2, 10**3))

    n_val = p_val * q_val
    fi = (p_val - 1) * (q_val - 1)
    eil = e(fi)
    d_val = d(fi)

    rng = random.Random(d_val ^ n_val ^ shift)

    encrypted_data = bytearray()
    for b in raw_bytes:
        gamma = rng.randint(0, 255)
        enc_b = (b + shift + gamma) % 256
        encrypted_data.append(enc_b)

    header = struct.pack('>4sIIQQ', MAGIC_HEADER, shift, len(raw_bytes), d_val, n_val)
    full_payload = header + bytes(encrypted_data)

    pad = (3 - len(full_payload) % 3) % 3
    full_payload += b'\x00' * pad
    total_pixels = len(full_payload) // 3

    width = math.isqrt(total_pixels) + 1
    height = (total_pixels + width - 1) // width

    extra_pad = (width * height * 3) - len(full_payload)
    if extra_pad > 0:
        full_payload += bytes([rng.randint(0, 255) for _ in range(extra_pad)])

    cipher_img = Image.frombytes('RGB', (width, height), full_payload)
    out_buf = io.BytesIO()
    cipher_img.save(out_buf, format='PNG')
    return out_buf.getvalue()


def decrypt_cipher_image_to_original(cipher_img_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(cipher_img_bytes))
    if img.mode != 'RGB':
        img = img.convert('RGB')
    raw_payload = img.tobytes()

    if len(raw_payload) < 28 or raw_payload[:4] != MAGIC_HEADER:
        raise ValueError("Файл не содержит корректного шифра ЖИРАФ.")

    magic, shift, orig_len, d_val, n_val = struct.unpack('>4sIIQQ', raw_payload[:28])
    encrypted_data = raw_payload[28:28 + orig_len]

    rng = random.Random(d_val ^ n_val ^ shift)

    decrypted_data = bytearray()
    for b in encrypted_data:
        gamma = rng.randint(0, 255)
        orig_b = (b - shift - gamma) % 256
        decrypted_data.append(orig_b)

    return bytes(decrypted_data)


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

# Сохранение форматирования и последних ключей шифрования
user_format_info = {}
user_last_keys = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "🔐 *Бот шифрования Ж.И.Р.А.Ф.*\n\n"
        "Я умею шифровать и расшифровывать текст и изображения оригинальным алгоритмом Цезарь + RSA.\n\n"
        "Выберите действие на клавиатуре:"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_keyboard)


# --- ТЕКСТ: ШИФРОВАНИЕ ---

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
        # Запоминаем сгенерированные d и n для удобства
        user_last_keys[user_id] = (packet[1], packet[2])

        packet_str = f"['{packet[0]}', {packet[1]}, {packet[2]}]"

        response = (
            f"✅ *Зашифровано успешно!*\n\n"
            f"```\n{packet_str}\n```\n\n"
            f"📋 *Нажмите на блок выше, чтобы скопировать весь пакет для расшифровки.*"
        )
        await message.answer(response, parse_mode="Markdown", reply_markup=main_keyboard)
    except Exception as e:
        await message.answer(f"❌ Ошибка при шифровании: {e}", reply_markup=main_keyboard)

    await state.clear()


# --- ТЕКСТ: РАСШИФРОВКА ---

@dp.message(F.text == "🔓 Расшифровать")
async def decrypt_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📋 Вставьте пакет для расшифровки:\n"
        "*(в формате `['строка_цифр', d, n]` либо просто скопированную строку цифр)*",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CryptStates.waiting_for_decrypt)

@dp.message(CryptStates.waiting_for_decrypt)
async def decrypt_process(message: types.Message, state: FSMContext):
    raw_text = message.text.strip().replace("```", "").replace("`", "")
    user_id = message.from_user.id
    packet = None

    try:
        # Вариант 1: передан полный пакет ['...', d, n]
        if raw_text.startswith("[") and raw_text.endswith("]"):
            packet = eval(raw_text)
        # Вариант 2: переданы только цифры шифра (как получилось у вас)
        elif raw_text.isdigit() or (raw_text.startswith("'") and raw_text.endswith("'")):
            clean_digits = "".join(ch for ch in raw_text if ch.isdigit())
            if user_id in user_last_keys:
                d_val, n_val = user_last_keys[user_id]
                packet = [clean_digits, d_val, n_val]
            else:
                await message.answer(
                    "❌ Вы отправили только строку цифр без ключей `d` и `n`.\n\n"
                    "Отправьте полный пакет в формате:\n`['строка_цифр', d, n]`",
                    parse_mode="Markdown",
                    reply_markup=main_keyboard
                )
                await state.clear()
                return
        else:
            # Попытка разобрать через eval на всякий случай
            parsed = eval(raw_text)
            if isinstance(parsed, (list, tuple)) and len(parsed) >= 3:
                packet = parsed

        if not packet or len(packet) < 3:
            raise ValueError("Неверный формат пакета.")

        char_info = user_format_info.get(user_id)
        decrypted = decrypt_packet(packet, char_info)

        if user_id in user_format_info:
            del user_format_info[user_id]

        await message.answer(f"✅ *Расшифровано:*\n\n`{decrypted}`", parse_mode="Markdown", reply_markup=main_keyboard)

    except Exception as e:
        await message.answer(
            f"❌ Ошибка при расшифровке: {e}\n\n"
            "Убедитесь, что отправляете пакет в формате:\n`['строка_цифр', d, n]`",
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )

    await state.clear()


# --- ИЗОБРАЖЕНИЕ: ШИФРОВАНИЕ ---

@dp.message(F.text == "🖼️ Зашифровать изображение")
async def img_encrypt_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📷 Отправьте фотографию для шифрования (как фото или файл):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CryptStates.waiting_for_image_encrypt)

@dp.message(CryptStates.waiting_for_image_encrypt, F.photo | F.document)
async def img_encrypt_process(message: types.Message, state: FSMContext):
    status_msg = await message.answer("⏳ Шифрование изображения...")

    try:
        file_id = message.photo[-1].file_id if message.photo else message.document.file_id
        file_info = await bot.get_file(file_id)
        downloaded = await bot.download_file(file_info.file_path)
        raw_bytes = downloaded.read()

        cipher_png_bytes = await asyncio.to_thread(encrypt_image_to_cipher_image, raw_bytes)

        await status_msg.delete()

        output_file = BufferedInputFile(cipher_png_bytes, filename="encrypted_image.png")
        caption_text = (
            "🔒 *Изображение зашифровано в картинку-шифр!*\n\n"
            "✨ *Как расшифровать обратно:*\n"
            "1. Нажмите «📥 Расшифровать изображение».\n"
            "2. Перешлите этот файл боту.\n\n"
            "Исходное фото восстановится в *100% оригинальном качестве*!"
        )
        await message.answer_document(
            document=output_file,
            caption=caption_text,
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )

    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка при шифровании: {e}", reply_markup=main_keyboard)

    await state.clear()


# --- ИЗОБРАЖЕНИЕ: РАСШИФРОВКА ---

@dp.message(F.text == "📥 Расшифровать изображение")
async def img_decrypt_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📥 *Отправьте зашифрованную картинку-файл:*\n\n"
        "💡 *Совет:* Просто **перешлите** полученное сообщение с файлом `encrypted_image.png` боту.",
        parse_mode="Markdown",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CryptStates.waiting_for_image_decrypt)

@dp.message(CryptStates.waiting_for_image_decrypt, F.document | F.photo)
async def img_decrypt_process(message: types.Message, state: FSMContext):
    status_msg = await message.answer("⏳ Расшифровываю изображение...")

    try:
        file_id = message.document.file_id if message.document else message.photo[-1].file_id
        file_info = await bot.get_file(file_id)
        downloaded = await bot.download_file(file_info.file_path)
        cipher_bytes = downloaded.read()

        orig_bytes = await asyncio.to_thread(decrypt_cipher_image_to_original, cipher_bytes)

        await status_msg.delete()
        restored_photo = BufferedInputFile(orig_bytes, filename="restored_image.jpg")
        await message.answer_photo(
            photo=restored_photo,
            caption="🔓 *Изображение успешно расшифровано в 100% качестве!*",
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )

    except ValueError:
        await status_msg.delete()
        await message.answer(
            "❌ *Не удалось расшифровать изображение!*\n\n"
            "📌 Отправьте зашифрованную картинку как **Файл / Документ** (без сжатия) "
            "или просто **перешлите** исходный файл от бота.",
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )
    except Exception as e:
        await status_msg.delete()
        await message.answer(f"❌ Ошибка расшифровки: {e}", reply_markup=main_keyboard)

    await state.clear()


@dp.message(F.text == "❓ Помощь")
async def help_command(message: types.Message):
    help_text = (
        "🔐 *Справка по боту Ж.И.Р.А.Ф.*\n\n"
        "• *Шифрование текста*: Введите русский текст, получите цифровой пакет.\n"
        "• *Расшифровка текста*: Отправьте пакет целиком либо только строку с цифрами.\n"
        "• *Шифрование картинок*: Отправьте фото — бот вернёт зашифрованный PNG-файл с шумом.\n"
        "• *Расшифровка картинок*: Нажмите «📥 Расшифровать изображение» и перешлите боту файл. Фото восстановится без потерь качества."
    )
    await message.answer(help_text, parse_mode="Markdown", reply_markup=main_keyboard)


async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот запущен...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
