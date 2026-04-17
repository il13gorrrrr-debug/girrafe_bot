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

# ==================== ТВОЙ РАБОЧИЙ АЛГОРИТМ ШИФРОВАНИЯ ====================
RUSSIAN_LOWERCASE = 'абвгдеёжзийклмнопрстуфхцчшщъыьэюя'
alf = ['а', 'б', 'в', 'г', 'д', 'е', 'ё', 'ж', 'з', 'и', 'й', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у', 'ф', 'х', 'ц', 'ч', 'ш', 'щ', 'ъ', 'ы', 'ь', 'э', 'ю', 'я']
num = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31', '32', '33']

# Словарь для перевода заглавных букв в строчные
upper_to_lower = {
    'А': 'а', 'Б': 'б', 'В': 'в', 'Г': 'г', 'Д': 'д', 'Е': 'е', 'Ё': 'ё',
    'Ж': 'ж', 'З': 'з', 'И': 'и', 'Й': 'й', 'К': 'к', 'Л': 'л', 'М': 'м',
    'Н': 'н', 'О': 'о', 'П': 'п', 'Р': 'р', 'С': 'с', 'Т': 'т', 'У': 'у',
    'Ф': 'ф', 'Х': 'х', 'Ц': 'ц', 'Ч': 'ч', 'Ш': 'ш', 'Щ': 'щ', 'Ъ': 'ъ',
    'Ы': 'ы', 'Ь': 'ь', 'Э': 'э', 'Ю': 'ю', 'Я': 'я'
}
# Обратный словарь для восстановления заглавных букв
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

@lru_cache(None)
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

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ БОТА ====================

def normalize_text(text):
    """
    Приводит текст к нижнему регистру для шифрования,
    но сохраняет информацию о том, где были заглавные буквы и не-буквы.
    """
    lower_text = ''
    char_info = []  # список: {'type': 'upper'/'lower'/'other', 'char': буква}

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
    """
    Восстанавливает оригинальный регистр и не-буквы.
    """
    result = ''
    letter_index = 0  # индекс для отслеживания расшифрованных БУКВ

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
            # Не-буква (пробел, знак препинания, цифра)
            result += item['char']

    # Добавляем оставшиеся буквы, если есть (на всякий случай)
    if letter_index < len(decrypted_lower):
        result += decrypted_lower[letter_index:]

    return result

def encrypt_text(text):
    """
    Шифрует текст, обрабатывая его целиком (с пробелами и заглавными буквами).
    Возвращает пакет и информацию о форматировании.
    """
    # Нормализуем текст
    lower_text, char_info = normalize_text(text)

    # Шифруем нормализованный текст
    packet = shifr(lower_text)

    return packet, char_info

def decrypt_packet(packet, char_info=None):
    """
    Расшифровывает пакет. Если передана char_info, восстанавливает регистр и не-буквы.
    """
    # Расшифровываем
    decrypted_lower = de_shifr(packet)

    # Если есть информация о форматировании, восстанавливаем
    if char_info:
        return restore_text(decrypted_lower, char_info)
    else:
        return decrypted_lower

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

# Хранилище для сохранения информации о форматировании
user_format_info = {}

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        "🔐 *Бот шифрования Ж.И.Р.А.Ф.\n\n"
        "Я умею шифровать и расшифровывать сообщения комбинированным алгоритмом.\n\n"
        "✨ *Возможности:*\n"
        "• Поддержка заглавных и строчных букв\n"
        "• Поддержка пробелов и знаков препинания\n"
        "• Шифрование целых предложений\n\n"
        "Выберите действие на клавиатуре:"
    )
    await message.answer(welcome_text, parse_mode="Markdown", reply_markup=main_keyboard)

@dp.message(lambda msg: msg.text == "🔐 Зашифровать")
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

    # Проверяем, есть ли русские буквы
    has_russian = any(
        ch in alf or ch in upper_to_lower
        for ch in text
    )

    if not has_russian:
        await message.answer(
            "❌ Текст должен содержать русские буквы!",
            reply_markup=main_keyboard
        )
        await state.clear()
        return

    try:
        packet, char_info = encrypt_text(text)

        # Сохраняем информацию о форматировании
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

@dp.message(lambda msg: msg.text == "🔓 Расшифровать")
async def decrypt_start(message: types.Message, state: FSMContext):
    await message.answer(
        "📋 Вставьте пакет для расшифровки:\n"
        "*(в формате ['зашифрованная_строка', d, n])*",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CryptStates.waiting_for_decrypt)

@dp.message(CryptStates.waiting_for_decrypt)
async def decrypt_process(message: types.Message, state: FSMContext):
    try:
        packet = eval(message.text)

        # Пробуем получить сохранённую информацию о форматировании
        user_id = message.from_user.id
        char_info = user_format_info.get(user_id)

        decrypted = decrypt_packet(packet, char_info)

        # Очищаем сохранённую информацию после использования
        if user_id in user_format_info:
            del user_format_info[user_id]

        await message.answer(
            f"✅ *Расшифровано:*\n\n`{decrypted}`",
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )
    except SyntaxError:
        await message.answer(
            "❌ *Неверный формат пакета!*\n\n"
            "Пакет должен быть в формате:\n"
            "`['строка', число, число]`",
            parse_mode="Markdown",
            reply_markup=main_keyboard
        )
    except Exception as e:
        await message.answer(
            f"❌ Ошибка при расшифровке: {e}",
            reply_markup=main_keyboard
        )

    await state.clear()

@dp.message(lambda msg: msg.text == "❓ Помощь")
async def help_command(message: types.Message):
    help_text = (
        "🔐 *Как пользоваться ботом*\n\n"
        "*Зашифровать:*\n"
        "1. Нажмите кнопку \"🔐 Зашифровать\"\n"
        "2. Введите текст (можно с заглавными буквами, пробелами, знаками)\n"
        "3. Получите пакет с зашифрованными данными\n\n"
        "*Расшифровать:*\n"
        "1. Нажмите \"🔓 Расшифровать\"\n"
        "2. Вставьте полученный ранее пакет\n"
        "3. Получите исходный текст с сохранением регистра и знаков\n\n"
        "⚠️ *Важно:* Пакет должен быть точной копией того, что выдал бот при шифровании!\n\n"
        "💡 *Совет:* Если расшифровываете пакет от другого пользователя, "
        "регистр и знаки препинания могут не восстановиться полностью."
    )
    await message.answer(help_text, parse_mode="Markdown", reply_markup=main_keyboard)

async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
