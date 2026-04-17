import os
import asyncio
import random
import logging
from functools import lru_cache
from re import finditer
from math import gcd, sqrt
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Загружаем токен из .env файла
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==================== АЛГОРИТМ ШИФРОВАНИЯ ====================
alf = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я']
num = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33']

@lru_cache(None)
def nom(b):
    for i in range(len(alf)):
        if b == alf[i]:
            return num[i]
    return None

@lru_cache(None)
def denom(code):
    for i in range(len(num)):
        if code == num[i]:
            return alf[i]
    return None

@lru_cache(None)
def shif_c(s):
    result = ''
    for bu in s:
        idx = alf.index(bu)
        new_idx = (idx + 5) % 33
        result += alf[new_idx]
    return result

@lru_cache(None)
def de_shif_c(s):
    result = ''
    for bu in s:
        idx = alf.index(bu)
        new_idx = (idx - 5) % 33
        result += alf[new_idx]
    return result

def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

def mx_pr(number):
    for i in range(number, 1, -1):
        if is_prime(i):
            return i
    return 2

def get_e(fi):
    e_list = []
    for i in range(2, fi):
        if gcd(i, fi) == 1:
            e_list.append(i)
        if len(e_list) == 6:
            break
    return e_list[5] if e_list else 3

def get_d(fi, eil):
    for d in range(1, 10**6):
        if (eil * d) % fi == 1:
            return d
    return None

def sh_RSA(st):
    p = mx_pr(random.randint(100, 1000))
    q = mx_pr(random.randint(100, 1000))
    while p == q:
        q = mx_pr(random.randint(100, 1000))

    n = p * q
    fi = (p - 1) * (q - 1)
    eil = get_e(fi)
    d = get_d(fi, eil)

    s = ''.join(nom(ch) for ch in st)
    blocks = [s[i:i+2] for i in range(0, len(s), 2)]

    encrypted = []
    block_size = len(str(n))
    for block in blocks:
        encrypted_block = pow(int(block), eil, n)
        encrypted.append(f"{encrypted_block:0{block_size}d}")

    return ''.join(encrypted), d, n

def de_RSA(st, d, n):
    block_size = len(str(n))
    blocks = [st[i:i+block_size] for i in range(0, len(st), block_size)]

    decrypted = []
    for block in blocks:
        dec_block = pow(int(block), d, n)
        decrypted.append(f"{dec_block:02d}")

    return ''.join(decrypted)

def shifr(s):
    return sh_RSA(shif_c(s))

def de_shifr(packet):
    encrypted_str, d, n = packet
    rsa_decrypted = de_RSA(encrypted_str, d, n)
    codes = [rsa_decrypted[i:i+2] for i in range(0, len(rsa_decrypted), 2)]
    cesar_encrypted = ''.join(denom(code) for code in codes)
    return de_shif_c(cesar_encrypted)

# ==================== TELEGRAM БОТ ====================
class CryptStates(StatesGroup):
    waiting_for_encrypt = State()
    waiting_for_decrypt = State()

main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔐 Зашифровать"), KeyboardButton(text="🔓 Расшифровать")],
        [KeyboardButton(text="❓ Помощь")]
    ],
    resize_keyboard=True
)

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "🔐 *Бот шифрования RSA + Цезарь*\n\n"
        "Я умею шифровать и расшифровывать сообщения "
        "комбинированным алгоритмом.\n\n"
        "Выберите действие на клавиатуре:"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_keyboard)

@dp.message(lambda msg: msg.text == "🔐 Зашифровать")
async def encrypt_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📝 Введите текст для шифрования (только русские буквы в нижнем регистре):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CryptStates.waiting_for_encrypt)

@dp.message(CryptStates.waiting_for_encrypt)
async def encrypt_process(message: types.Message, state: FSMContext):
    text = message.text.lower()

    if not all(ch in alf for ch in text if ch.isalpha()):
        await message.answer(
            "❌ Используйте только русские буквы!",
            reply_markup=main_keyboard
        )
        await state.clear()
        return

    try:
        encrypted_packet = shifr(text)
        response = (
            f"✅ *Зашифровано успешно!*\n\n"
            f"```\n{encrypted_packet}\n```\n\n"
            f"📋 Скопируйте этот пакет для расшифровки."
        )
        await message.answer(response, parse_mode="Markdown", reply_markup=main_keyboard)
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}", reply_markup=main_keyboard)

    await state.clear()

@dp.message(lambda msg: msg.text == "🔓 Расшифровать")
async def decrypt_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📋 Вставьте пакет для расшифровки (в формате ['строка', число, число]):",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CryptStates.waiting_for_decrypt)

@dp.message(CryptStates.waiting_for_decrypt)
async def decrypt_process(message: types.Message, state: FSMContext):
    try:
        packet = eval(message.text)
        decrypted = de_shifr(packet)
        await message.answer(
            f"✅ *Расшифровано:*\n\n`{decrypted}`",
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка: неверный формат пакета\n\n{e}",
            reply_markup=main_keyboard
        )

    await state.clear()

@dp.message(lambda msg: msg.text == "❓ Помощь")
async def help_command(message: types.Message):
    help_text = (
        "🔐 *Как пользоваться ботом*\n\n"
        "*Зашифровать:*\n"
        "1. Нажмите кнопку \"🔐 Зашифровать\"\n"
        "2. Введите текст на русском\n"
        "3. Получите пакет с зашифрованными данными\n\n"
        "*Расшифровать:*\n"
        "1. Нажмите \"🔓 Расшифровать\"\n"
        "2. Вставьте полученный ранее пакет\n"
        "3. Получите исходный текст\n\n"
        "⚠️ *Важно:* пакет должен быть точной копией того, что выдал бот при шифровании!"
    )
    await message.answer(help_text, parse_mode="Markdown")

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())