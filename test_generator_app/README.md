    # Прототип приложения для генерации тестов

    Это прототип веб-приложения на Flask для создания, генерации и прохождения тестов с автоматической проверкой.

    ## Структура проекта

    - `app.py`: Точка входа и фабрика приложения Flask.
    - `config.py`: Конфигурационные параметры.
    - `database/`: Директория для файла базы данных SQLite.
    - `models/`: Модули для работы с базой данных (`database_manager.py`).
    - `routes/`: Blueprints для обработки HTTP-маршрутов (`admin_routes.py`, `quiz_routes.py`).
    - `services/`: Модули с бизнес-логикой (`question_service.py`, `quiz_service.py`).
    - `static/`: Статические файлы (CSS, JavaScript).
    - `templates/`: HTML-шаблоны Jinja2.
    - `requirements.txt`: Зависимости Python.

    ## Установка и запуск

    1.  **Клонировать репозиторий (если есть) или создать файлы по структуре.**
    2.  **Создать виртуальное окружение (рекомендуется):**
```bash
        python -m venv venv
        source venv/bin/activate  # Linux/macOS
        # venv\Scripts\activate    # Windows