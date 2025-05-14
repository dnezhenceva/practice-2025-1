import os
import telebot
import requests
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

# Словари для перевода
ZODIAC_SIGNS = {
    'овен': 'aries',
    'телец': 'taurus',
    'близнецы': 'gemini',
    'рак': 'cancer',
    'лев': 'leo',
    'дева': 'virgo',
    'весы': 'libra',
    'скорпион': 'scorpio',
    'стрелец': 'sagittarius',
    'козерог': 'capricorn',
    'водолей': 'aquarius',
    'рыбы': 'pisces'
}

# Создание клавиатур
def main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Гороскоп"), KeyboardButton("Помощь"))
    return keyboard

def zodiac_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    buttons = [KeyboardButton(sign.capitalize()) for sign in ZODIAC_SIGNS.keys()]
    keyboard.add(*buttons)
    return keyboard

def day_keyboard():
    keyboard = ReplyKeyboardMarkup(row_width=3, resize_keyboard=True)
    keyboard.add(
        KeyboardButton("Сегодня"),
        KeyboardButton("Завтра"),
        KeyboardButton("Вчера"),
        KeyboardButton("Дата")
    )
    return keyboard

def translate_text(text: str) -> str:
    """Бесплатный перевод через MyMemory API"""
    try:
        url = "https://api.mymemory.translated.net/get"
        params = {
            'q': text,
            'langpair': 'en|ru',
            'de': 'user@example.com'
        }
        response = requests.get(url, params=params, timeout=5)
        if response.status_code == 200:
            return response.json().get('responseData', {}).get('translatedText', text)
    except Exception:
        pass
    return text

def get_daily_horoscope(sign_en: str, day: str) -> dict:
    """Получение и перевод гороскопа"""
    try:
        url = "https://horoscope-app-api.vercel.app/api/v1/get-horoscope/daily"
        params = {"sign": sign_en, "day": day}
        response = requests.get(url, params, timeout=10)
        horoscope = response.json()
        
        if 'data' in horoscope and 'horoscope_data' in horoscope['data']:
            horoscope['data']['horoscope_data'] = translate_text(horoscope['data']['horoscope_data'])
        
        return horoscope
    except Exception:
        return {"error": "Ошибка при получении гороскопа"}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    text = (
        "✨ *Добро пожаловать в Бот-Гороскоп!* ✨\n\n"
        "Я помогу вам узнать ваше астрологическое предсказание.\n"
        "Просто отправьте команду /гороскоп и следуйте инструкциям.\n\n"
        "Доступные команды:\n"
        "/гороскоп - Получить предсказание\n"
        "/помощь - Справка по боту"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text.lower() == 'помощь')
@bot.message_handler(commands=['помощь', 'help'])
def send_help(message):
    text = (
        "ℹ *Справка по боту-гороскопу*\n\n"
        "Как использовать:\n"
        "1. Отправьте /гороскоп\n"
        "2. Выберите ваш знак зодиака\n"
        "3. Укажите день (сегодня, завтра или дату)\n\n"
        "Бот покажет ваш персональный гороскоп на выбранный день.\n\n"
        "Поддерживаемые знаки:\n"
        "- Овен, Телец, Близнецы, Рак\n"
        "- Лев, Дева, Весы, Скорпион\n"
        "- Стрелец, Козерог, Водолей, Рыбы"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: message.text.lower() == 'гороскоп')
@bot.message_handler(commands=['гороскоп', 'horoscope'])
def sign_handler(message):
    text = "♈ *Выберите ваш знак зодиака:*\n" + "\n".join(
        f"- {sign.capitalize()}" for sign in ZODIAC_SIGNS.keys()
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=zodiac_keyboard())

@bot.message_handler(func=lambda message: message.text.lower() in ZODIAC_SIGNS.keys())
def handle_zodiac(message):
    sign_ru = message.text.lower()
    text = (
        "📅 *На какой день вам нужен гороскоп?*\n\n"
        "Вы можете выбрать:\n"
        "- Сегодня\n"
        "- Завтра\n"
        "- Вчера\n\n"
        "Или введите дату в формате *ГГГГ-ММ-ДД*"
    )
    bot.send_message(message.chat.id, text, parse_mode="Markdown", reply_markup=day_keyboard())
    bot.register_next_step_handler(message, lambda m: process_day(m, sign_ru))

def process_day(message, sign_ru):
    user_day = message.text.lower()
    
    if user_day == 'дата':
        text = "Введите дату в формате ГГГГ-ММ-ДД (например, 2023-12-31):"
        bot.send_message(message.chat.id, text, reply_markup=day_keyboard())
        bot.register_next_step_handler(message, lambda m: fetch_horoscope(m, sign_ru, m.text))
    else:
        fetch_horoscope(message, sign_ru, user_day)

def fetch_horoscope(message, sign_ru, day):
    bot.send_chat_action(message.chat.id, 'typing')
    
    try:
        day_en = {'сегодня': 'TODAY', 'завтра': 'TOMORROW', 'вчера': 'YESTERDAY'}.get(day.lower(), day)
        sign_en = ZODIAC_SIGNS[sign_ru.lower()]
        horoscope = get_daily_horoscope(sign_en, day_en)
        
        if 'error' in horoscope:
            raise Exception(horoscope['error'])
        
        data = horoscope["data"]
        response = (
            f"🔮 *Гороскоп для {sign_ru.capitalize()}*\n"
            f"📅 *Дата:* {data['date']}\n\n"
            f"{data['horoscope_data']}\n\n"
            f"⭐ Хорошего дня! ⭐"
        )
        
        bot.send_message(message.chat.id, response, parse_mode="Markdown", reply_markup=main_keyboard())
        
    except Exception as e:
        error_text = (
            "⚠ *Произошла ошибка*\n"
            "Не удалось получить гороскоп. Пожалуйста, попробуйте позже.\n\n"
            f"Техническая информация: {str(e)}"
        )
        bot.send_message(message.chat.id, error_text, parse_mode="Markdown", reply_markup=main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    bot.reply_to(message, "❓ Я не понимаю эту команду. Напишите /помощь для списка команд.", reply_markup=main_keyboard())

if __name__ == '__main__':
    print("Бот-гороскоп с быстрыми командами запущен!")
    bot.infinity_polling()