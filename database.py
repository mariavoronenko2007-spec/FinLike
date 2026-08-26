import os

from dotenv import load_dotenv
from psycopg2.extras import Json
from psycopg2.pool import ThreadedConnectionPool


load_dotenv()


connection_pool = ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    host=os.getenv("DB_HOST"),
    port=os.getenv("DB_PORT"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
)


def get_connection():
    return connection_pool.getconn()


def release_connection(connection):
    connection.rollback()
    connection_pool.putconn(connection)


def get_database_schema():
    connection = get_connection()
    cursor = connection.cursor()

    try:
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

        schema_text = ""
        current_table = None

        for table_name, column_name, data_type in columns:
            if table_name != current_table:
                current_table = table_name
                schema_text += f"\ntable {table_name}:\n"

            schema_text += f"- {column_name}: {data_type}\n"

        schema_text += "\nrelationships:\n"

        for (
            table_name,
            column_name,
            foreign_table,
            foreign_column,
        ) in relationships:
            schema_text += (
                f"- {table_name}.{column_name} "
                f"=> {foreign_table}.{foreign_column}\n"
            )

        return schema_text

    finally:
        cursor.close()
        release_connection(connection)


def check_user_login(login):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT student_code
            FROM students
            WHERE UPPER(student_code) = UPPER(%s)

            UNION ALL

            SELECT teacher_code
            FROM teachers
            WHERE UPPER(teacher_code) = UPPER(%s)

            UNION ALL

            SELECT applicant_code
            FROM applicants
            WHERE UPPER(applicant_code) = UPPER(%s)

            UNION ALL

            SELECT admin_code
            FROM administration
            WHERE UPPER(admin_code) = UPPER(%s)

            LIMIT 1;
            """,
            (
                login,
                login,
                login,
                login,
            ),
        )

        return cursor.fetchone() is not None

    finally:
        cursor.close()
        release_connection(connection)


def execute_select(sql):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "SET statement_timeout = 5000;"
        )

        cursor.execute(sql)

        columns = [
            description[0]
            for description in cursor.description
        ]

        rows = cursor.fetchall()

        return columns, rows

    finally:
        cursor.close()
        release_connection(connection)


def get_user_profile(login):
    connection = get_connection()
    cursor = connection.cursor()

    role = login.split("-")[0].lower()

    try:
        if role == "stu":
            cursor.execute(
                """
                SELECT
                    s.fio_name,
                    s.enrollment_year,
                    s.is_expelled,
                    p.name,
                    f.name
                FROM students s
                JOIN programs p
                    ON s.program_id = p.id
                JOIN faculties f
                    ON p.faculty_id = f.id
                WHERE UPPER(s.student_code) = UPPER(%s);
                """,
                (login,),
            )

            user = cursor.fetchone()

            if not user:
                return None

            cursor.execute(
                """
                SELECT
                    c.name,
                    g.grade,
                    g.date_received
                FROM grades g
                JOIN students s
                    ON g.student_id = s.id
                JOIN courses c
                    ON g.course_id = c.id
                WHERE UPPER(s.student_code) = UPPER(%s)
                ORDER BY g.date_received DESC
                LIMIT 5;
                """,
                (login,),
            )

            grade_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    COUNT(*),
                    ROUND(AVG(g.grade), 1)
                FROM grades g
                JOIN students s
                    ON g.student_id = s.id
                WHERE UPPER(s.student_code) = UPPER(%s);
                """,
                (login,),
            )

            grades_count, average_grade = cursor.fetchone()

            return {
                "role": "stu",
                "login": login,
                "full_name": user[0],
                "enrollment_year": user[1],
                "is_expelled": user[2],
                "program": user[3],
                "faculty": user[4],
                "grades_count": grades_count,
                "average_grade": average_grade,
                "grades": [
                    {
                        "title": row[0],
                        "subtitle": str(row[2]),
                        "value": row[1],
                    }
                    for row in grade_rows
                ],
                "courses": [
                    {
                        "title": row[0],
                        "subtitle": "Учебная дисциплина",
                    }
                    for row in grade_rows
                ],
            }

        if role == "tea":
            cursor.execute(
                """
                SELECT
                    t.full_name,
                    f.name
                FROM teachers t
                JOIN faculties f
                    ON t.faculty_id = f.id
                WHERE UPPER(t.teacher_code) = UPPER(%s);
                """,
                (login,),
            )

            user = cursor.fetchone()

            if not user:
                return None

            cursor.execute(
                """
                SELECT
                    c.name,
                    c.semester,
                    c.credits
                FROM courses c
                JOIN teachers t
                    ON c.teacher_id = t.id
                WHERE UPPER(t.teacher_code) = UPPER(%s)
                ORDER BY c.semester;
                """,
                (login,),
            )

            courses = cursor.fetchall()

            cursor.execute(
                """
                SELECT
                    c.name,
                    s.day_of_week,
                    s.start_time,
                    s.room
                FROM schedule s
                JOIN courses c
                    ON s.course_id = c.id
                JOIN teachers t
                    ON c.teacher_id = t.id
                WHERE UPPER(t.teacher_code) = UPPER(%s)
                ORDER BY s.day_of_week, s.start_time
                LIMIT 5;
                """,
                (login,),
            )

            schedule = cursor.fetchall()

            return {
                "role": "tea",
                "login": login,
                "full_name": user[0],
                "faculty": user[1],
                "faculty_short": user[1],
                "courses_count": len(courses),
                "courses": [
                    {
                        "title": row[0],
                        "subtitle": f"Семестр {row[1]}",
                        "value": f"{row[2]} кр.",
                    }
                    for row in courses
                ],
                "schedule": [
                    {
                        "title": row[0],
                        "subtitle": (
                            f"День недели: {row[1]}, "
                            f"аудитория {row[3]}"
                        ),
                        "value": str(row[2])[:5],
                    }
                    for row in schedule
                ],
            }

        if role == "app":
            cursor.execute(
                """
                SELECT full_name
                FROM applicants
                WHERE UPPER(applicant_code) = UPPER(%s);
                """,
                (login,),
            )

            user = cursor.fetchone()

            if not user:
                return None

            cursor.execute(
                """
                SELECT
                    p.name,
                    a.exam_score,
                    a.application_date,
                    a.is_admitted
                FROM applications a
                JOIN applicants ap
                    ON a.applicant_id = ap.id
                JOIN programs p
                    ON a.program_id = p.id
                WHERE UPPER(ap.applicant_code) = UPPER(%s)
                ORDER BY a.application_date DESC;
                """,
                (login,),
            )

            applications = cursor.fetchall()

            scores = [
                row[1]
                for row in applications
                if row[1] is not None
            ]

            return {
                "role": "app",
                "login": login,
                "full_name": user[0],
                "applications_count": len(applications),
                "best_score": max(scores) if scores else "—",
                "admitted": any(
                    row[3]
                    for row in applications
                ),
                "applications": [
                    {
                        "title": row[0],
                        "subtitle": str(row[2]),
                        "value": row[1],
                    }
                    for row in applications
                ],
                "statuses": [
                    {
                        "title": row[0],
                        "subtitle": "Результат рассмотрения",
                        "value": (
                            "Зачислен"
                            if row[3]
                            else "Конкурс"
                        ),
                    }
                    for row in applications
                ],
            }

        if role == "adm":
            cursor.execute(
                """
                SELECT
                    a.full_name,
                    a.position,
                    f.name
                FROM administration a
                LEFT JOIN faculties f
                    ON a.faculty_id = f.id
                WHERE UPPER(a.admin_code) = UPPER(%s);
                """,
                (login,),
            )

            user = cursor.fetchone()

            if not user:
                return None

            cursor.execute(
                """
                SELECT
                    (SELECT COUNT(*) FROM students),
                    (SELECT COUNT(*) FROM applicants),
                    (SELECT COUNT(*) FROM programs),
                    (SELECT COUNT(*) FROM teachers);
                """
            )

            (
                students_count,
                applicants_count,
                programs_count,
                teachers_count,
            ) = cursor.fetchone()

            return {
                "role": "adm",
                "login": login,
                "full_name": user[0],
                "position": user[1],
                "faculty": user[2],
                "students_count": students_count,
                "applicants_count": applicants_count,
                "programs_count": programs_count,
                "overview": [
                    {
                        "title": "Студенты",
                        "subtitle": "Всего в базе",
                        "value": students_count,
                    },
                    {
                        "title": "Преподаватели",
                        "subtitle": "Всего сотрудников",
                        "value": teachers_count,
                    },
                    {
                        "title": "Абитуриенты",
                        "subtitle": "Всего в базе",
                        "value": applicants_count,
                    },
                ],
                "department": [
                    {
                        "title": user[1],
                        "subtitle": (
                            user[2]
                            or "Администрация университета"
                        ),
                        "value": login,
                    }
                ],
            }

        return None

    finally:
        cursor.close()
        release_connection(connection)


