from flask import Flask, g
import os
import datetime
from EngLes.test_generator_app import config
from EngLes.test_generator_app.models.database_manager import init_db_command, close_db_connection
import os


# Импорты блюпринтов будут добавлены позже, когда они будут созданы
REL_PATH = 'C:/EngLes/EngLes/templates'

def create_app(test_config=None):
    template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), REL_PATH)
    """Фабрика для создания экземпляра приложения Flask."""
    app = Flask(__name__,template_folder=template_folder, instance_relative_config=True)

    # Загрузка конфигурации
    if test_config is None:
        # Загрузка из config.py
        app.config.from_object(config)
    else:
        # Загрузка из переданной тестовой конфигурации
        app.config.from_mapping(test_config)

    # Убедимся, что папка instance существует (если используется instance_relative_config)
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Регистрация функции закрытия соединения с БД
    app.teardown_appcontext(close_db_connection)

    # Регистрация команды CLI для инициализации БД
    # Вызывать из терминала: flask init-db
    @app.cli.command('init-db')
    def init_db_cli_command():
        """Очищает существующие данные и создает новые таблицы."""
        init_db_command(app)
        # print('Initialized the database.') # Сообщение уже есть в init_db_command

    # Передача текущего года в шаблоны через g
    @app.before_request
    def before_request():
        g.year = datetime.date.today().year

    # --- Регистрация Blueprints ---
    # Blueprints будут импортированы и зарегистрированы здесь
    # Пример:
    from EngLes.test_generator_app.routes import admin_routes_bp, quiz_routes_bp  # Создадим эти файлы далее
    app.register_blueprint(admin_routes_bp, url_prefix='/admin')  # Маршруты админки будут /admin/...
    app.register_blueprint(quiz_routes_bp)  # Маршруты тестов будут корневыми /...

    # Простой маршрут для проверки, что приложение работает
    @app.route('/hello')
    def hello():
        return 'Hello, World! Your Quiz App is starting!'

    return app


# Если файл запускается напрямую (python app.py), а не через flask run
if __name__ == '__main__':
    app_instance = create_app()
    app_instance.run()  # debug будет взят из config.DEBUG