import asyncio

import aiohttp

from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from aiogram.utils.formatting import (Bold, as_list, as_marked_section)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram import Router, types

from random import choices

from googletrans import Translator

router = Router()

translator = Translator()

class Recipes(StatesGroup):
    waiting_for_category = State()
    waiting_for_recipes = State()

@router.message(Command("category_search_random"))
async def recipes_handler(message: Message, command: CommandObject, state: FSMContext):
    if command.args is None:
        return await message.answer("Ошибка! Не указано количество рецептов!")

    async with aiohttp.ClientSession() as session:
        await state.set_data({"recipes_count" : command.args})
        async with session.get(url="https://www.themealdb.com/api/json/v1/1/list.php?c=list") as resp:
            data = await resp.json()
            builder = ReplyKeyboardBuilder()
            for meal in data['meals']:
                builder.add(types.KeyboardButton(text=meal["strCategory"]))
            builder.adjust(3)

            await message.answer("Выберите категорию блюда:", reply_markup=builder.as_markup(resize_keyboard=True))

            await state.set_state(Recipes.waiting_for_category.state)

@router.message(Recipes.waiting_for_category)
async def finder_meals_for_category(message: types.Message, state: FSMContext):
    async with aiohttp.ClientSession() as session:
        async with session.get(url=f"https://www.themealdb.com/api/json/v1/1/filter.php?c={message.text}") as resp:
            data = await resp.json()
            count = await state.get_data()
            recipes = choices(list(data['meals']), k=int(count['recipes_count']))
            id_recipes = [recipes[i]['idMeal'] for i in range(len(recipes))]
            await state.set_data({"id_recipes" : id_recipes})

            meals_name = [recipes[i]['strMeal'] for i in range(len(recipes))]
            names_ru = []
            for name in meals_name:
                names_ru.append((translator.translate(name, dest='ru')).text)

            kb = [
                [
                    types.KeyboardButton(text="Покажи рецепты")
                ]
            ]
            keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
            await message.answer(f"Как вам такие варианты: "
                                 f"{', '.join(names_ru)}", reply_markup=keyboard)

            await state.set_state(Recipes.waiting_for_recipes.state)

@router.message(Recipes.waiting_for_recipes)
async def recipes_description(message: Message, state:FSMContext):
    async with aiohttp.ClientSession() as session:
        data = await state.get_data()
        recipes_id = [data['id_recipes'][i] for i in range(len(data['id_recipes']))]
        fetch_awaitables = [fetch(i, session) for i in recipes_id]
        recipes = await asyncio.gather(*fetch_awaitables)
        for d_meal in recipes:
            for meal in d_meal['meals']:
                print(meal)
                response = as_list(
                    Bold(translator.translate(meal['strMeal'], dest='ru').text),
                    f"\nРецепт:",
                    f"{translator.translate(meal['strInstructions'], dest='ru').text}",
                    f"\nИнгредиенты:",
                    f"""{translator.translate(', '.join([f'{meal.get(f"strIngredient{i}", None)} - {meal.get(f"strMeasure{i}", None)}' for i in range(1, 21)]), dest='ru').text}"""
                )
                await message.answer(**response.as_kwargs())

async def fetch(id, session):
    async with session.get(url=f"https://www.themealdb.com/api/json/v1/1/lookup.php?i={id}") as resp:
        data = await resp.json()
        return data
