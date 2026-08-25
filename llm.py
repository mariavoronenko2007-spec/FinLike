import os

from dotenv import load_dotenv
from openai import OpenAI

from database import get_database_schema


load_dotenv()


client = OpenAI(
    api_key=os.getenv("YANDEX_API_KEY"),
    base_url="https://ai.api.cloud.yandex.net/v1",
)


def generate_sql(question):
    folder_id = os.getenv("YANDEX_FOLDER_ID")
    schema = get_database_schema()

    system_prompt = f"""
Ты генерируешь SQL-запросы для PostgreSQL.

Используй только таблицы и столбцы из этой схемы:

{schema}

Правила:
- Генерируй только SELECT-запросы.
- Не используй INSERT, UPDATE, DELETE, DROP, ALTER.
- Не придумывай таблицы и столбцы.
- Используй связи между таблицами из схемы.
- Не выводи ФИО студентов.
- Верни только SQL-запрос без объяснений и без Markdown.
- НЕ ИСПОЛЬЗУЙ КАВЫЧКИ И ТАБУЛЯЦИЮ. ОТВЕТ СТРОКА
"""

    response = client.chat.completions.create(
        model=f"gpt://{folder_id}/yandexgpt/latest",
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ],
        max_tokens=200,
        temperature=0,
    )

    return response.choices[0].message.content.strip()