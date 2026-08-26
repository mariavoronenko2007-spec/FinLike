import re


ALLOWED_TABLES = {
    "faculties",
    "programs",
    "students",
    "teachers",
    "courses",
    "grades",
    "schedule",
    "applicants",
    "applications",
    "administration",
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


AGGREGATE_FUNCTIONS = [
    "count",
    "avg",
    "sum",
    "min",
    "max",
]


def clean_sql(sql):
    sql = sql.strip()

    if sql.startswith("```sql"):
        sql = sql[6:]

    elif sql.startswith("```"):
        sql = sql[3:]

    if sql.endswith("```"):
        sql = sql[:-3]

    return sql.strip()


def get_tables(sql):
    return re.findall(
        r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        sql.lower(),
    )


def has_aggregate(sql):
    sql_lower = sql.lower()

    for function in AGGREGATE_FUNCTIONS:
        if re.search(
            rf"\b{function}\s*\(",
            sql_lower,
        ):
            return True

    return False


def get_select_part(sql):
    match = re.search(
        r"^\s*select\s+(.*?)\s+from\s",
        sql,
        flags=re.IGNORECASE | re.DOTALL,
    )

    if not match:
        return ""

    return match.group(1).lower()


def has_student_personal_fields(sql):
    select_part = get_select_part(sql)

    return bool(
        re.search(
            r"\b(fio_name|student_code)\b",
            select_part,
        )
    )


def has_applicant_personal_fields(sql):
    select_part = get_select_part(sql)

    return bool(
        re.search(
            r"\b(full_name|applicant_code)\b",
            select_part,
        )
    )


def has_own_student_filter(sql, login):
    if not login:
        return False

    pattern = (
        rf"\bstudent_code\s*=\s*"
        rf"['\"]{re.escape(login)}['\"]"
    )

    return bool(
        re.search(
            pattern,
            sql,
            flags=re.IGNORECASE,
        )
    )


def has_own_applicant_filter(sql, login):
    if not login:
        return False

    pattern = (
        rf"\bapplicant_code\s*=\s*"
        rf"['\"]{re.escape(login)}['\"]"
    )

    return bool(
        re.search(
            pattern,
            sql,
            flags=re.IGNORECASE,
        )
    )


def has_other_student_code(sql, login):
    if not login:
        return False

    codes = re.findall(
        r"['\"](STU-[A-Z0-9_-]+)['\"]",
        sql,
        flags=re.IGNORECASE,
    )

    for code in codes:
        if code.lower() != login.lower():
            return True

    return False


def has_other_applicant_code(sql, login):
    if not login:
        return False

    codes = re.findall(
        r"['\"](APP-[A-Z0-9_-]+)['\"]",
        sql,
        flags=re.IGNORECASE,
    )

    for code in codes:
        if code.lower() != login.lower():
            return True

    return False


def uses_student_name(sql):
    return bool(
        re.search(
            r"\bfio_name\b",
            sql,
            flags=re.IGNORECASE,
        )
    )


def uses_applicant_name(sql):
    return bool(
        re.search(
            r"\bfull_name\b",
            sql,
            flags=re.IGNORECASE,
        )
    )


def check_sql(sql, role="anon", login=None):
    sql_clean = clean_sql(sql)
    sql_lower = sql_clean.lower()

    if not sql_lower.startswith("select"):
        return (
            False,
            "Изменение данных запрещено. "
            "Доступны только запросы на получение информации.",
        )

    if ";" in sql_clean.rstrip(";"):
        return (
            False,
            "Разрешён только один запрос за раз.",
        )

    for word in FORBIDDEN_WORDS:
        if re.search(
            rf"\b{word}\b",
            sql_lower,
        ):
            return (
                False,
                "Изменение данных запрещено.",
            )

    tables = get_tables(sql_clean)

    if not tables:
        return (
            False,
            "Не удалось обработать запрос. "
            "Сформулируйте вопрос о данных университета.",
        )

    for table in tables:
        if table not in ALLOWED_TABLES:
            return (
                False,
                "Запрос нельзя выполнить "
                "по текущим данным.",
            )

    uses_student_data = (
        "students" in tables
        or "grades" in tables
    )

    uses_applicant_data = (
        "applicants" in tables
        or "applications" in tables
    )

    if role == "anon":

        if has_student_personal_fields(sql_clean):
            return (
                False,
                "Персональные данные студентов "
                "недоступны без авторизации.",
            )

        if has_applicant_personal_fields(sql_clean):
            return (
                False,
                "Персональные данные абитуриентов "
                "недоступны без авторизации.",
            )

        if (
            uses_student_data
            or uses_applicant_data
        ) and not has_aggregate(sql_clean):
            return (
                False,
                "Без авторизации доступна только "
                "общая статистическая информация.",
            )

    elif role == "stu":

        if has_other_student_code(
            sql_clean,
            login,
        ):
            return (
                False,
                "Данные других студентов "
                "являются конфиденциальной информацией.",
            )

        if has_other_applicant_code(
            sql_clean,
            login,
        ):
            return (
                False,
                "Данные других абитуриентов "
                "являются конфиденциальной информацией.",
            )

        if uses_applicant_data:

            if has_applicant_personal_fields(sql_clean):
                return (
                    False,
                    "Персональные данные абитуриентов "
                    "недоступны для вашей роли.",
                )

            if uses_applicant_name(sql_clean):
                return (
                    False,
                    "Данные конкретного абитуриента "
                    "являются конфиденциальными.",
                )

            if not has_aggregate(sql_clean):
                return (
                    False,
                    "Персональные данные абитуриентов "
                    "недоступны для вашей роли.",
                )

        if uses_student_data:

            own_data = has_own_student_filter(
                sql_clean,
                login,
            )

            if has_student_personal_fields(sql_clean):
                if not own_data:
                    return (
                        False,
                        "Вы можете получать только "
                        "свои персональные данные.",
                    )

            if (
                uses_student_name(sql_clean)
                and not own_data
            ):
                return (
                    False,
                    "Данные другого студента "
                    "являются конфиденциальными.",
                )

            if (
                not own_data
                and not has_aggregate(sql_clean)
            ):
                return (
                    False,
                    "Вы можете получать свои данные "
                    "или общую статистическую информацию.",
                )

    elif role == "app":

        if has_other_applicant_code(
            sql_clean,
            login,
        ):
            return (
                False,
                "Данные других абитуриентов "
                "являются конфиденциальной информацией.",
            )

        if has_other_student_code(
            sql_clean,
            login,
        ):
            return (
                False,
                "Данные других студентов "
                "являются конфиденциальной информацией.",
            )

        if uses_student_data:

            if has_student_personal_fields(sql_clean):
                return (
                    False,
                    "Персональные данные студентов "
                    "недоступны для вашей роли.",
                )

            if uses_student_name(sql_clean):
                return (
                    False,
                    "Данные конкретного студента "
                    "являются конфиденциальными.",
                )

            if not has_aggregate(sql_clean):
                return (
                    False,
                    "Персональные данные студентов "
                    "недоступны для вашей роли.",
                )

        if uses_applicant_data:

            own_data = has_own_applicant_filter(
                sql_clean,
                login,
            )

            if has_applicant_personal_fields(sql_clean):
                if not own_data:
                    return (
                        False,
                        "Вы можете получать только "
                        "свои персональные данные.",
                    )

            if (
                uses_applicant_name(sql_clean)
                and not own_data
            ):
                return (
                    False,
                    "Данные другого абитуриента "
                    "являются конфиденциальными.",
                )

            if (
                not own_data
                and not has_aggregate(sql_clean)
            ):
                return (
                    False,
                    "Вы можете получать свои данные "
                    "или общую статистическую информацию.",
                )

    elif role == "tea":
        return (
            True,
            "Запрос безопасен.",
        )

    elif role == "adm":
        return (
            True,
            "Запрос безопасен.",
        )

    else:
        if (
            uses_student_data
            or uses_applicant_data
        ) and not has_aggregate(sql_clean):
            return (
                False,
                "Недостаточно прав для получения информации.",
            )

    return (
        True,
        "Запрос безопасен.",
    )


def add_limit(sql, limit=100):
    sql_clean = clean_sql(sql).rstrip(";")

    if not re.search(
        r"\blimit\b",
        sql_clean.lower(),
    ):
        sql_clean += f" LIMIT {limit}"

    return sql_clean + ";"