import os
import logging
import time
import datetime

import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

from database import *
import random


from openrouter_api import get_neural_response

# Загрузка переменных окружения
load_dotenv()

# Получение токена бота из переменных окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()

# Определение состояний
class Form_testing_prompts(StatesGroup):
    testing_prompts = State()  # Состояние для анализа промтов

class Form_waiting_for_topic(StatesGroup):
    waiting_for_topic = State()  # Состояние ожидания выбора темы

# Определяем состояния теста
class TestStates(StatesGroup):
    taking_test = State()

# Настройка логирования
logging.basicConfig(level=logging.INFO)



# Функция для создания inline-клавиатуры с главным меню
def create_main_menu():
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(text="Тестирование промтов", callback_data="test_prompts"),
        InlineKeyboardButton(text="Примеры промтов", callback_data="examples"),
        InlineKeyboardButton(text="Пройти тест", callback_data="take_test"),
        InlineKeyboardButton(text="Мой прогресс", callback_data="progress"),
        InlineKeyboardButton(text="Просмотр истории", callback_data="view_history"),
    )
    builder.adjust(2)  # Расположение кнопок (2 кнопки в строке)
    return builder.as_markup()




# Обработчик любого текстового сообщения
@dp.message(F.text)
async def handle_any_message(message: types.Message, state: FSMContext):

    current_state = await state.get_state()
    if current_state == Form_testing_prompts.testing_prompts:
        # Если состояние "testing_prompts", передаем управление handle_prompt_analysis
        await handle_prompt_analysis(message, state)
    else:
        
        user_id = message.from_user.id

        # Проверяем, является ли пользователь новым
        if not  is_user_exist(user_id):  # Функция для проверки существования пользователя в базе
            # Отправляем приветственное сообщение
            await message.answer(
                "Привет! Я бот, который поможет тебе анализировать промты. "
                "Выбери действие:",
                reply_markup=create_main_menu(),
            )
            
            # Сохраняем пользователя в базе
            # save_user(user_id)
            
            save_user_progress(user_id)
            
        else:
            # Если пользователь уже существует, обрабатываем сообщение как обычно
            # await handle_prompt_analysis(message, state)
            # create_main_menu()
            
            await message.answer(
                "✨ Выберите действие: ✨",
                reply_markup=create_main_menu(),
            )


# Функция для создания inline-клавиатуры с темами
def create_topics_keyboard(topics):
    builder = InlineKeyboardBuilder()
    for topic in topics:
        builder.add(InlineKeyboardButton(text=topic, callback_data=f"topic_{topic}"))
    builder.adjust(2)  # Расположение кнопок (2 кнопки в строке)
    return builder.as_markup()




def create_dates_keyboard(dates, page: int = 0, items_per_page: int = 5):
    """
    Создает inline-клавиатуру с датами и кнопкой "Удалить".
    """
    builder = InlineKeyboardBuilder()
    
    # Вычисляем начальный и конечный индекс для текущей страницы
    start_index = page * items_per_page
    end_index = start_index + items_per_page
    paginated_dates = dates[start_index:end_index]

    # Добавляем кнопки с датами и кнопкой "Удалить"
    for date in paginated_dates:
        short_date = time.strftime('%d.%m.%y', time.strptime(date, '%Y-%m-%d'))
        builder.row(
            InlineKeyboardButton(text=short_date, callback_data=f"date_{date}"),
            InlineKeyboardButton(text="❌ Удалить", callback_data=f"delete_{date}"),
        )

    # Добавляем кнопки пагинации
    pagination_buttons = []
    if page > 0:
        pagination_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"dates_page_{page - 1}"))
    if end_index < len(dates):
        pagination_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"dates_page_{page + 1}"))
    
    if pagination_buttons:
        builder.row(*pagination_buttons)

    return builder.as_markup()



