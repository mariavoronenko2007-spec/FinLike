from database import execute_select
from llm import generate_sql
from security import add_limit, check_sql


question = "Сколько учеников учиться на каждой дисциплине?"

sql = generate_sql(question)

print("Вопрос:")
print(question)

print("\nSQL от YandexGPT:")
print(sql)

is_safe, message = check_sql(sql)

print("\nПроверка безопасности:")
print(message)

if is_safe:
    safe_sql = add_limit(sql)

    columns, rows = execute_select(safe_sql)

    print("\nSQL после проверки:")
    print(safe_sql)

    print("\nСтолбцы:")
    print(columns)

    print("\nРезультат:")
    print(rows)