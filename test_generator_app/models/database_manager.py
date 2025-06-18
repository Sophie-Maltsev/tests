import sqlite3
import os
from flask import g  # Используем g для хранения соединения в контексте запроса
from ..config import DATABASE_PATH  # Импортируем путь к БД из config.py


def get_db_connection():
    """
    Устанавливает соединение с базой данных SQLite.
    Соединение хранится в g для повторного использования в рамках одного запроса.
    """
    db = getattr(g, '_database', None)
    if db is None:
        # Убедимся, что директория database существует
        db_dir = os.path.dirname(DATABASE_PATH)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
        db = g._database = sqlite3.connect(DATABASE_PATH)
        db.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по именам
    return db


def close_db_connection(exception=None):
    """Закрывает соединение с базой данных, если оно было открыто."""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db_command(app):
    """Команда для инициализации БД (создания таблиц)."""
    with app.app_context():  # Нужен контекст приложения для g
        conn = get_db_connection()
        create_tables(conn)
        close_db_connection()
        print("База данных инициализирована и таблицы созданы/проверены.")


def create_tables(conn):
    """ Создает таблицы в базе данных, если они еще не существуют """
    sql_create_questions_table = """
    CREATE TABLE IF NOT EXISTS questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_text TEXT NOT NULL,
        topic TEXT
    );
    """

    sql_create_answers_table = """
    CREATE TABLE IF NOT EXISTS answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question_id INTEGER NOT NULL,
        answer_text TEXT NOT NULL,
        is_correct INTEGER NOT NULL DEFAULT 0, -- 0 for false, 1 for true
        FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
    );
    """

    sql_create_generated_tests_table = """
    CREATE TABLE IF NOT EXISTS generated_tests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        num_questions INTEGER NOT NULL,
        creation_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    """

    sql_create_test_questions_link_table = """
    CREATE TABLE IF NOT EXISTS test_questions (
        test_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        PRIMARY KEY (test_id, question_id),
        FOREIGN KEY (test_id) REFERENCES generated_tests (id) ON DELETE CASCADE,
        FOREIGN KEY (question_id) REFERENCES questions (id) ON DELETE CASCADE
    );
    """

    sql_create_user_attempts_table = """
    CREATE TABLE IF NOT EXISTS user_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        test_instance_id INTEGER NOT NULL,
        score INTEGER,
        total_questions_in_test INTEGER,
        attempt_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (test_instance_id) REFERENCES generated_tests (id) ON DELETE CASCADE
    );
    """

    try:
        cursor = conn.cursor()
        print(f"Подключено к БД: {DATABASE_PATH}")
        print("Создание таблицы 'questions'...")
        cursor.execute(sql_create_questions_table)
        print("Создание таблицы 'answers'...")
        cursor.execute(sql_create_answers_table)
        print("Создание таблицы 'generated_tests'...")
        cursor.execute(sql_create_generated_tests_table)
        print("Создание таблицы 'test_questions'...")
        cursor.execute(sql_create_test_questions_link_table)
        print("Создание таблицы 'user_attempts'...")
        cursor.execute(sql_create_user_attempts_table)
        conn.commit()
        print("Таблицы успешно созданы или уже существуют.")
    except sqlite3.Error as e:
        print(f"Ошибка при создании таблиц: {e}")
        conn.rollback()  # Откатываем изменения в случае ошибки
    # Соединение будет закрыто через close_db_connection в app.py или init_db_command


# Функции для непосредственного выполнения запросов (можно вынести в отдельный CRUD модуль, если их станет много)
def query_db(query, args=(), one=False):
    """Выполняет SQL-запрос и возвращает результат."""
    cur = get_db_connection().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    """Выполняет SQL-запрос (INSERT, UPDATE, DELETE) и коммитит изменения."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, args)
    last_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    return last_id  # Возвращаем ID последней вставленной строки, если применимо