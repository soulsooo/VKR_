# app/__init__.py
import os
from flask import Flask, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
import time

db = SQLAlchemy()

print("🔄 app/__init__.py загружен!")

def create_app():
    app = Flask(__name__)
    print("✅ 1. Flask app created")
    
    # Конфигурация
    app.config['SECRET_KEY'] = 'your-very-secret-key-here-12345'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:JociTfcnMlAxNqPaqYYixBwQvEZiqpwR@switchyard.proxy.rlwy.net:17344/railway'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # КРИТИЧЕСКИ ВАЖНО: Настройки сессии
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SECURE'] = False  # False для разработки
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    
    # Автообновление шаблонов
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
    app.config['DEBUG'] = True
    
    # Инициализация расширений
    db.init_app(app)
    print("✅ 2. Extensions initialized")
    
    # ⚡️ РАДИКАЛЬНОЕ ОТКЛЮЧЕНИЕ КЭШИРОВАНИЯ ДЛЯ ВСЕХ ЗАПРОСОВ
    @app.after_request
    def add_no_cache_headers(response):
        """Полное отключение кэширования для всех типов запросов"""
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response
    
    # КРИТИЧЕСКИ ВАЖНО: Делаем сессию постоянной
    @app.before_request
    def make_session_permanent():
        session.permanent = True
        app.permanent_session_lifetime = timedelta(hours=24)
    
    # Глобальная переменная для версионирования статических файлов
    @app.context_processor
    def inject_version():
        """Добавляет версию для обхода кэша статических файлов"""
        return dict(
            version=str(int(time.time())),
            cache_buster=str(int(time.time()))
        )
    
    # Переопределение статической папки с версионированием
    @app.route('/static/<path:filename>')
    def custom_static(filename):
        """Статические файлы с параметром версии"""
        cache_buster = str(int(time.time()))
        response = send_from_directory(app.static_folder, filename)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    
    # Регистрируем роуты
    try:
        from app.routes import init_routes
        init_routes(app)
        print("✅ 3. Routes registered successfully")
    except Exception as e:
        print(f"❌ ERROR registering routes: {e}")
        import traceback
        traceback.print_exc()
        return app
    
    # Роут для API.JS с отключенным кэшем
    @app.route('/js/api.js')
    def serve_api_js():
        response = send_from_directory('static/js', 'api.js')
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response
    
    # Создаем таблицы
    with app.app_context():
        db.create_all()
        print("✅ 4. Database tables created/checked")
        
        # Проверяем есть ли пользователи, создаем тестовых если нет
        from app.models import User
        try:
            user_count = User.query.count()
            if user_count == 0:
                # Создаем администратора
                admin = User(username='admin', email='admin@lab.ru', role='admin')
                admin.set_password('admin123')
                db.session.add(admin)
                
                # Создаем обычного пользователя
                user = User(username='user', email='user@lab.ru', role='user')
                user.set_password('user123')
                db.session.add(user)
                
                # Создаем студента
                student = User(username='student', email='student@lab.ru', role='student')
                student.set_password('student123')
                db.session.add(student)
                
                db.session.commit()
                print("✅ Тестовые пользователи созданы")
                print("   👤 admin / admin123")
                print("   👤 user / user123") 
                print("   👤 student / student123")
            else:
                print(f"✅ В базе уже есть {user_count} пользователей")
                
        except Exception as e:
            print(f"⚠️ Ошибка при создании пользователей: {e}")
            db.session.rollback()
    
    print("✅ 5. App creation completed successfully")
    print("🔥 РАДИКАЛЬНОЕ ОТКЛЮЧЕНИЕ КЭША АКТИВИРОВАНО")
    print("🔐 НАСТРОЙКИ СЕССИИ АКТИВИРОВАНЫ")
    print("🚫 FLASK-LOGIN ОТКЛЮЧЕН - используется кастомная аутентификация")
    return app