import os
import requests
from dotenv import load_dotenv



# Загрузка переменных окружения
load_dotenv()

# Получение API-ключа OpenRouter и токена бота из переменных окружения
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "meta-llama/llama-3.3-70b-instruct:free"



# Системный промт

SYSTEM_PROMPT = """

Ты — помощник для анализа промтов. Твоя задача — находить ошибки в промтах и давать рекомендации по их улучшению. 
Всегда возвращай ответ в следующем формате:

Ошибки: 
[список ошибок]

Рекомендации: 
[список рекомендаций]

Ищи следующие ошибки:
- Запрос слишком общий.
- Не хватает контекста.
- Неправильная формулировка.


Если ошибок нет, то не стоит давать большие рекомендации


Пример плохого промта: "Расскажи про ИИ"
Ошибки: Запрос слишком общий.
Рекомендации: Уточните, что именно вы хотите узнать про ИИ (например, "Какие есть типы ИИ?").

Пример хорошего промта: "Какие есть типы ИИ?"
Ошибки: Нет.
Рекомендации: Запрос сформулирован четко и конкретно.
"""



# Функция для отправки запроса к OpenRouter API
async def get_neural_response(prompt: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": MODEL,  # Модель для запроса
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},

            {"role": "user", "content": prompt}
            ],
    }
    
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Ошибка: {response.status_code}, {response.text}"
