import re
from pymongo import MongoClient


from dotenv import load_dotenv
import os

# Загрузка переменных окружения
load_dotenv()

# Получение переменных окружения
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")

# Подключение к MongoDB
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DATABASE]

collection_questions = db["questions"]  # Коллекция для хранения вопросов


def parse_questions(text):
    sections = re.split(r'### Тема: ', text)[1:]
    parsed_data = []
    
    for section in sections:
        lines = section.split("\n", 1)
        topic = lines[0].strip()
        content = lines[1] if len(lines) > 1 else ""
        
        questions = re.findall(r'\d+\. \*\*Промт:\*\* "(.+?)"', content)
        options = re.findall(r'\*\*Варианты ответа:\*\*(.*?)\*\*Правильный ответ:\*\*', content, re.S)
        correct_answers = re.findall(r'\*\*Правильный ответ:\*\* (.+)', content)
        
        for i in range(len(questions)):
            options_list = re.findall(r'([A-D]\)) (.+)', options[i])
            parsed_data.append({
                "topic": topic,
                "question": questions[i],
                "options": dict(options_list),
                "correct_answer": correct_answers[i]
            })
    
    return parsed_data



def save_to_mongo(data):
    collection_questions.insert_many(data)
        
        
        
        
if __name__ == "__main__":
    
    path_to_file = "usefull_tools/creating_database_with_test_questions/qustions.txt"
    
    with open(path_to_file, "r") as f:
        text = f.read()
        parsed_data = parse_questions(text)
        save_to_mongo(parsed_data)
        