@dp.callback_query(F.data.startswith("delete_"))
async def handle_delete_history(callback: CallbackQuery):
    user_id = callback.from_user.id
    selected_date = callback.data.replace("delete_", "")  # Извлекаем дату из callback_data

    try:
        # Удаляем историю за выбранную дату
        deleted_count = delete_history_by_date(user_id, selected_date)

        if deleted_count > 0:
            await callback.message.answer(f"История за {selected_date} успешно удалена.")
            
        else:
            await callback.message.answer(f"История за {selected_date} отсутствует.")
            
    except Exception as e:
        logging.error(f"Ошибка при удалении истории: {e}")
        await callback.message.answer("Произошла ошибка при удалении истории. Пожалуйста, попробуйте позже.")

    
    # Получаем уникальные даты из истории
    unique_dates = await get_unique_dates(user_id)

    # Проверяем, есть ли даты в истории
    if not unique_dates:
        # Если дат нет, показываем главное меню
        await callback.message.edit_text("История запросов пуста.")

        await callback.message.answer("✨ Выберите действие: ✨", reply_markup=create_main_menu())

        
    else:
        # Если даты есть, показываем клавиатуру с датами
        await callback.message.answer(
            "Выберите дату:",
            reply_markup=create_dates_keyboard(unique_dates),
        )
    


# Добавьте обработчик для callback-запросов пагинации:
@dp.callback_query(F.data.startswith("dates_page_"))
async def handle_dates_pagination(callback: CallbackQuery):
    page = int(callback.data.replace("dates_page_", ""))
    user_id = callback.from_user.id

    # Получаем уникальные даты из истории
    unique_dates = get_unique_dates(user_id)

    # Обновляем клавиатуру с новой страницей
    await callback.message.edit_text(
        "Выберите дату:",
        reply_markup=create_dates_keyboard(unique_dates, page=page),
    )



# Обработка команды /start
@dp.message(Command("start"))
async def handle_start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Привет! Я бот, который общается с нейронной сетью. ✨ Выберите действие: ✨",
        reply_markup=create_main_menu(),
    )



# Обработка callback-запроса для главного меню
@dp.callback_query(F.data == "main_menu")
async def handle_main_menu(callback: CallbackQuery):
    
    # await callback.message.delete()
    await callback.message.edit_text(
        "✨ Выберите действие: ✨",
        reply_markup=create_main_menu()
    )




# Обработка callback-запроса "Тестирование промтов"
@dp.callback_query(F.data == "test_prompts")
async def handle_test_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите ваш промт, и я проанализирую его.")
    await state.set_state(Form_testing_prompts.testing_prompts)



# Обработка текстовых сообщений в состоянии "testing_prompts"
@dp.message(Form_testing_prompts.testing_prompts)
async def handle_prompt_analysis(message: types.Message, state: FSMContext):
    
    user_prompt = message.text
    user_id = message.from_user.id

    await message.answer("🤔 Думаю...")

    try:
        # Анализ промта с помощью OpenRouter API
        neural_response = await get_neural_response(
            f"Проанализируй этот промт и дай рекомендации: {user_prompt}"
        )

        # Сохраняем историю
        save_user_history(user_id, user_prompt, neural_response)


        # Увеличиваем количество проанализированных промтов
        increment_analyzed_prompts(user_id)


        # Отправляем результат пользователю
        
        if "Ошибки:" in neural_response:
            neural_response = neural_response.replace("Ошибки:", "❌ Ошибки:")

        # Добавляем зеленую галочку перед "Рекомендации"
        if "Рекомендации:" in neural_response:
            neural_response = neural_response.replace("Рекомендации:", "✅ Рекомендации:")

        await message.answer(f"\n{neural_response}")
        
    except Exception as e:
        logging.error(f"Ошибка при анализе промта: {e}")
        await message.answer("Произошла ошибка при анализе промта. Пожалуйста, попробуйте позже.")

    # Сбрасываем состояние
    await state.clear()
    await message.answer("✨ Выберите действие: ✨", reply_markup=create_main_menu())




# Обработка callback-запроса "Примеры промтов"
@dp.callback_query(F.data == "examples")
async def handle_examples(callback: CallbackQuery, state: FSMContext):
    # Получаем список тем из базы данных
    topics = await get_topics()

    if topics:
        await callback.message.edit_text(
            "Выберите тему:", reply_markup=create_topics_keyboard(topics)
        )
        await state.set_state(Form_waiting_for_topic.waiting_for_topic)
    else:
        await callback.message.edit_text("Темы не найдены в базе данных.")



