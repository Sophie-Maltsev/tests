from flask import Blueprint, render_template, request, redirect, url_for, flash
from ..services import question_service  # Импортируем наш сервис

# Создаем Blueprint. 'admin_bp' - имя блюпринта, __name__ - имя модуля, template_folder - если шаблоны для этого блюпринта в отдельной папке
admin_routes_bp = Blueprint('admin_bp', __name__, template_folder='../templates/admin')


# Если шаблоны лежат в общей папке templates, то template_folder можно не указывать или указать '../templates'

@admin_routes_bp.route('/')  # Будет доступно по /admin/ (т.к. url_prefix='/admin' в app.py)
@admin_routes_bp.route('/questions')
def manage_questions_page():
    questions = question_service.get_all_questions_with_details()
    # Указываем путь к шаблону относительно общей папки templates, если template_folder не настроен идеально
    return render_template('manage_questions.html', questions=questions)


@admin_routes_bp.route('/questions/add', methods=['GET', 'POST'])
def add_question_page():
    if request.method == 'POST':
        question_text = request.form.get('question_text', '').strip()
        topic = request.form.get('topic', '').strip()

        answers_data = []
        try:
            correct_answer_index = int(request.form['correct_answer_index'])
        except (KeyError, ValueError):
            flash('Не выбран правильный ответ или передано некорректное значение.', 'error')
            return render_template('question_form.html',
                                   form_title="Добавить новый вопрос",
                                   form_action=url_for('admin_bp.add_question_page'),
                                   # Используем имя эндпоинта с префиксом блюпринта
                                   question=request.form)  # Передаем обратно введенные данные

        answer_count_from_form = 0
        for i in range(4):  # Предполагаем макс. 4 ответа как в форме
            ans_text_key = f'answer_text_{i}'
            if ans_text_key in request.form and request.form[ans_text_key].strip():
                answer_text = request.form[ans_text_key].strip()
                is_correct = 1 if i == correct_answer_index else 0
                answers_data.append({'text': answer_text, 'is_correct': is_correct})
                answer_count_from_form += 1

        if not question_text:
            flash('Текст вопроса не может быть пустым.', 'error')
        elif answer_count_from_form < 2:
            flash('Вопрос должен иметь как минимум два варианта ответа.', 'error')
        else:
            question_id = question_service.add_new_question(question_text, topic, answers_data)
            if question_id:
                flash('Вопрос успешно добавлен!', 'success')
                return redirect(url_for('admin_bp.manage_questions_page'))
            else:
                flash('Ошибка при добавлении вопроса. Проверьте введенные данные.', 'error')

        # Если дошли сюда - была ошибка, показываем форму снова с введенными данными
        return render_template('question_form.html',
                               form_title="Добавить новый вопрос",
                               form_action=url_for('admin_bp.add_question_page'),
                               question=request.form,  # request.form ведет себя как словарь
                               answers_submitted=answers_data)  # Для восстановления ответов, если нужно

    return render_template('question_form.html',
                           form_title="Добавить новый вопрос",
                           form_action=url_for('admin_bp.add_question_page'))


@admin_routes_bp.route('/questions/edit/<int:question_id>', methods=['GET', 'POST'])
def edit_question_page(question_id):
    if request.method == 'POST':
        question_text = request.form.get('question_text', '').strip()
        topic = request.form.get('topic', '').strip()

        new_answers_data = []
        try:
            correct_answer_index = int(request.form['correct_answer_index'])
        except (KeyError, ValueError):
            flash('Не выбран правильный ответ или передано некорректное значение.', 'error')
            # Загружаем вопрос снова для отображения в форме
            question_for_form = question_service.get_question_by_id_with_answers(question_id)
            if not question_for_form: return redirect(url_for('admin_bp.manage_questions_page'))
            return render_template('question_form.html',
                                   form_title="Редактировать вопрос",
                                   form_action=url_for('admin_bp.edit_question_page', question_id=question_id),
                                   question=question_for_form)

        answer_count_from_form = 0
        for i in range(4):
            ans_text_key = f'answer_text_{i}'
            if ans_text_key in request.form and request.form[ans_text_key].strip():
                answer_text = request.form[ans_text_key].strip()
                is_correct = 1 if i == correct_answer_index else 0
                new_answers_data.append({'text': answer_text, 'is_correct': is_correct})
                answer_count_from_form += 1

        if not question_text:
            flash('Текст вопроса не может быть пустым.', 'error')
        elif answer_count_from_form < 2:
            flash('Вопрос должен иметь как минимум два варианта ответа.', 'error')
        else:
            success = question_service.update_existing_question(question_id, question_text, topic, new_answers_data)
            if success:
                flash('Вопрос успешно обновлен!', 'success')
                return redirect(url_for('admin_bp.manage_questions_page'))
            else:
                flash('Ошибка при обновлении вопроса.', 'error')

        # При ошибке снова показываем форму с текущими (несохраненными) данными из формы
        # или перезагружаем из БД, если данные формы потеряны
        question_from_db = question_service.get_question_by_id_with_answers(question_id)
        # Можно попытаться восстановить введенные данные из request.form
        # Для простоты пока загрузим из БД
        return render_template('question_form.html',
                               form_title="Редактировать вопрос",
                               form_action=url_for('admin_bp.edit_question_page', question_id=question_id),
                               question=question_from_db)

    # GET-запрос
    question = question_service.get_question_by_id_with_answers(question_id)
    if not question:
        flash('Вопрос не найден.', 'error')
        return redirect(url_for('admin_bp.manage_questions_page'))

    return render_template('question_form.html',
                           form_title="Редактировать вопрос",
                           form_action=url_for('admin_bp.edit_question_page', question_id=question_id),
                           question=question)


@admin_routes_bp.route('/questions/delete/<int:question_id>', methods=['POST'])
def delete_question_action(question_id):
    success = question_service.delete_question_by_id(question_id)
    if success:
        flash('Вопрос успешно удален.', 'success')
    else:
        flash('Ошибка при удалении вопроса.', 'error')
    return redirect(url_for('admin_bp.manage_questions_page'))