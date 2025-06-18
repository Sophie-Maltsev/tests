import os

# Базовая директория проекта
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Конфигурация базы данных
DATABASE_NAME = 'quiz_database.db'
DATABASE_PATH = os.path.join(BASE_DIR, 'database', DATABASE_NAME)  # Путь к БД внутри папки database

# Секретный ключ для Flask сессий и flash сообщений
# ВАЖНО: Замените этот ключ на свой собственный, случайный и сложный!
SECRET_KEY = 'your_very_secret_and_unique_key_for_this_project_change_it_now'

# Режим отладки (True для разработки, False для продакшена)
DEBUG = True