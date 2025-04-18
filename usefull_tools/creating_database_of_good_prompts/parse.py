from pymongo import MongoClient
import re
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
collection = db["prompts_example"]




# Функция для парсинга текста
def parse_text(text):
    # Регулярное выражение для поиска тем
    topic_pattern = r"### \*\*(.*?)\*\*"
    
    # Разделяем текст на блоки по темам
    blocks = re.split(r"---\n", text)  # Разделитель между темами

    # Сбор данных в структурированный формат
    parsed_data = []
    for block in blocks:
        # Ищем тему в текущем блоке
        topic_match = re.search(topic_pattern, block)
        if topic_match:
            topic = topic_match.group(1)
            
            # Ищем все промты в текущем блоке
            prompts = re.findall(r"\d+\.\s*(.*?)\n", block)
            
            # Добавляем тему и промты в результат
            if prompts:
                parsed_data.append({
                    "topic": topic,
                    "prompts": prompts,
                })

    return parsed_data




if __name__ == "__main__":
    
    path_to_file = "usefull_tools/creating_database_of_good_prompts/good_prompts.txt"
    
    
    with open(path_to_file, "r") as f:
        text = f.read()
        
        parsed_data = parse_text(text)

    # Вывод результата
    for data in parsed_data:
        print(f"Тема: {data['topic']}")
        for i, prompt in enumerate(data["prompts"], start=1):
            print(f"{i}. {prompt}")
        print("---")
        
        
        
    for topic_data in parsed_data:
        topic = topic_data["topic"]
        prompts = topic_data["prompts"]
        
        # Сохраняем каждый промт отдельно
        for prompt in prompts:
            document = {
                "topic": topic,
                "prompt": prompt,
            }
            
            collection.insert_one(document)

    print("Промты успешно сохранены в базу данных.")