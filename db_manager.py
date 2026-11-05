import os
import psycopg2
import time
from pymongo import MongoClient
from dotenv import load_dotenv

# Завантажуємо змінні з файлу .env до os.environ
load_dotenv()
# Отримання параметрів підключення зі змінних оточення
try:
    PG_DB = os.environ["POSTGRES_DB"]
    PG_USER = os.environ["POSTGRES_USER"]
    PG_PASSWORD = os.environ["POSTGRES_PASSWORD"]
    PG_PORT = os.environ["POSTGRES_PORT"]
    MONGO_USERNAME = os.environ["MONGO_INITDB_ROOT_USERNAME"]
    MONGO_PASSWORD = os.environ["MONGO_INITDB_ROOT_PASSWORD"]
    MONGO_PORT = os.environ["MONGO_PORT"]
# Програма негайно зупиниться, якщо хоча б однієї змінної немає
except KeyError as e:
    raise RuntimeError(f"Критична помилка конфігурації: відсутня змінна оточення {e}")

# ФОРМУВАННЯ РЯДКІВ ПІДКЛЮЧЕННЯ
DSN = f"dbname={PG_DB} user={PG_USER} password={PG_PASSWORD} host=localhost port={PG_PORT}"
MONGO_URI = f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@localhost:{MONGO_PORT}/labdb?authSource=admin"

# КЛАС МЕНЕДЖЕРА БАЗИ ДАНИХ
class DatabaseManager:
    # ФУНКЦІЯ, ЩО РЕАЛІЗУЄ ТРАНЗАКЦІЮ ВИСТАВЛЕННЯ ОЦІНКИ
    # Аргументи передає користувач через UI
    @staticmethod
    def execute_grade_transaction(gradebook_id, course_id, grade_id, thread_name, use_lock, log_callback):
        # Відкриття з'єднання з базою даних PostgreSQL, що у контейнері
        conn = psycopg2.connect(DSN)
        # Збереження змін транзакції лише при виконанні conn.commit()
        conn.autocommit = False
        # Створення об'єкта для взаємодії з базою даних
        cur = conn.cursor()

        try:
            # Виклик безпечного логування для фонового потоку
            log_callback(f"[{thread_name}] Початок транзакції (Блокування: {use_lock})...")

            '''
            Читання поточного сумарного балу та кількості оцінок.
            Залежно від аргументу use_lock вибірка виконується з/без блокування.
            '''
            if use_lock:
                cur.execute("SELECT total_score, grade_count FROM gradebooks WHERE gradebook_id = %s FOR UPDATE",
                            (gradebook_id,))
            else:
                cur.execute("SELECT total_score, grade_count FROM gradebooks WHERE gradebook_id = %s", (gradebook_id,))

            # Витягування поточних даних з результату запиту
            total_score, grade_count = cur.fetchone()

            # Вибірка балу за ID
            cur.execute("SELECT grade_value FROM grade_types WHERE grade_id = %s", (grade_id,))
            grade_value = cur.fetchone()[0]

            log_callback(f"[{thread_name}] Прочитано: total_score={total_score}, grade_count={grade_count}. Виставляється оцінка: {grade_value}")

            # Штучна затримка, щоб обидва потоки прочитали початковий стан
            time.sleep(1.5)

            # Вставка нової оцінки в таблицю grades
            cur.execute(
                "INSERT INTO grades (gradebook_id, course_id, grade_id) VALUES (%s, %s, %s)",
                (gradebook_id, course_id, grade_id)
            )

            # Оновлення рейтингу студента
            new_total = total_score + grade_value
            new_count = grade_count + 1

            # Оновлення даних в таблиці залікової книжки
            cur.execute(
                "UPDATE gradebooks SET total_score = %s, grade_count = %s WHERE gradebook_id = %s",
                (new_total, new_count, gradebook_id)
            )

            # Фіксація транзакції
            conn.commit()
            log_callback(f"[{thread_name}] УСПІХ. Результат: total_score={new_total}, grade_count={new_count}")

        except Exception as e:
            # Відкат транзакції у випадку помилки
            conn.rollback()
            log_callback(f"[{thread_name}] ПОМИЛКА: {e}")
        finally:
            # Закриття з'єднання
            cur.close()
            conn.close()

    # ОТРИМАННЯ СПИСКУ КУРСІВ
    @staticmethod
    def get_courses():
        try:
            conn = psycopg2.connect(DSN)
            cur = conn.cursor()
            cur.execute("SELECT course_id, course_name FROM courses ORDER BY course_id")
            courses = cur.fetchall()
            cur.close()
            conn.close()
            return courses
        except Exception as e:
            # Виведення помилки в консоль, щоб уникнути мовчазного ігнорування проблем підключення
            print(f"Помилка підключення при отриманні списку курсів: {e}")
            return [(1, 'Бази даних'), (2, 'Машинне навчання')]

    # ОТРИМАННЯ ДОСТУПНИХ ОЦІНОК
    @staticmethod
    def get_grades():
        try:
            conn = psycopg2.connect(DSN)
            cur = conn.cursor()
            cur.execute("SELECT grade_id, grade_value FROM grade_types ORDER BY grade_id")
            grades = cur.fetchall()
            cur.close()
            conn.close()
            return grades
        except Exception as e:
            # Виведення помилки в консоль, щоб уникнути мовчазного ігнорування проблем підключення
            print(f"Помилка підключення при отриманні доступних оцінок: {e}")
            return [(1, 60), (2, 75), (3, 80), (4, 90), (5, 100)]

    # ОТРИМАННЯ ІСТОРІЇ ВСІХ ВИСТАВЛЕНИХ ОЦІНОК З ДЕТАЛЯМИ (JOIN)
    @staticmethod
    def get_all_grades_history():
        try:
            conn = psycopg2.connect(DSN)
            cur = conn.cursor()
            query = """
                SELECT g.grade_record_id, s.full_name, c.course_name, gt.grade_value, g.created_at
                FROM grades g
                JOIN gradebooks gb ON g.gradebook_id = gb.gradebook_id
                JOIN students s ON gb.student_id = s.student_id
                JOIN courses c ON g.course_id = c.course_id
                JOIN grade_types gt ON g.grade_id = gt.grade_id
                ORDER BY g.created_at DESC;
            """
            cur.execute(query)
            history = cur.fetchall()
            cur.close()
            conn.close()
            return history
        except Exception as e:
            # Виведення помилки в консоль, щоб уникнути мовчазного ігнорування проблем підключення
            print(f"Помилка підключення при отриманні історії оцінок: {e}")
            return []

    # ОТРИМАННЯ ДОКУМЕНТІВ MONGODB
    @staticmethod
    def get_mongo_course_profiles():
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        try:
            db = client["labdb"]
            docs = list(db["course_profiles"].find())
            return docs
        finally:
            client.close()