# Обработка callback-запроса для выбора темы
@dp.callback_query(F.data.startswith("topic_"))
async def handle_topic_selection(callback: CallbackQuery, state: FSMContext):
    selected_topic = callback.data.replace("topic_", "")
    user_id = callback.from_user.id

    try:
        # Получаем промты для выбранной темы
        prompts = get_prompts_by_topic(selected_topic)

        if prompts:
            response = f"Промты по теме '{selected_topic}':\n\n"
            for i, prompt in enumerate(prompts, start=1):
                response += f"{i}. {prompt}\n"
            await callback.message.edit_text(response)

            # Сохраняем выбранную тему в прогресс пользователя
            save_user_progress(user_id, selected_topic)
            
            
        else:
            await callback.message.edit_text(f"Промты по теме '{selected_topic}' не найдены.")
    except Exception as e:
        logging.error(f"Ошибка при получении промтов: {e}")
        await callback.message.edit_text("Произошла ошибка при получении промтов. Пожалуйста, попробуйте позже.")

    # Сбрасываем состояние
    await state.clear()
    await callback.message.answer("✨ Выберите действие: ✨", reply_markup=create_main_menu())




# Обработка callback-запроса "Просмотр истории"
@dp.callback_query(F.data == "view_history")
async def handle_view_history(callback: CallbackQuery):
    user_id = callback.from_user.id

    # Получаем уникальные даты из истории
    unique_dates = await get_unique_dates(user_id)

    if unique_dates:
        await callback.message.edit_text(
            "Выберите дату:", reply_markup=create_dates_keyboard(unique_dates)
        )
    else:
        await callback.message.edit_text("История запросов пуста.")

        # await handle_main_menu()
        await callback.message.answer("✨ Выберите действие: ✨", reply_markup=create_main_menu())



@dp.callback_query(F.data.startswith("date_"))
async def handle_date_selection(callback: CallbackQuery):
    
    user_id = callback.from_user.id
    selected_date = callback.data.replace("date_", "")  # Извлекаем дату из callback_data
    
    # Получаем историю пользователя
    history = get_user_history(user_id, selected_date)
    

    # Формируем сообщение с историей за выбранную дату
    if history:
        response = f"История за {selected_date}:\n\n"
        
        for entry in history:
            response += f"📅 {entry['timestamp']}\n\n"
            response += f"❓ {entry['prompt']}\n\n"
            response += f"🤖 {entry['response']}\n\n\n"
        # await callback.message.edit_text(response)
        
        # Отправляем длинное сообщение
        await send_long_message(callback.message.chat.id, response)

        
    else:
        await callback.message.edit_text(f"История за {selected_date} отсутствует.")

    # Возврат в главное меню
    await callback.message.answer("✨ Выберите действие: ✨", reply_markup=create_main_menu())
    


# Обработка callback-запроса "Мой прогресс"
@dp.callback_query(F.data == "progress")
async def handle_progress(callback: CallbackQuery):
    user_id = callback.from_user.id

    try:
        # Получаем прогресс пользователя
        user_progress = get_user_progress(user_id)

        if user_progress:
            # Формируем сообщение с прогрессом
            response = "Ваш прогресс 🧠:\n\n"
            
            # Просмотренные темы
            viewed_topics = user_progress.get("viewed_topics", [])
            if viewed_topics:
                response += "📚 Просмотренные темы:\n"
                for topic in viewed_topics:
                    response += f"📖 {topic}\n"
            else:
                response += "📚 Вы ещё не просмотрели ни одной темы.\n"
            
            # Количество проанализированных промтов
            analyzed_prompts = user_progress.get("analyzed_prompts", 0)
            response += f"\n📊 Проанализировано промтов: {analyzed_prompts}\n"
            
            # Количество пройденных тестов
            tests_passed = user_progress.get("tests_passed", 0)
            response += f"\n📝 Пройдено тестов: {tests_passed}\n"
            
            # Средний процент выполнения тестов
            average_percentage = user_progress.get("average_percentage", 0.0)
            response += f"\n📈 Средний процент выполнения: {average_percentage}%\n"
            
            await callback.message.edit_text(response)
        else:
            await callback.message.edit_text("Прогресс не найден.")
    except Exception as e:
        logging.error(f"Ошибка при получении прогресса: {e}")
        await callback.message.edit_text("Произошла ошибка при получении вашего прогресса. Пожалуйста, попробуйте позже.")

    # Возврат в главное меню
    await callback.message.answer("✨ Выберите действие: ✨", reply_markup=create_main_menu())
    
    
    
    

def split_message(text: str, max_length: int = 4096) -> list[str]:
    """
    Разделяет текст на части, каждая из которых не превышает max_length символов.
    """
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]



async def send_long_message(chat_id: int, text: str):
    """
    Отправляет длинное сообщение, разбивая его на части.
    """
    parts = split_message(text)
    for part in parts:
        await bot.send_message(chat_id, part)
        
        





