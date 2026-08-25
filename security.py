import re


ALLOWED_TABLES = {
    "faculties",
    "programs",
    "students",
    "teachers",
    "courses",
    "grades",
    "schedule",
    "applications",
}


FORBIDDEN_WORDS = {
    "insert",
    "update",
    "delete",
    "drop",
    "alter",
    "truncate",
    "create",
}


def clean_sql(sql):
    sql = sql.strip()

    if sql.startswith("```sql"):
        sql = sql[6:]

    elif sql.startswith("```"):
        sql = sql[3:]

    if sql.endswith("```"):
        sql = sql[:-3]

    return sql.strip()


def check_sql(sql):
    sql_clean = clean_sql(sql)
    sql_lower = sql_clean.lower()

    if not sql_lower.startswith("select"):
        return False, "Разрешены только SELECT-запросы."

    for word in FORBIDDEN_WORDS:
        if re.search(rf"\b{word}\b", sql_lower):
            return False, f"Запрещённая команда: {word}"

    tables = re.findall(
        r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        sql_lower,
    )

    for table in tables:
        if table not in ALLOWED_TABLES:
            return False, f"Таблица {table} не разрешена."

    if "students" in tables:
        if re.search(r"\bfull_name\b", sql_lower):
            return (
                False,
                "Информация о конкретном студенте является конфиденциальной."
            )

        if re.search(r"\bstudent_code\b", sql_lower):
            return (
                False,
                "Информация о конкретном студенте является конфиденциальной."
            )

        aggregate_functions = [
            "count(",
            "avg(",
            "sum(",
            "min(",
            "max(",
        ]

        has_aggregate = any(
            function in sql_lower
            for function in aggregate_functions
        )

        if not has_aggregate:
            return (
                False,
                "Персональные данные студентов не предоставляются. "
                "Доступна только агрегированная или обезличенная информация."
            )

    return True, "Запрос безопасен."


def add_limit(sql, limit=100):
    sql_clean = clean_sql(sql).rstrip(";")

    if not re.search(r"\blimit\b", sql_clean.lower()):
        sql_clean += f" LIMIT {limit}"

    return sql_clean + ";"

    for table in tables:
        if table not in ALLOWED_TABLES:
            return False, f"Таблица {table} не разрешена."

    return True, "Запрос безопасен."


def add_limit(sql, limit=100):
    sql_clean = sql.strip().rstrip(";")

    if not re.search(r"\blimit\b", sql_clean.lower()):
        sql_clean += f" LIMIT {limit}"

    return sql_clean + ";"