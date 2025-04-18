from pymongo import MongoClient
from datetime import datetime
from dotenv import load_dotenv
import pytz
import os
import time
import random



# Загрузка переменных окружения
load_dotenv()

# Получение переменных окружения
MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

# MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION")

# Подключение к MongoDB
client = MongoClient(MONGODB_URL)
db = client[MONGODB_DATABASE]
# collection = db[MONGODB_COLLECTION]

collection_prompts_example = db["prompts_example"]   # Коллекция для примеров хороших промтов
collection_user_history = db["user_history"]  # Коллекция для истории
collection_user_progress = db["user_progress"]   # Коллекция для хранения прогресса пользователей
collection_questions = db["questions"]  # Коллекция для хранения вопросов для тестирования
collection_users = db["users"]   # регистрация пользователей в mini app

collection_lessons = db["lessons"] # Уроки
collection_questions_for_lessons = db["questions_for_lessons"]




def get_current_time() -> str:
    """Получает текущее время"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return current_time


# def convert_utc_to_local(utc_time: datetime, timezone="Europe/Moscow"):
#     """
#     Преобразует время из UTC в локальный часовой пояс.

#     :param utc_time: Время в UTC (объект datetime).
#     :param timezone: Название часового пояса (например, "Europe/Moscow").
#     :return: Время в локальном часовом поясе (объект datetime).
#     """
    
#     local_timezone = pytz.timezone(timezone)  # Укажите ваш часовой пояс
#     local_time = utc_time.replace(tzinfo=pytz.utc).astimezone(local_timezone)
#     return local_time



# Функция для получения списка тем из коллекции с примерами хороших промтов
async def get_topics():
    topics = collection_prompts_example.distinct("topic")  # Получаем уникальные темы
    return topics



def get_prompts_by_topic(selected_topic: str):
    """
    Получает промты для выбранной темы из базы данных.

    :param selected_topic: Название темы.
    :return: Список промтов.
    """
    
    # Запрос к базе данных для получения промтов по выбранной теме
    prompts_cursor = collection_prompts_example.find({"topic": selected_topic}, {"_id": 0, "prompt": 1})
    # Преобразуем курсор в список промтов
    prompts = [prompt["prompt"] for prompt in prompts_cursor]
    
    return prompts



def save_user_history(user_id: int, user_prompt: str, neural_response: str):
    """
    Сохраняет историю запросов и ответов нейронной сети.

    :param user_id: ID пользователя.
    :param user_prompt: Запрос пользователя.
    :param neural_response: Ответ нейронной сети.
    """
    
    
    
    history_entry = {
        "user_id": user_id,
        "prompt": user_prompt,
        "response": neural_response,
        "timestamp": get_current_time(),  # Временная метка
    }
    
    collection_user_history.insert_one(history_entry)




def get_user_history(user_id: int, selected_date: str = None):
    """
    Получает историю запросов и ответов для пользователя.
    Если указана selected_date, возвращает историю за конкретный день.

    :param user_id: ID пользователя.
    :param selected_date: Дата в формате 'YYYY-MM-DD' (опционально).
    :return: Список записей истории.
    """
    
    query = {"user_id": user_id}

    # Если указана дата, добавляем фильтр по дате
    if selected_date:
        # Ищем записи, где timestamp начинается с selected_date
        query["timestamp"] = {"$regex": f"^{selected_date}"}

    # Получаем историю из базы данных
    history = collection_user_history.find(query, {"_id": 0, "prompt": 1, "response": 1, "timestamp": 1})
    return list(history)



# def save_user_query(user_id: int, user_text: str, timestamp: datetime):
#     """
#     Сохраняет запрос пользователя в MongoDB.

#     :param user_id: ID пользователя.
#     :param user_text: Текст запроса.
#     :param time_stamp: Временная метка запроса.
#     """
    
#     local_time = convert_utc_to_local(timestamp, timezone="Europe/Moscow")

#     # Форматируем время в читабельный формат
#     formatted_timestamp = local_time.strftime("%Y-%m-%d %H:%M:%S")
    
    
#     query_data = {
#         "user_id": user_id,
#         "text": user_text,
#         "timestamp": formatted_timestamp,  # Преобразуем datetime в строку
#     }
    
#     collection.insert_one(query_data)
#     print(f"Запрос пользователя {user_id} сохранён в MongoDB.")
    
    
    
def save_user_progress(user_id: int, topic: str = None, new_average_percentage: float = None):
    """
    Сохраняет просмотренную тему (если передана) и инициализирует поле analyzed_prompts, если оно отсутствует.
    Также добавляет поля для хранения количества пройденных тестов и среднего процента выполнения.
    Если передан new_average_percentage, перезаписывает значение average_percentage.

    :param user_id: ID пользователя
    :param topic: Название темы, которую просмотрел пользователь (опционально)
    :param new_average_percentage: Новое значение для average_percentage (опционально)
    """
    
    # Проверяем, существует ли запись пользователя
    user_data = collection_user_progress.find_one({"user_id": user_id})

    if user_data:
        # Если запись существует, обновляем её
        update_data = {}
        
        # Если передана тема, добавляем её в список viewed_topics
        if topic is not None:
            update_data["$addToSet"] = {"viewed_topics": topic}

        # Если передан new_average_percentage, обновляем значение
        if new_average_percentage is not None:
            if "$set" not in update_data:
                update_data["$set"] = {}
            update_data["$set"]["average_percentage"] = new_average_percentage

        # Выполняем обновление
        if update_data:
            collection_user_progress.update_one(
                {"user_id": user_id},
                update_data
            )
            
    else:
        # Если запись не существует, создаём новую
        new_user_data = {
            "user_id": user_id,
            "viewed_topics": [],
            "analyzed_prompts": 0,
            "tests_passed": 0,
            "average_percentage": 0.0
        }
        
        collection_user_progress.insert_one(new_user_data)




