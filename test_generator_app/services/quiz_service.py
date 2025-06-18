from ..models.database_manager import query_db, execute_db
import random
import sqlite3


def generate_new_test_instance(num_questions_to_generate):
    """
    Генерирует новый экземпляр теста:
    1. Выбирает случайные вопросы.
    2. Создает запись в generated_tests.
    3. Создает связи в test_questions.
    Возвращает ID нового экземпляра теста или None в случае ошибки.
    """
    all_question_ids_raw = query_db("SELECT id FROM questions")
    if not all_question_ids_raw:
        return None  # Нет вопросов для генерации

    all_question_ids = [q['id'] for q in all_question_ids_raw]

    if num_questions_to_generate <= 0:
        return None  # Некорректное количество

    actual_num_to_select = min(num_questions_to_generate, len(all_question_ids))
    if actual_num_to_select == 0:
        return None

    selected_question_ids = random.sample(all_question_ids, actual_num_to_select)

    try:
        test_instance_id = execute_db("INSERT INTO generated_tests (num_questions) VALUES (?)",
                                      (actual_num_to_select,))
        if test_instance_id:
            for q_id in selected_question_ids:
                execute_db("INSERT INTO test_questions (test_id, question_id) VALUES (?, ?)",
                           (test_instance_id, q_id))
            return test_instance_id
    except sqlite3.Error as e:
        print(f"Ошибка в quiz_service.generate_new_test_instance: {e}")
        return None
    return None


def get_test_questions_for_instance(test_instance_id):
    """
    Получает все вопросы и варианты ответов для данного экземпляра теста.
    """
    # Проверяем, существует ли тест
    test_instance = query_db("SELECT id FROM generated_tests WHERE id = ?", (test_instance_id,), one=True)
    if not test_instance:
        return None  # Тест не найден

    sql_get_questions = """
    SELECT q.id, q.question_text, q.topic
    FROM questions q
    JOIN test_questions tq ON q.id = tq.question_id
    WHERE tq.test_id = ?
    ORDER BY RANDOM() 
    """
    questions_raw = query_db(sql_get_questions, (test_instance_id,))

    if not questions_raw:
        return []  # Нет вопросов для этого теста (маловероятно, если тест создан)

    questions_with_answers = []
    for q_raw in questions_raw:
        question_dict = dict(q_raw)
        answers_raw = query_db("SELECT id, answer_text FROM answers WHERE question_id = ? ORDER BY RANDOM()",
                               (question_dict['id'],))
        question_dict['answers'] = [dict(ans_raw) for ans_raw in answers_raw] if answers_raw else []
        questions_with_answers.append(question_dict)

    return questions_with_answers


def submit_and_evaluate_test(test_instance_id, user_submitted_answers):
    """
    Проверяет ответы пользователя, сохраняет попытку и возвращает результат.
    user_submitted_answers: словарь {question_id: selected_answer_id}
    Возвращает словарь с результатами или None в случае ошибки.
    """
    test_instance = query_db("SELECT id, num_questions FROM generated_tests WHERE id = ?",
                             (test_instance_id,), one=True)
    if not test_instance:
        return {'error': 'Test instance not found.'}

    # Получаем ID вопросов, которые действительно были в этом тесте
    test_question_ids_raw = query_db("SELECT question_id FROM test_questions WHERE test_id = ?",
                                     (test_instance_id,))
    if not test_question_ids_raw:
        return {'error': 'No questions found for this test instance.'}

    actual_test_question_ids = {tq['question_id'] for tq in test_question_ids_raw}

    # Проверка, что пользователь ответил на все вопросы теста
    # Это можно сделать и на клиенте, но серверная проверка обязательна
    if len(user_submitted_answers) != len(actual_test_question_ids):
        # Убедимся, что все ключи user_submitted_answers являются вопросами этого теста
        # и что все вопросы теста есть в ответах
        submitted_q_ids = set(user_submitted_answers.keys())
        if not submitted_q_ids.issubset(actual_test_question_ids) or not actual_test_question_ids.issubset(
                submitted_q_ids):
            return {'error': 'Mismatch in submitted answers and actual test questions. Please answer all questions.'}

    score = 0
    for question_id, selected_answer_id in user_submitted_answers.items():
        if question_id not in actual_test_question_ids:
            # Пропускаем ответ, если вопрос не из этого теста (доп. проверка)
            continue

        correct_answer_info = query_db("SELECT is_correct FROM answers WHERE id = ? AND question_id = ?",
                                       (selected_answer_id, question_id), one=True)
        if correct_answer_info and correct_answer_info['is_correct'] == 1:
            score += 1

    total_questions_in_test_attempt = len(actual_test_question_ids)

    try:
        attempt_id = execute_db("""
            INSERT INTO user_attempts (test_instance_id, score, total_questions_in_test) 
            VALUES (?, ?, ?)
        """, (test_instance_id, score, total_questions_in_test_attempt))

        return {
            'attempt_id': attempt_id,
            'test_instance_id': test_instance_id,
            'score': score,
            'total_questions_in_test': total_questions_in_test_attempt
        }
    except sqlite3.Error as e:
        print(f"Ошибка в quiz_service.submit_and_evaluate_test при сохранении попытки: {e}")
        return {'error': 'Failed to save test attempt.'}