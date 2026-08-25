from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import execute_select
from llm import generate_sql
from security import add_limit, check_sql


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Question(BaseModel):
    question: str


@app.post("/ask")
def ask(question_data: Question):
    question = question_data.question

    sql = generate_sql(question)

    is_safe, message = check_sql(sql)

    if not is_safe:
        return {
            "success": False,
            "answer": message,
            "sql": sql,
            "columns": [],
            "rows": [],
        }

    safe_sql = add_limit(sql)

    try:
        columns, rows = execute_select(safe_sql)

        if len(rows) == 1 and len(rows[0]) == 1:
            answer = f"Результат: {rows[0][0]}"
        elif len(rows) == 0:
            answer = "По вашему запросу данные не найдены."
        else:
            answer = f"Найдено записей: {len(rows)}"

        return {
            "success": True,
            "answer": answer,
            "sql": safe_sql,
            "columns": columns,
            "rows": rows,
        }

    except Exception:
        return {
            "success": False,
            "answer": "Не удалось выполнить запрос.",
            "sql": safe_sql,
            "columns": [],
            "rows": [],
        }