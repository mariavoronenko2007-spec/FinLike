import os

import psycopg2
from dotenv import load_dotenv


load_dotenv()


def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def get_database_schema():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            table_name,
            column_name,
            data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
    )

    columns = cursor.fetchall()

    cursor.execute(
        """
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
        ORDER BY tc.table_name;
        """
    )

    relationships = cursor.fetchall()

    cursor.close()
    connection.close()

    schema_text = ""
    current_table = None

    for table_name, column_name, data_type in columns:
        if table_name != current_table:
            current_table = table_name
            schema_text += f"\ntable {table_name}:\n"

        schema_text += f"- {column_name}: {data_type}\n"

    schema_text += "\rrelationships:\n"

    for table_name, column_name, foreign_table, foreign_column in relationships:
        schema_text += (
            f"- {table_name}.{column_name} "
            f"=> {foreign_table}.{foreign_column}\n"
        )

    return schema_text

def execute_select(sql):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SET statement_timeout = 5000;")
        cursor.execute(sql)

        columns = [description[0] for description in cursor.description]
        rows = cursor.fetchall()

        return columns, rows

    finally:
        cursor.close()
        connection.close()
    