from ..models.database_manager import query_db, execute_db  # Используем наши обертки для БД
import sqlite3  # Для обработки специфичных ошибок SQLite


def get_all_questions_with_details():
    """Возвращает список всех вопросов с их темами."""
    sql = "SELECT id, question_text, topic FROM questions ORDER BY id DESC"
    questions_raw = query_db(sql)
    return [dict(q) for q in questions_raw] if questions_raw else []


def get_question_by_id_with_answers(question_id):
    """Возвращает один вопрос по ID вместе с его вариантами ответов."""
    question_sql = "SELECT * FROM questions WHERE id = ?"
    question_raw = query_db(question_sql, (question_id,), one=True)

    if not question_raw:
        return None

    answers_sql = "SELECT * FROM answers WHERE question_id = ? ORDER BY id"
    answers_raw = query_db(answers_sql, (question_id,))

    question_dict = dict(question_raw)
    question_dict['answers'] = [dict(ans) for ans in answers_raw] if answers_raw else []
    return question_dict


def get_min_free_id():
    """
    Возвращает минимальное свободное положительное число для вставки в поле id.
    Если таблица пуста — возвращает 1.
    """
    sql = """
    SELECT 
        COALESCE(
            (SELECT MIN(t.id + 1) 
             FROM questions t 
             LEFT JOIN questions t2 ON t2.id = t.id + 1 
             WHERE t2.id IS NULL),
            1
        ) AS free_id
    """
    row = query_db(sql, one=True)
    return row['free_id'] if row else 1

def add_new_question(question_text, topic, answers_data):
    """
    Добавляет новый вопрос и его ответы, используя минимальный свободный ID.
    """
    if not question_text or len(answers_data) < 2:
        return None

    try:
        min_id = get_min_free_id()
        # ВАЖНО: Поле id в таблице questions НЕ ДОЛЖНО быть AUTOINCREMENT.
        question_id = execute_db("INSERT INTO questions (id, question_text, topic) VALUES (?, ?, ?)",
                                 (min_id, question_text, topic if topic else None))
        if question_id:
            for ans_data in answers_data:
                execute_db("INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)",
                           (min_id, ans_data['text'], ans_data['is_correct']))
            return min_id
    except sqlite3.Error as e:
        print(f"Ошибка в question_service.add_new_question: {e}")
        return None
    return None


def update_existing_question(question_id, question_text, topic, new_answers_data):
    """
    Обновляет существующий вопрос и его ответы.
    new_answers_data: полный новый список ответов для этого вопроса.
    Возвращает True в случае успеха, False в случае ошибки.
    """
    if not question_text or len(new_answers_data) < 2:
        return False

    try:
        # Обновляем сам вопрос
        execute_db("UPDATE questions SET question_text = ?, topic = ? WHERE id = ?",
                   (question_text, topic if topic else None, question_id))

        # Удаляем старые ответы
        execute_db("DELETE FROM answers WHERE question_id = ?", (question_id,))

        # Добавляем новые ответы
        for ans_data in new_answers_data:
            execute_db("INSERT INTO answers (question_id, answer_text, is_correct) VALUES (?, ?, ?)",
                       (question_id, ans_data['text'], ans_data['is_correct']))
        return True
    except sqlite3.Error as e:
        print(f"Ошибка в question_service.update_existing_question: {e}")
        return False


def delete_question_by_id(question_id):
    """
    Удаляет вопрос и связанные с ним ответы (благодаря ON DELETE CASCADE).
    Возвращает True в случае успеха, False в случае ошибки.
    """
    try:
        # ON DELETE CASCADE в схеме должен удалить связанные ответы и записи в test_questions
        execute_db("DELETE FROM questions WHERE id = ?", (question_id,))
        return True
    except sqlite3.Error as e:
        print(f"Ошибка в question_service.delete_question_by_id: {e}")
        return False


def count_total_questions():
    """Возвращает общее количество вопросов в базе."""
    result = query_db("SELECT COUNT(id) as count FROM questions", one=True)
    return result['count'] if result else 0