# Обработчик начала теста
@dp.callback_query(F.data == "take_test")
async def handle_take_test(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    questions = await get_test_questions(user_id)

    if not questions:
        await callback.message.edit_text("❌ У вас нет изученных тем или нет доступных вопросов.")
        await callback.message.answer("✨ Выберите действие: ✨", reply_markup=create_main_menu())
        return
    
    await state.update_data(questions=questions, current_question=0, correct_answers=0)
    await state.set_state(TestStates.taking_test)

    # Отправляем первый вопрос
    await send_next_question(callback.message, state, is_first=True)


# Функция отправки следующего вопроса
async def send_next_question(message: types.Message, state: FSMContext, is_first=False):
    data = await state.get_data()
    current_question_index = data["current_question"]
    questions = data["questions"]

    if current_question_index >= len(questions):  # Все вопросы пройдены
        await finish_test(message, state)
        return

    question_data = questions[current_question_index]
    question_text = question_data["question"]
    options = question_data["options"]

    builder = InlineKeyboardBuilder()
    for key, value in options.items():
        builder.add(InlineKeyboardButton(text=value, callback_data=f"answer_{key}"))
    builder.adjust(1)  # Кнопки в 1 столбец

    if is_first:
        await message.answer(f"📝 Вопрос {current_question_index + 1}/5:\n{question_text}", reply_markup=builder.as_markup())
    else:
        await message.edit_text(f"📝 Вопрос {current_question_index + 1}/5:\n{question_text}", reply_markup=builder.as_markup())




# Обработчик ответов пользователя
@dp.callback_query(F.data.startswith("answer_"))
async def handle_answer(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    current_question_index = data["current_question"]
    questions = data["questions"]
    
    question_data = questions[current_question_index]
    selected_answer = callback.data.replace("answer_", "")
    correct_answer_key = question_data["correct_answer"].split(")")[0] + ")"

    is_correct = selected_answer == correct_answer_key
    correct_answers = data["correct_answers"] + (1 if is_correct else 0)

    # Обновляем состояние
    await state.update_data(current_question=current_question_index + 1, correct_answers=correct_answers)

    # Убираем кнопки, оставляя только вопрос
    # await callback.message.edit_text(f"📝 Вопрос {current_question_index + 1}/5\nВы выбрали вариант: {question_data['options'][selected_answer]}")

    # Даем небольшую паузу перед следующим вопросом
    # await asyncio.sleep(1.5)

    # Отправляем следующий вопрос или завершаем тест
    await send_next_question(callback.message, state)


# # Завершение теста
# async def finish_test(message: types.Message, state: FSMContext):
#     data = await state.get_data()
#     correct_answers = data["correct_answers"]
#     total_questions = len(data["questions"])
#     percentage = round((correct_answers / total_questions) * 100, 2)

#     result_text = f"🎉 Тест завершён!\n✅ Правильных ответов: {correct_answers}/{total_questions}\n📊 Процент выполнения: {percentage}%"

#     await message.edit_text(result_text)

#     # Очистка состояния и возврат в главное меню
#     await state.clear()
#     await message.answer("✨ Выберите действие: ✨", reply_markup=create_main_menu())




async def finish_test(message: types.Message, state: FSMContext):
    # Получаем данные из состояния
    data = await state.get_data()
    user_id = message.chat.id

    correct_answers = data["correct_answers"]
    total_questions = len(data["questions"])
    percentage = round((correct_answers / total_questions) * 100, 2)

    # Формируем текст результата
    result_text = f"🎉 Тест завершён!\n✅ Правильных ответов: {correct_answers}/{total_questions}\n📊 Процент выполнения: {percentage}%"
    await message.edit_text(result_text)

    # Очистка состояния и возврат в главное меню
    await state.clear()
    await message.answer("✨ Выберите действие: ✨", reply_markup=create_main_menu())

    # Обновление данных пользователя в базе данных

    # Получаем текущие данные пользователя
    increment_passed_tests(user_id)

    user_data = get_user_progress(user_id)

    if user_data:
                
        # Пересчитываем средний процент выполнения
        current_average = user_data["average_percentage"]
        tests_passed = user_data["tests_passed"]
        
        new_average = round((current_average * (tests_passed - 1) + percentage) / tests_passed, 2)

   
        save_user_progress(user_id=user_id, new_average_percentage=new_average)



# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())