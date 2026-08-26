import re

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import (
    check_user_login,
    create_chat,
    execute_select,
    get_chat_messages,
    get_user_chats,
    get_user_profile,
    save_chat_message,
)
from llm import generate_sql, get_role
from security import add_limit, check_sql


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginData(BaseModel):
    login: str


class Question(BaseModel):
    question: str
    login: str | None = None


class ChatCreateData(BaseModel):
    login: str
    title: str


class ChatRequest(BaseModel):
    login: str
    chat_id: int


class ChatMessageData(BaseModel):
    login: str
    chat_id: int
    sender: str
    content: dict


def is_invalid_question(question):
    text = question.strip()

    if not text:
        return True

    letters = re.findall(
        r"[A-Za-zА-Яа-яЁё]",
        text,
    )

    if not letters:
        return True

    if " " not in text:
        non_letters = re.findall(
            r"[^A-Za-zА-Яа-яЁё]",
            text,
        )

        if len(non_letters) >= len(letters):
            return True

    return False


def asks_for_secrets(question):
    text = question.lower()

    secret_words = [
        "пароль",
        "пароли",
        "password",
        "passwords",
        "api key",
        "api_key",
        "секретный ключ",
        "секретные ключи",
        "токен доступа",
        "токены доступа",
        "access token",
        ".env",
        "db_password",
        "yandex_api_key",
    ]

    return any(
        word in text
        for word in secret_words
    )


@app.post("/login")
def login(login_data: LoginData):
    user_login = login_data.login.strip().upper()

    if not user_login:
        return {
            "success": False,
            "message": "Введите логин.",
        }

    if "-" not in user_login:
        return {
            "success": False,
            "message": "Неверный формат логина.",
        }

    if not check_user_login(user_login):
        return {
            "success": False,
            "message": "Пользователь с таким логином не найден.",
        }

    return {
        "success": True,
        "login": user_login,
    }


@app.post("/profile")
def profile(login_data: LoginData):
    user_login = login_data.login.strip().upper()

    if not user_login:
        return {
            "success": False,
            "message": "Логин не передан.",
        }

    profile_data = get_user_profile(
        user_login
    )

    if not profile_data:
        return {
            "success": False,
            "message": "Пользователь не найден.",
        }

    return {
        "success": True,
        "profile": profile_data,
    }


@app.post("/chats")
def chats(login_data: LoginData):
    user_login = login_data.login.strip().upper()

    if not check_user_login(user_login):
        return {
            "success": False,
            "chats": [],
        }

    user_chats = get_user_chats(
        user_login
    )

    return {
        "success": True,
        "chats": user_chats,
    }


@app.post("/chats/create")
def create_new_chat(
    chat_data: ChatCreateData
):
    user_login = chat_data.login.strip().upper()
    title = chat_data.title.strip()

    if not check_user_login(user_login):
        return {
            "success": False,
        }

    if not title:
        title = "Новый диалог"

    chat_id = create_chat(
        user_login,
        title,
    )

    return {
        "success": True,
        "chat_id": chat_id,
    }


@app.post("/chats/messages")
def chat_messages(
    chat_request: ChatRequest
):
    user_login = (
        chat_request.login
        .strip()
        .upper()
    )

    if not check_user_login(user_login):
        return {
            "success": False,
            "messages": [],
        }

    messages = get_chat_messages(
        chat_request.chat_id,
        user_login,
    )

    return {
        "success": True,
        "messages": messages,
    }


@app.post("/chats/message")
def add_chat_message(
    message_data: ChatMessageData
):
    user_login = (
        message_data.login
        .strip()
        .upper()
    )

    if not check_user_login(user_login):
        return {
            "success": False,
        }

    if message_data.sender not in {
        "user",
        "assistant",
    }:
        return {
            "success": False,
        }

    saved = save_chat_message(
        message_data.chat_id,
        user_login,
        message_data.sender,
        message_data.content,
    )

    return {
        "success": saved,
    }


@app.post("/ask")
def ask(question_data: Question):
    question = question_data.question.strip()
    login = question_data.login

    if is_invalid_question(question):
        return {
            "success": False,
            "answer": (
                "Не удалось понять запрос. "
                "Сформулируйте вопрос о данных университета."
            ),
            "sql": "",
            "columns": [],
            "rows": [],
        }

    if asks_for_secrets(question):
        return {
            "success": False,
            "answer": (
                "Доступ к паролям, ключам и другим "
                "секретным данным запрещён."
            ),
            "sql": "",
            "columns": [],
            "rows": [],
        }

    if login:
        login = login.strip().upper()

        if not check_user_login(login):
            login = None

    role = get_role(login)

    sql = generate_sql(
        question,
        login,
    )

    is_safe, message = check_sql(
        sql,
        role,
        login,
    )

    if not is_safe:
        return {
            "success": False,
            "answer": message,
            "sql": "",
            "columns": [],
            "rows": [],
        }

    safe_sql = add_limit(sql)

    try:
        columns, rows = execute_select(
            safe_sql
        )

        if len(rows) == 0:
            answer = (
                "По вашему запросу данные не найдены."
            )

        elif (
            len(rows) == 1
            and len(rows[0]) == 1
        ):
            answer = (
                f"Результат: {rows[0][0]}"
            )

        else:
            answer = (
                f"Найдено записей: {len(rows)}"
            )

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
            "sql": "",
            "columns": [],
            "rows": [],
        }