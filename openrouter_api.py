import os
import requests
from dotenv import load_dotenv
# import json
import asyncio


# # Загрузка переменных окружения
load_dotenv()

# # Получение API-ключа OpenRouter и токена бота из переменных окружения
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "meta-llama/llama-4-scout:free"

MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen2.5-vl-3b-instruct:free",
    "meta-llama/llama-4-scout:free",
    "deepseek/deepseek-v3-base:free"
]


# # # Системный промт

# Добавить температуру
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
async def get_neural_response_from_one_model(prompt: str) -> str:
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
    print(response.json())
    if response.status_code == 200:
        
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Ошибка: {response.status_code}, {response.text}"









import asyncio
import aiohttp
from typing import List, Dict

async def get_model_response(session: aiohttp.ClientSession, model: str, prompt: str) -> Dict:
    """Получает ответ от конкретной модели"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
    }
    
    try:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                return {
                    "model": model,
                    "response": result["choices"][0]["message"]["content"],
                    "status": "success"
                }
            else:
                error = await response.text()
                return {
                    "model": model,
                    "response": f"Ошибка: {response.status}, {error}",
                    "status": "error"
                }
    except Exception as e:
        return {
            "model": model,
            "response": f"Ошибка соединения: {str(e)}",
            "status": "error"
        }


async def get_all_models_responses(prompt: str) -> List[Dict]:
    """Получает ответы от всех моделей"""
    async with aiohttp.ClientSession() as session:
        tasks = [get_model_response(session, model, prompt) for model in MODELS]
        return await asyncio.gather(*tasks)

async def process_with_main_model(prompt: str, responses: List[Dict]) -> str:
    """Обрабатывает ответы с помощью основной модели"""
    # Выбираем только успешные ответы
    success_responses = [r for r in responses if r["status"] == "success"]
    
    if not success_responses:
        return "Все модели вернули ошибки"
    
    # Формируем контекст для основной модели
    context = "Ответы других моделей:\n"
    for resp in success_responses:
        context += f"\n{resp['model']}:\n{resp['response']}\n"
    
    # Запрашиваем анализ у основной модели
    main_model = "meta-llama/llama-4-scout:free"
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    
    data = {
        "model": main_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": context},
            {"role": "user", "content": "Проанализируй ответы других моделей и дай итоговый ответ"}
        ],
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                return result["choices"][0]["message"]["content"]
            else:
                error = await response.text()
                return f"Ошибка при запросе к основной модели: {error}"



async def get_neural_response(prompt: str, use_several_models:bool = False) -> str:
    """Основная функция для получения ответа"""
    
    
    if use_several_models:
    # Получаем ответы от всех моделей
        all_responses = await get_all_models_responses(prompt)
        
        # Обрабатываем ответы с помощью основной модели
        final_response = await process_with_main_model(prompt, all_responses)
        
        # Формируем полный отчет
        report = f"{final_response}\n\n"
        report += "ОТВЕТЫ МОДЕЛЕЙ:\n"
        for resp in all_responses:
            report += f"\n{resp['model']} ({resp['status']}):\n{resp['response']}\n"
        print(report)
        return report

    else:
        print("use 1 model")
        task = await get_neural_response_from_one_model(prompt)
        return task



# Пример использования
async def main():
    prompt = "Объясни, как работает искусственный интеллект?"
    response = await get_neural_response(prompt)



if __name__ == "__main__":
    asyncio.run(main())