def increment_analyzed_prompts(user_id: int):
    """
    Увеличивает количество проанализированных промтов на 1 для указанного пользователя.
    """
    
    collection_user_progress.update_one(
        {"user_id": user_id},
        {"$inc": {"analyzed_prompts": 1}},  # Увеличиваем значение на 1
        upsert=True  # Создаем запись, если её нет
    )



def increment_passed_tests(user_id: int):
    """
    Увеличивает количество пройденных тестов на 1 для указанного пользователя.
    """
    
    collection_user_progress.update_one(
        {"user_id": user_id},
        {"$inc": {"tests_passed": 1}},  # Увеличиваем значение на 1
        upsert=True  # Создаем запись, если её нет
    )


def get_user_progress(user_id: int) -> dict:
    """
    Возвращает все данные о прогрессе пользователя.
    
    :param user_id: ID пользователя.
    :return: Словарь с данными о прогрессе пользователя. Если пользователь не найден, возвращает пустой словарь.
    """
    
    user_progress = collection_user_progress.find_one({"user_id": user_id})
    if user_progress:
        return user_progress  # Возвращаем весь документ
    return {}  # Возвращаем пустой словарь, если пользователь не найден



async def get_unique_dates(user_id: int) -> list:
    """
    Возвращает список уникальных дат, за которые есть история запросов.
    """
    
    history =  collection_user_history.find({"user_id": user_id}).to_list(length=None)    
    unique_dates = set()
    
    for entry in history:
        date = entry['timestamp'].split()[0]  # Извлекаем дату из timestamp
        unique_dates.add(date)
    
    return sorted(unique_dates, reverse=True) 



def delete_history_by_date(user_id: int, date: str):
    """
    Удаляет историю запросов пользователя за указанную дату.

    :param user_id: ID пользователя.
    :param date: Дата в формате 'YYYY-MM-DD'.
    :return: Количество удаленных записей.
    """
    
    # Используем регулярное выражение для поиска записей, где timestamp начинается с указанной даты
    result = collection_user_history.delete_many({
        "user_id": user_id,
        "timestamp": {"$regex": f"^{date}"}  # Ищем строки, начинающиеся с date
    })
    
    return result.deleted_count  # Возвращает количество удаленных записей




def is_user_exist(user_id: int) -> bool:
    """
    Проверяет, существует ли пользователь в базе данных.
    """
    
    user =  collection_user_progress.find_one({"user_id": user_id})
    return user is not None

        

# Функция получения списка изученных тем пользователя
async def get_studied_topics(user_id):
    user_progress = collection_user_progress.find_one({"user_id": user_id})
    return user_progress.get("viewed_topics", []) if user_progress else []


# Функция получения 5 случайных вопросов по изученным темам
async def get_test_questions(user_id):
    studied_topics = await get_studied_topics(user_id)
    if not studied_topics:
        return []

    questions_cursor = collection_questions.find({"topic": {"$in": studied_topics}})
    questions_list = list(questions_cursor)
    
    return random.sample(questions_list, min(5, len(questions_list)))  # Берем до 5 вопросов



def register_user(user_id: int, username: str, first_name: str, last_name: str = ""):
    """Регистрирует нового пользователя или возвращает существующего"""
    user = collection_users.find_one({"user_id": user_id})
    
    if not user:
        new_user = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            # "email": 
            "registered_at": get_current_time(),
            "last_activity": get_current_time()
            
        }
        collection_users.insert_one(new_user)
        return False  # Пользователь новый
    
    else:
        collection_users.update_one(
            {"user_id": user_id},
            {"$set": {"last_activity": get_current_time()}})
        return True  # Пользователь уже существует



# Получает уроки из базы
def get_lessons():
    try:
        # Подключение к коллекции lessons
        lessons =  collection_lessons.find() 
                
        return lessons
    
    except Exception as e:
        print(f"Error getting lessons: {e}")
        return None
    
    
def get_lesson_by_number(number):
    try:
        lesson =  collection_lessons.find_one({"number": {"$regex": f"^{number}"}})
        return lesson
    except Exception as e:
        print(f"Error getting lesson: {e}")
        return None
    
    
    
def get_available_tests():
    """
    Получает список уникальных номеров уроков (number_lesson), для которых есть тесты
    Возвращает список вида ["1 урок", "2 урок", ...] или None при ошибке
    """
    
    try:
        # Используем distinct для получения уникальных значений number_lesson
        available_lessons = collection_questions_for_lessons.distinct("number_lesson")
        
        if not available_lessons:
            print("В базе нет тестов ни для одного урока")
            return None
            
        print(f"Найдены тесты для уроков: {available_lessons}")
        return available_lessons
    
    except Exception as e:
        print(f"Ошибка при получении списка уроков: {e}")
        return None
    
    

# Функция для получения полных данных теста по номеру урока
def get_lesson_test_data(lesson_number: str):
    """
    Получает полные данные теста для конкретного урока
    
    
    """
    try:
        test_data = collection_questions_for_lessons.find_one(
            {"number_lesson": lesson_number},
            {"_id": 0}  # Исключаем поле _id из результатов
        )
        return test_data
    
    except Exception as e:
        print(f"Ошибка при получении теста для урока {lesson_number}: {e}")
        return None