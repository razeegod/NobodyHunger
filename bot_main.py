import asyncio

import logging
import sys

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import F
from aiogram.utils.formatting import (Bold, as_list, as_marked_section)

from token_data import TOKEN

from recipes_handler import router

dp = Dispatcher()
dp.include_router(router)

@dp.message(CommandStart())
async def start_handler(message: Message):
    keyboard_buttons = [
        [
            types.KeyboardButton(text="Команды"),
            types.KeyboardButton(text="Описание бота"),
        ]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=keyboard_buttons, resize_keyboard=True)

    await message.answer(f"Привет, {message.from_user.full_name}! Чем могу помочь?", reply_markup=keyboard)

@dp.message(F.text.lower() == "команды")
async def commands_handler(message: Message):
    response = as_list(
        as_marked_section(
            Bold("Список доступных команд: "),
            "/category_search_random 3 - задаст нужное количество рецептов",
            marker=("🎂 ")
        )
    )

    await message.answer(**response.as_kwargs())

@dp.message(F.text.lower() == "описание бота")
async def description_handler(message: Message):
    await message.answer("Бот, который не оставит голодным и предложит разные рецепты!")

async def main():
    bot = Bot(TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())