def create_chat(user_login, title):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO chats (
                user_login,
                title
            )
            VALUES (%s, %s)
            RETURNING id;
            """,
            (
                user_login,
                title,
            ),
        )

        chat_id = cursor.fetchone()[0]

        connection.commit()

        return chat_id

    finally:
        cursor.close()
        release_connection(connection)


def get_user_chats(user_login):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                id,
                title,
                created_at
            FROM chats
            WHERE user_login = %s
            ORDER BY created_at DESC, id DESC;
            """,
            (user_login,),
        )

        rows = cursor.fetchall()

        return [
            {
                "id": row[0],
                "title": row[1],
                "created_at": row[2].isoformat(),
            }
            for row in rows
        ]

    finally:
        cursor.close()
        release_connection(connection)


def save_chat_message(
    chat_id,
    user_login,
    sender,
    content,
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT 1
            FROM chats
            WHERE id = %s
              AND user_login = %s;
            """,
            (
                chat_id,
                user_login,
            ),
        )

        if cursor.fetchone() is None:
            return False

        cursor.execute(
            """
            INSERT INTO chat_messages (
                chat_id,
                sender,
                content
            )
            VALUES (%s, %s, %s);
            """,
            (
                chat_id,
                sender,
                Json(content),
            ),
        )

        connection.commit()

        return True

    finally:
        cursor.close()
        release_connection(connection)


def get_chat_messages(
    chat_id,
    user_login,
):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            SELECT
                cm.sender,
                cm.content,
                cm.created_at
            FROM chat_messages cm
            JOIN chats c
                ON cm.chat_id = c.id
            WHERE cm.chat_id = %s
              AND c.user_login = %s
            ORDER BY cm.created_at, cm.id;
            """,
            (
                chat_id,
                user_login,
            ),
        )

        rows = cursor.fetchall()

        return [
            {
                "sender": row[0],
                "content": row[1],
                "created_at": row[2].isoformat(),
            }
            for row in rows
        ]

    finally:
        cursor.close()
        release_connection(connection)