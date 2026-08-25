# FinLake

FinLake — веб-приложение для работы с данными университета на естественном языке.

Пользователь задаёт вопрос, YandexGPT преобразует его в SQL, запрос проходит проверку безопасности и только после этого выполняется в PostgreSQL. Результат возвращается в интерфейс в виде ответа, SQL-запроса и таблицы.

## Как работает

```text
Пользователь
    ↓
Frontend
    ↓
FastAPI
    ↓
YandexGPT
    ↓
SQL
    ↓
security.py
    ↓
PostgreSQL
    ↓
Ответ + SQL + таблица
```

LLM не имеет прямого доступа к базе данных и используется только для генерации SQL.

## Структура проекта

```text
university_ai/
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   ├── account.html
│   ├── account.css
│   └── account.js
├── api.py
├── database.py
├── llm.py
├── security.py
├── main.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

- `api.py` — API на FastAPI, связывает frontend и backend.
- `database.py` — подключение к PostgreSQL, получение схемы и выполнение запросов.
- `llm.py` — отправка вопроса и схемы БД в YandexGPT, получение SQL.
- `security.py` — проверка SQL перед выполнением.
- `frontend/` — интерфейс FinLake и история диалогов.

## Безопасность

Перед выполнением каждый SQL-запрос проверяется приложением.

Реализовано:

- разрешены только `SELECT`-запросы;
- запрещены изменяющие команды (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER` и другие);
- разрешён доступ только к таблицам из whitelist;
- к выборкам добавляется `LIMIT`;
- установлен `statement_timeout`;
- запрещено раскрытие персональных данных студентов;
- запрос выполняется в PostgreSQL только после успешной проверки.

Персональные данные студентов не выдаются. Разрешены агрегированные и обезличенные результаты, например количество студентов или средний балл.

## Настройка

### 1. Создать виртуальное окружение

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Установить зависимости

```bash
pip install -r requirements.txt
```

### 3. Настроить PostgreSQL

Необходимо создать базу данных проекта и выполнить SQL-скрипт с таблицами и тестовыми данными.

### 4. Настроить переменные окружения

В корне проекта создать файл `.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=university
DB_USER=postgres
DB_PASSWORD=your_database_password

YANDEX_API_KEY=your_yandex_api_key
YANDEX_FOLDER_ID=your_yandex_folder_id
```

Нужно указать реальные данные подключения к PostgreSQL и данные доступа к YandexGPT.

`.env` содержит секретные данные и не должен попадать в GitHub.

В `.gitignore` должны быть:

```gitignore
.env
.venv/
__pycache__/
*.pyc
.DS_Store
```

## Запуск

### Backend

Активировать окружение:

```bash
source .venv/bin/activate
```

Запустить FastAPI:

```bash
uvicorn api:app --reload
```

После запуска API доступно по адресу:

```text
http://127.0.0.1:8000
```

Для проверки API можно открыть:

```text
http://127.0.0.1:8000/docs
```

### Frontend

Открыть:

```text
frontend/index.html
```

через Live Server в VS Code.

Во время работы приложения должны быть доступны PostgreSQL, FastAPI и YandexGPT API.

## Пример работы

Вопрос пользователя:

```text
Сколько всего студентов?
```

YandexGPT формирует SQL:

```sql
SELECT COUNT(*) FROM students;
```

После проверки запрос выполняется в PostgreSQL.

Frontend показывает:

```text
Результат: 45

SQL:
SELECT COUNT(*) FROM students LIMIT 100;

Таблица:
count
45
```

Если пользователь запрашивает сведения о конкретном студенте, запрос блокируется и данные из PostgreSQL не выдаются.
