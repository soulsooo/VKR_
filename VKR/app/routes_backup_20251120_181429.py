from flask import render_template, redirect, url_for, request, flash, jsonify, session
from app import db
from app.models import User, EquipmentCategory, EquipmentItem, Booking, Favorite, Quest
from datetime import datetime, timedelta
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from functools import wraps
import os
import json

def init_routes(app):
    print("🎯 routes.py is being imported...")

    # КАСТОМНЫЕ ДЕКОРАТОРЫ
    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'error': 'Требуется авторизация'}), 401
                flash('Требуется авторизация', 'error')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function

    def admin_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash('Требуется авторизация', 'error')
                return redirect(url_for('login'))
            
            user = User.query.get(session['user_id'])
            if not user or user.role != 'admin':
                flash('Доступ запрещен. Требуются права администратора', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function

    def get_current_user():
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if not user:
                session.clear()
                return None
            return user
        return None

    # УНИВЕРСАЛЬНЫЕ ФУНКЦИИ ДЛЯ РОЛЕЙ
    def is_student(user):
        return user.role in ['student', 'user']

    def is_admin(user):
        return user.role == 'admin'

    # БЕЗОПАСНЫЙ RENDER_TEMPLATE
    def safe_render_template(template_name, **context):
        template_path = os.path.join(app.template_folder, template_name)
        if not os.path.exists(template_path):
            print(f"⚠️ Шаблон {template_name} не найден, используем index.html")
            return render_template('index.html', **context)
        return render_template(template_name, **context)

    # ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ДАННЫХ ДАШБОРДА
    def get_dashboard_data(user):
        if not user:
            return {}
            
        user_bookings_count = Booking.query.filter_by(user_id=user.id).filter(
            Booking.status.in_(['pending', 'confirmed'])
        ).count()
        
        completed_sessions = Booking.query.filter_by(
            user_id=user.id, 
            status='completed'
        ).count()
        
        user_favorites_count = Favorite.query.filter_by(user_id=user.id).count()
        
        recent_bookings = Booking.query.filter_by(user_id=user.id).options(
            joinedload(Booking.equipment)
        ).order_by(Booking.created_at.desc()).limit(5).all()
        
        return {
            'user_bookings_count': user_bookings_count,
            'completed_sessions': completed_sessions,
            'user_favorites_count': user_favorites_count,
            'recent_bookings': recent_bookings
        }

    # АУТЕНТИФИКАЦИЯ
    @app.route('/')
    def index():
        if 'user_id' in session:
            user = get_current_user()
            if user:
                return redirect(url_for('dashboard'))
            else:
                session.clear()
        return safe_render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
                if 'user_id' in session:
            user = get_current_user()
            if user:
                flash('Вы уже авторизованы', 'info')
                if is_admin(user):
                    session['user_id'] = user.id
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
if request.method == 'POST':
            username = request.form.get('username')
            password = request.form.get('password')
            
            user = User.query.filter_by(username=username).first()
            
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['username'] = user.username
                session['user_role'] = user.role
                session.permanent = True
                
                flash('Успешный вход!', 'success')
                
                if is_admin(user):
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Неверный логин или пароль', 'error')
        
        return safe_render_template('login.html')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
            
        if request.method == 'POST':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            if User.query.filter_by(username=username).first():
                flash('Пользователь с таким именем уже существует', 'error')
                return safe_render_template('login.html')
                
            user = User(
                username=username,
                email=email,
                role='user'
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Регистрация успешна! Теперь вы можете войти.', 'success')
            return redirect(url_for('login'))
        
        return safe_render_template('login.html')

    @app.route('/logout')
    def logout():
        username = session.get('username', 'Неизвестный')
        session.clear()
        flash('Вы вышли из системы', 'info')
        return redirect(url_for('index'))

    # ОСНОВНЫЕ РОУТЫ
    @app.route('/dashboard')
    @login_required
    def dashboard():
        user = get_current_user()
        
        if is_admin(user):
            return redirect(url_for('admin_dashboard'))
        else:
            dashboard_data = get_dashboard_data(user)
            return safe_render_template('dashboard.html', 
                                    user=user,
                                    user_bookings_count=dashboard_data['user_bookings_count'],
                                    completed_sessions=dashboard_data['completed_sessions'],
                                    user_favorites_count=dashboard_data['user_favorites_count'],
                                    recent_bookings=dashboard_data['recent_bookings'])

    # ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ
    @app.route('/profile')
    @login_required
    def profile():
        user = get_current_user()
        
        if is_admin(user):
            users_count = User.query.count()
            equipment_count = EquipmentItem.query.count()
            categories_count = EquipmentCategory.query.count()
            active_bookings = Booking.query.filter(Booking.status.in_(['pending', 'confirmed'])).count()
            equipment_in_repair = EquipmentItem.query.filter_by(is_available=False).count()
            
            return safe_render_template('admin_profile.html',
                                    user=user,
                                    users_count=users_count,
                                    equipment_count=equipment_count,
                                    categories_count=categories_count,
                                    active_bookings=active_bookings,
                                    equipment_in_repair=equipment_in_repair,
                                    total_bookings=Booking.query.count())
        else:
            user_bookings = Booking.query.filter_by(user_id=user.id).options(
                joinedload(Booking.equipment)
            ).order_by(Booking.created_at.desc()).all()
            
            user_favorites = Favorite.query.filter_by(user_id=user.id).options(
                joinedload(Favorite.equipment)
            ).all()
            
            return safe_render_template('profile.html', 
                                    user=user,
                                    user_bookings=user_bookings,
                                    user_favorites=user_favorites)

    # АДМИНСКИЕ РОУТЫ - ПЕРЕНЕСЕМ ИХ ВЫШЕ, ЧТОБЫ ИЗБЕЖАТЬ ОШИБОК

    # ГЛАВНАЯ АДМИН-ПАНЕЛЬ
    @app.route('/admin')
    @login_required
    @admin_required
    def admin_dashboard():
        user = get_current_user()
        
        total_users = User.query.count()
        total_equipment = EquipmentItem.query.count()
        total_bookings = Booking.query.count()
        available_equipment = EquipmentItem.query.filter_by(is_available=True).count()
        pending_bookings = Booking.query.filter_by(status='pending').count()
        equipment_in_repair = EquipmentItem.query.filter_by(is_available=False).count()
        
        recent_bookings = Booking.query.options(
            joinedload(Booking.user),
            joinedload(Booking.equipment)
        ).order_by(Booking.created_at.desc()).limit(10).all()
        
        return safe_render_template('admin_dashboard.html',
                                user=user,
                                total_users=total_users,
                                total_equipment=total_equipment,
                                total_bookings=total_bookings,
                                available_equipment=available_equipment,
                                pending_bookings=pending_bookings,
                                equipment_in_repair=equipment_in_repair,
                                recent_bookings=recent_bookings)

    # ДОБАВЛЕНИЕ НОВОГО ОБОРУДОВАНИЯ - ПЕРВЫМ ДЕЛАЕМ ЭТОТ МАРШРУТ
    @app.route('/admin/equipment/add', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def admin_add_equipment():
        user = get_current_user()
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            category_id = request.form.get('category_id')
            image_url = request.form.get('image_url')
            specifications = request.form.get('specifications')
            
            if not all([name, description, category_id]):
                flash('Все обязательные поля должны быть заполнены', 'error')
                return redirect(url_for('admin_add_equipment'))
            
            try:
                new_equipment = EquipmentItem(
                    name=name,
                    description=description,
                    category_id=category_id,
                    image_url=image_url,
                    specifications=specifications,
                    is_available=True
                )
                
                db.session.add(new_equipment)
                db.session.commit()
                
                flash('Оборудование успешно добавлено!', 'success')
                return redirect(url_for('admin_equipment'))
                
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при добавлении оборудования: {str(e)}', 'error')
                return redirect(url_for('admin_add_equipment'))
        
        categories = EquipmentCategory.query.all()
        return safe_render_template('admin_add_equipment.html',
                                user=user,
                                categories=categories)

    # УПРАВЛЕНИЕ ОБОРУДОВАНИЕМ
    @app.route('/admin/equipment')
    @login_required
    @admin_required
    def admin_equipment():
        user = get_current_user()
        categories = EquipmentCategory.query.all()
        items = EquipmentItem.query.options(joinedload(EquipmentItem.category)).all()
        
        return safe_render_template('admin_equipment.html', 
                                user=user,
                                categories=categories, 
                                items=items)

    # УДАЛЕНИЕ ОБОРУДОВАНИЯ
    @app.route('/admin/equipment/<int:equipment_id>/delete', methods=['POST'])
    @login_required
    @admin_required
    def admin_delete_equipment(equipment_id):
        try:
            equipment = EquipmentItem.query.get(equipment_id)
            if not equipment:
                flash('Оборудование не найдено', 'error')
                return redirect(url_for('admin_equipment'))
            
            active_bookings = Booking.query.filter_by(
                equipment_id=equipment_id,
                status='confirmed'
            ).first()
            
            if active_bookings:
                flash('Нельзя удалить оборудование с активными бронированиями', 'error')
                return redirect(url_for('admin_equipment'))
            
            db.session.delete(equipment)
            db.session.commit()
            
            flash('Оборудование успешно удалено!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при удалении оборудования: {str(e)}', 'error')
        
        return redirect(url_for('admin_equipment'))

    # ОТПРАВКА НА РЕМОНТ / ВОЗВРАТ ИЗ РЕМОНТА
    @app.route('/admin/equipment/<int:equipment_id>/repair', methods=['POST'])
    @login_required
    @admin_required
    def admin_toggle_repair(equipment_id):
        try:
            equipment = EquipmentItem.query.get(equipment_id)
            if not equipment:
                flash('Оборудование не найдено', 'error')
                return redirect(url_for('admin_equipment'))
            
            equipment.is_available = not equipment.is_available
            db.session.commit()
            
            status = "отправлено на ремонт" if not equipment.is_available else "возвращено в работу"
            flash(f'Оборудование "{equipment.name}" {status}!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при изменении статуса оборудования: {str(e)}', 'error')
        
        return redirect(url_for('admin_equipment'))

    @app.route('/admin/categories')
    @login_required
    @admin_required
    def admin_categories():
        user = get_current_user()
        categories = EquipmentCategory.query.all()
        
        return safe_render_template('admin_categories.html',
                                user=user,
                                categories=categories)

    # УПРАВЛЕНИЕ БРОНИРОВАНИЯМИ
    @app.route('/admin/bookings')
    @login_required
    @admin_required
    def admin_bookings():
        user = get_current_user()
        bookings = Booking.query.options(
            joinedload(Booking.user), 
            joinedload(Booking.equipment)
        ).order_by(Booking.created_at.desc()).all()
        
        return safe_render_template('admin_bookings.html',
                                user=user,
                                bookings=bookings)

    # ПОДТВЕРЖДЕНИЕ БРОНИРОВАНИЯ
    @app.route('/admin/bookings/<int:booking_id>/confirm', methods=['POST'])
    @login_required
    @admin_required
    def admin_confirm_booking(booking_id):
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                flash('Бронирование не найдено', 'error')
                return redirect(url_for('admin_bookings'))
            
            booking.status = 'confirmed'
            db.session.commit()
            
            flash('Бронирование подтверждено!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при подтверждении бронирования: {str(e)}', 'error')
        
        return redirect(url_for('admin_bookings'))

    # ОТКЛОНЕНИЕ БРОНИРОВАНИЯ
    @app.route('/admin/bookings/<int:booking_id>/reject', methods=['POST'])
    @login_required
    @admin_required
    def admin_reject_booking(booking_id):
        try:
            booking = Booking.query.get(booking_id)
            if not booking:
                flash('Бронирование не найдено', 'error')
                return redirect(url_for('admin_bookings'))
            
            booking.status = 'rejected'
            db.session.commit()
            
            flash('Бронирование отклонено!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка при отклонении бронирования: {str(e)}', 'error')
        
        return redirect(url_for('admin_bookings'))

    # ОБОРУДОВАНИЕ И КАТЕГОРИИ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ
    @app.route('/equipment')
    @login_required
    def equipment():
        user = get_current_user()
        categories = EquipmentCategory.query.all()
        items = EquipmentItem.query.all()
        
        return safe_render_template('equipment_catalog.html', 
                                user=user,
                                categories=categories, 
                                items=items)

    # ДЕТАЛЬНОЕ ОПИСАНИЕ ОБОРУДОВАНИЯ
    @app.route('/equipment/<int:equipment_id>')
    @login_required
    def equipment_detail(equipment_id):
        user = get_current_user()
        item = EquipmentItem.query.options(joinedload(EquipmentItem.category)).get(equipment_id)
        
        if not item:
            flash('Оборудование не найдено', 'error')
            return redirect(url_for('equipment'))
        
        is_favorited = False
        if not is_admin(user):
            is_favorited = Favorite.query.filter_by(
                user_id=user.id, 
                equipment_id=equipment_id
            ).first() is not None
        
        specifications = {}
        if item.specifications:
            try:
                if isinstance(item.specifications, str):
                    specifications = json.loads(item.specifications)
                else:
                    specifications = item.specifications
            except:
                specifications = {}
        
        return safe_render_template('equipment_detail.html', 
                                user=user,
                                item=item,
                                is_favorited=is_favorited,
                                specifications=specifications)

    @app.route('/category/<int:category_id>')
    @login_required
    def category_detail(category_id):
        user = get_current_user()
        category = EquipmentCategory.query.get(category_id)
        
        if not category:
            flash('Категория не найдена', 'error')
            return redirect(url_for('equipment'))
        
        items = EquipmentItem.query.filter_by(category_id=category_id).all()
        
        return safe_render_template('category_detail.html',
                                user=user,
                                category=category,
                                items=items)

    # БРОНИРОВАНИЕ - РАБОЧАЯ ВЕРСИЯ
    @app.route('/booking', methods=['GET', 'POST'])
    @login_required
    def booking():
        user = get_current_user()
        
        if is_admin(user):
            flash('Администраторы не могут создавать бронирования', 'info')
            return redirect(url_for('admin_bookings'))
        
        if request.method == 'POST':
            equipment_id = request.form.get('equipment_id')
            start_date_str = request.form.get('start_date')
            end_date_str = request.form.get('end_date')
            purpose = request.form.get('purpose')
            
            if not all([equipment_id, start_date_str, end_date_str, purpose]):
                flash('Все поля обязательны для заполнения', 'error')
                return redirect(url_for('booking'))
            
            try:
                start_date = datetime.fromisoformat(start_date_str)
                end_date = datetime.fromisoformat(end_date_str)
                
                if start_date < datetime.now():
                    flash('Нельзя бронировать оборудование на прошедшую дату', 'error')
                    return redirect(url_for('booking'))
                
                if end_date <= start_date:
                    flash('Дата окончания должна быть позже даты начала', 'error')
                    return redirect(url_for('booking'))
                
                equipment = EquipmentItem.query.get(equipment_id)
                if not equipment:
                    flash('Оборудование не найдено', 'error')
                    return redirect(url_for('booking'))
                
                if not equipment.is_available:
                    flash('Это оборудование временно недоступно', 'error')
                    return redirect(url_for('booking'))
                
                conflicting_booking = Booking.query.filter(
                    Booking.equipment_id == equipment_id,
                    Booking.status.in_(['pending', 'confirmed']),
                    or_(
                        Booking.start_date.between(start_date, end_date),
                        Booking.end_date.between(start_date, end_date),
                        (Booking.start_date <= start_date) & (Booking.end_date >= end_date)
                    )
                ).first()
                
                if conflicting_booking:
                    flash('Это оборудование уже забронировано на выбранные даты', 'error')
                    return redirect(url_for('booking'))
                
                new_booking = Booking(
                    user_id=user.id,
                    equipment_id=equipment_id,
                    start_date=start_date,
                    end_date=end_date,
                    purpose=purpose,
                    status='pending'
                )
                
                db.session.add(new_booking)
                db.session.commit()
                
                flash('Запрос на бронирование отправлен на модерацию!', 'success')
                return redirect(url_for('profile'))
                
            except ValueError:
                flash('Неверный формат даты', 'error')
                return redirect(url_for('booking'))
            except Exception as e:
                db.session.rollback()
                flash(f'Ошибка при создании бронирования: {str(e)}', 'error')
                return redirect(url_for('booking'))
        
        items = EquipmentItem.query.filter_by(is_available=True).all()
        return safe_render_template('booking.html', 
                                user=user,
                                items=items)

    # КВЕСТЫ - ИСПРАВЛЕННАЯ ВЕРСИЯ
    @app.route('/quests')
    @login_required
    def quests():
        user = get_current_user()
        
        if is_admin(user):
            flash('Администраторы не могут проходить квесты', 'info')
            return redirect(url_for('admin_dashboard'))
        
        quests = Quest.query.filter_by(is_active=True).all()
        print(f"🔍 QUESTS: Found {len(quests)} active quests")
        
        return safe_render_template('quests.html', 
                                user=user,
                                quests=quests)

    @app.route('/quest/<int:quest_id>')
    @login_required
    def quest_detail(quest_id):
        user = get_current_user()
        
        if is_admin(user):
            flash('Администраторы не могут проходить квесты', 'info')
            return redirect(url_for('admin_dashboard'))
        
        quest = Quest.query.get(quest_id)
        if not quest:
            flash('Квест не найден', 'error')
            return redirect(url_for('quests'))
        
        return safe_render_template('quest_detail.html', 
                                user=user, 
                                quest=quest)

    # ЗАДАНИЯ КВЕСТОВ
    @app.route('/task/reading/<int:task_id>')
    @login_required
    def task_reading(task_id):
        user = get_current_user()
        if is_admin(user):
            flash('Администраторы не могут проходить квесты', 'info')
            return redirect(url_for('admin_dashboard'))
        return safe_render_template('task1_reading.html', user=user, task_id=task_id)

    @app.route('/task/quiz/<int:task_id>')
    @login_required
    def task_quiz(task_id):
        user = get_current_user()
        if is_admin(user):
            flash('Администраторы не могут проходить квесты', 'info')
            return redirect(url_for('admin_dashboard'))
        return safe_render_template('task2_quiz.html', user=user, task_id=task_id)

    @app.route('/task/practical/<int:task_id>')
    @login_required
    def task_practical(task_id):
        user = get_current_user()
        if is_admin(user):
            flash('Администраторы не могут проходить квесты', 'info')
            return redirect(url_for('admin_dashboard'))
        return safe_render_template('task4_practical.html', user=user, task_id=task_id)

    # ИЗБРАННОЕ - РАБОЧАЯ ВЕРСИЯ
    @app.route('/favorites')
    @login_required
    def favorites():
        user = get_current_user()
        
        if is_admin(user):
            flash('Эта функция недоступна для администраторов', 'info')
            return redirect(url_for('admin_dashboard'))
        
        user_favorites = Favorite.query.filter_by(user_id=user.id).options(
            joinedload(Favorite.equipment).joinedload(EquipmentItem.category)
        ).all()
        
        return safe_render_template('favorites.html', 
                                user=user,
                                favorites=user_favorites)

    # ОТЧЕТНОСТЬ
    @app.route('/reports')
    @login_required
    def reports():
    # ОТЛАДКА СЕССИИ
    print(f"🔐 ДОСТУП К ОТЧЕТАМ: user_id в сессии = {session.get('user_id')}")
    current_user = get_current_user()
    print(f"🔐 Текущий пользователь: {current_user.username if current_user else 'НЕТ'}")
    if not current_user:
        print("🔐 ПЕРЕАДРЕСАЦИЯ НА ЛОГИН")
        user = get_current_user()
        
        if not is_admin(user):
            user_bookings = Booking.query.filter_by(user_id=user.id).all()
            return safe_render_template('reports.html', 
                                    user=user,
                                    user_bookings=user_bookings)
        else:
            return safe_render_template('admin_reports.html', user=user)

    # О СИСТЕМЕ
    @app.route('/about')
    def about():
        user = get_current_user() if 'user_id' in session else None
        return safe_render_template('about.html', user=user)

    # API РОУТЫ

    @app.route('/api/equipment')
    @login_required
    def api_equipment():
        try:
            items = EquipmentItem.query.options(joinedload(EquipmentItem.category)).all()
            equipment_list = []
            for item in items:
                equipment_list.append({
                    'id': item.id,
                    'name': item.name,
                    'description': item.description,
                    'image_url': item.image_url,
                    'is_available': item.is_available,
                    'category_id': item.category_id,
                    'category_name': item.category.name if item.category else 'Без категории'
                })
            return jsonify(equipment_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/equipment/<int:equipment_id>')
    @login_required
    def api_equipment_detail(equipment_id):
        try:
            item = EquipmentItem.query.options(joinedload(EquipmentItem.category)).get(equipment_id)
            if not item:
                return jsonify({'error': 'Оборудование не найдено'}), 404
            
            specifications = {}
            if item.specifications:
                try:
                    if isinstance(item.specifications, str):
                        specifications = json.loads(item.specifications)
                    else:
                        specifications = item.specifications
                except:
                    specifications = {}
            
            return jsonify({
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'image_url': item.image_url,
                'is_available': item.is_available,
                'category_id': item.category_id,
                'category_name': item.category.name if item.category else 'Без категории',
                'specifications': specifications
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    # API ДЛЯ ИЗБРАННОГО
    @app.route('/api/user/favorites')
    @login_required
    def api_user_favorites():
        try:
            user = get_current_user()
            
            if is_admin(user):
                return jsonify([])
            
            favorites = Favorite.query.filter_by(user_id=user.id).options(
                joinedload(Favorite.equipment).joinedload(EquipmentItem.category)
            ).all()
            
            favorites_list = []
            for fav in favorites:
                if fav.equipment:
                    favorites_list.append({
                        'id': fav.equipment.id,
                        'name': fav.equipment.name,
                        'description': fav.equipment.description,
                        'image_url': fav.equipment.image_url,
                        'is_available': fav.equipment.is_available,
                        'category_name': fav.equipment.category.name if fav.equipment.category else 'Без категории'
                    })
            
            return jsonify(favorites_list)
        except Exception as e:
            print(f"Error in api_user_favorites: {e}")
            return jsonify([])

    @app.route('/api/equipment/<int:equipment_id>/favorite', methods=['POST'])
    @login_required
    def toggle_favorite(equipment_id):
        try:
            user = get_current_user()
            
            if is_admin(user):
                return jsonify({'success': False, 'error': 'Администраторы не могут использовать избранное'})
            
            equipment = EquipmentItem.query.get(equipment_id)
            if not equipment:
                return jsonify({'success': False, 'error': 'Оборудование не найдено'})
            
            existing_favorite = Favorite.query.filter_by(
                user_id=user.id, 
                equipment_id=equipment_id
            ).first()
            
            if existing_favorite:
                db.session.delete(existing_favorite)
                db.session.commit()
                return jsonify({
                    'success': True, 
                    'favorited': False,
                    'message': 'Удалено из избранного'
                })
            else:
                new_favorite = Favorite(
                    user_id=user.id,
                    equipment_id=equipment_id
                )
                db.session.add(new_favorite)
                db.session.commit()
                return jsonify({
                    'success': True, 
                    'favorited': True,
                    'message': 'Добавлено в избранное'
                })
                
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    # API ДЛЯ БРОНИРОВАНИЙ
    @app.route('/api/bookings')
    @login_required
    def api_bookings():
        try:
            user = get_current_user()
            
            if is_admin(user):
                bookings = Booking.query.options(
                    joinedload(Booking.user), 
                    joinedload(Booking.equipment)
                ).all()
            else:
                bookings = Booking.query.filter_by(user_id=user.id).options(
                    joinedload(Booking.equipment)
                ).all()
            
            bookings_list = []
            for booking in bookings:
                bookings_list.append({
                    'id': booking.id,
                    'equipment_name': booking.equipment.name if booking.equipment else 'Неизвестно',
                    'start_date': booking.start_date.isoformat() if booking.start_date else None,
                    'end_date': booking.end_date.isoformat() if booking.end_date else None,
                    'status': booking.status,
                    'purpose': booking.purpose
                })
            
            return jsonify(bookings_list)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/bookings', methods=['POST'])
    @login_required
    def create_booking():
        try:
            user = get_current_user()
            
            if is_admin(user):
                return jsonify({'success': False, 'error': 'Администраторы не могут создавать бронирования'})
            
            data = request.get_json()
            equipment_id = data.get('equipment_id')
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            purpose = data.get('purpose')
            
            if not all([equipment_id, start_date, end_date, purpose]):
                return jsonify({'success': False, 'error': 'Все поля обязательны'})
            
            equipment = EquipmentItem.query.get(equipment_id)
            if not equipment:
                return jsonify({'success': False, 'error': 'Оборудование не найдено'})
            
            if not equipment.is_available:
                return jsonify({'success': False, 'error': 'Оборудование недоступно для бронирования'})
            
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError as e:
                return jsonify({'success': False, 'error': 'Неверный формат даты'})
            
            new_booking = Booking(
                user_id=user.id,
                equipment_id=equipment_id,
                start_date=start_date,
                end_date=end_date,
                purpose=purpose,
                status='pending'
            )
            
            db.session.add(new_booking)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Бронирование создано успешно',
                'booking_id': new_booking.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 500

    # API ДЛЯ ОТЧЕТОВ
    @app.route('/api/reports')
    @login_required
    @admin_required
    def api_reports():
        try:
            total_users = User.query.count()
            total_equipment = EquipmentItem.query.count()
            total_bookings = Booking.query.count()
            available_equipment = EquipmentItem.query.filter_by(is_available=True).count()
            
            booking_stats = db.session.query(
                Booking.status,
                func.count(Booking.id)
            ).group_by(Booking.status).all()
            
            category_stats = db.session.query(
                EquipmentCategory.name,
                func.count(EquipmentItem.id)
            ).join(EquipmentItem).group_by(EquipmentCategory.name).all()
            
            reports_data = {
                'summary': {
                    'total_users': total_users,
                    'total_equipment': total_equipment,
                    'total_bookings': total_bookings,
                    'available_equipment': available_equipment
                },
                'booking_stats': {
                    status: count for status, count in booking_stats
                },
                'category_stats': {
                    name: count for name, count in category_stats
                }
            }
            
            return jsonify(reports_data)
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/user/profile')
    @login_required
    def api_user_profile():
        user = get_current_user()
        return jsonify({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role
        })

    # API ДЛЯ ДИНАМИЧЕСКИХ ОТЧЕТОВ ПОЛЬЗОВАТЕЛЯ
    @app.route('/api/user/reports')
    @login_required
    def api_user_reports():
        user = get_current_user()
        
        user_bookings = Booking.query.filter_by(user_id=user.id).all()
        completed_bookings = [b for b in user_bookings if b.status == 'completed']
        pending_bookings = [b for b in user_bookings if b.status == 'pending']
        confirmed_bookings = [b for b in user_bookings if b.status == 'confirmed']
        
        user_favorites_count = Favorite.query.filter_by(user_id=user.id).count()
        
        reports_data = {
            'total_bookings': len(user_bookings),
            'completed_bookings': len(completed_bookings),
            'pending_bookings': len(pending_bookings),
            'confirmed_bookings': len(confirmed_bookings),
            'favorites_count': user_favorites_count,
            'success_rate': round((len(completed_bookings) / len(user_bookings) * 100) if user_bookings else 0, 2)
        }
        
        return jsonify(reports_data)

    # API ДЛЯ СТАТИСТИКИ
    @app.route('/api/stats')
    @login_required
    def api_stats():
        user = get_current_user()
        stats = {
            'total_users': User.query.count(),
            'total_equipment': EquipmentItem.query.count(),
            'total_bookings': Booking.query.count(),
            'available_equipment': EquipmentItem.query.filter_by(is_available=True).count()
        }
        return jsonify(stats)

    # ОБРАБОТЧИКИ ОШИБОК
    @app.errorhandler(404)
    def not_found_error(error):
        user = get_current_user() if 'user_id' in session else None
        return safe_render_template('404.html', user=user), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        user = get_current_user() if 'user_id' in session else None
        return safe_render_template('500.html', user=user), 500

    # КОНТЕКСТНЫЙ ПРОЦЕССОР
    @app.context_processor
    def inject_user():
        user = None
        if 'user_id' in session:
            user = User.query.get(session['user_id'])
            if not user:
                session.clear()
        return dict(user=user)

    print("✅ Все маршруты успешно загружены!")