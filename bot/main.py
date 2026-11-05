import asyncio
import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from dotenv import load_dotenv

load_dotenv()
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: Message):
    url = os.environ['MINI_APP_URL']
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='🏟 MAYDONni ochish', web_app=WebAppInfo(url=url))]])
    await message.answer('MAYDON — Namangan shahridagi futbol, stol tennisi va bilyard joylari.', reply_markup=keyboard)

async def main():
    bot = Bot(os.environ['BOT_TOKEN'])
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
