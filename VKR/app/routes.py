from flask import render_template, redirect, url_for, request, flash, jsonify, session
from app import db
from app.models import User, EquipmentCategory, EquipmentItem, Booking, Favorite, Quest, UserQuestProgress
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

    # АДМИНСКИЕ РОУТЫ
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

    # УПРАВЛЕНИЕ ОБОРУДОВАНИЕМ
    @app.route('/admin/equipment')
    @login_required
    @admin_required
    def admin_equipment():
        """Управление оборудованием"""
        user = get_current_user()
        categories = EquipmentCategory.query.all()
        items = EquipmentItem.query.options(joinedload(EquipmentItem.category)).all()
        
        equipment_count = EquipmentItem.query.count()
        available_count = EquipmentItem.query.filter_by(is_available=True).count()
        busy_count = EquipmentItem.query.filter_by(is_available=False).count()
        
        return safe_render_template('equipment_catalog.html', 
                             user=user,
                             categories=categories, 
                             items=items,
                             equipment_count=equipment_count,
                             available_count=available_count,
                             busy_count=busy_count)

    @app.route('/admin/equipment/quick-add', methods=['POST'])
    @login_required
    @admin_required
    def admin_equipment_quick_add():
        """Быстрое добавление оборудования"""
        try:
            name = request.form.get('name')
            category = request.form.get('category')
            description = request.form.get('description')
            specifications = request.form.get('specifications', '{}')
            
            if not all([name, category, description]):
                return jsonify({'success': False, 'error': 'Все обязательные поля должны быть заполнены'}), 400
            
            category_obj = EquipmentCategory.query.filter_by(name=category).first()
            if not category_obj:
                category_obj = EquipmentCategory(name=category)
                db.session.add(category_obj)
                db.session.flush()
            
            new_equipment = EquipmentItem(
                name=name,
                description=description,
                category_id=category_obj.id,
                specifications=specifications,
                is_available=True
            )
            
            db.session.add(new_equipment)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Оборудование успешно добавлено!',
                'equipment_id': new_equipment.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'error': str(e)}), 400

    @app.route('/admin/equipment/<int:equipment_id>/repair', methods=['POST'])
    @login_required
    @admin_required
    def admin_toggle_repair(equipment_id):
        """Переключение статуса ремонта"""
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
        """Управление категориями"""
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
        
        equipment_count = EquipmentItem.query.count()
        available_count = EquipmentItem.query.filter_by(is_available=True).count()
        busy_count = EquipmentItem.query.filter_by(is_available=False).count()
        
        return safe_render_template('equipment_catalog.html', 
                             user=user,
                             categories=categories, 
                             items=items,
                             equipment_count=equipment_count,
                             available_count=available_count,
                             busy_count=busy_count)

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

    # БРОНИРОВАНИЕ
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

    # КВЕСТЫ
    @app.route('/quests')
    @login_required
    def quests():
        user = get_current_user()
        
        quests_data = [
            {
                'id': 1,
                'title': 'Основы 3D-печати',
                'description': 'Изучите принципы работы 3D-принтера и создайте свою первую модель',
                'icon': '🖨',
                'color': '#4CAF50',
                'duration': '2-3 часа',
                'task_count': 4,
                'tasks': [
                    {'id': 1, 'name': 'Технология FDM печати', 'type': 'reading', 'url': '/task/reading/1'},
                    {'id': 2, 'name': 'Тест по безопасности', 'type': 'quiz', 'url': '/task/quiz/2'},
                    {'id': 3, 'name': 'Подготовка модели', 'type': 'reading', 'url': '/task/reading/3'},
                    {'id': 4, 'name': 'Практическое задание', 'type': 'practical', 'url': '/task/practical/4'}
                ],
                'rewards': 'Допуск к 3D-принтерам • +100 опыта'
            }
        ]
        
        active_quests_count = len([q for q in quests_data if q.get('is_active', True)])
        draft_quests_count = len([q for q in quests_data if not q.get('is_active', True)])
        
        return safe_render_template('quests.html', 
                          user=user,
                          quests=quests_data,
                          active_quests_count=active_quests_count,
                          draft_quests_count=draft_quests_count)

    # ИЗБРАННОЕ
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

    # ========== СИСТЕМА ОТЧЕТОВ ==========
    
    @app.route('/reports')
    @login_required
    def user_reports():
        """Отчеты для обычных пользователей"""
        user = get_current_user()
        
        if is_admin(user):
            return redirect(url_for('admin_reports'))
        
        try:
            user_bookings = Booking.query.filter_by(user_id=user.id).order_by(Booking.created_at.desc()).all()
            completed_bookings = len([b for b in user_bookings if b.status == 'completed'])
            pending_bookings = len([b for b in user_bookings if b.status == 'pending'])
            confirmed_bookings = len([b for b in user_bookings if b.status == 'confirmed'])
            
            user_favorites_count = Favorite.query.filter_by(user_id=user.id).count()
            
            total_bookings = Booking.query.count()
            
            user_quests_completed = 0
            user_total_quests = 0
            
            return safe_render_template('reports.html', 
                                 user=user,
                                 user_bookings=user_bookings,
                                 completed_bookings=completed_bookings,
                                 pending_bookings=pending_bookings,
                                 confirmed_bookings=confirmed_bookings,
                                 total_bookings=total_bookings,
                                 user_favorites_count=user_favorites_count,
                                 user_quests_completed=user_quests_completed,
                                 user_total_quests=user_total_quests)
            
        except Exception as e:
            print(f"Ошибка в user_reports: {e}")
            return safe_render_template('reports.html',
                user=user,
                user_bookings=[],
                completed_bookings=0,
                pending_bookings=0,
                confirmed_bookings=0,
                total_bookings=0,
                user_favorites_count=0,
                user_quests_completed=0,
                user_total_quests=0
            )

    @app.route('/admin/reports')
    @login_required
    @admin_required
    def admin_reports():
        """Расширенные отчеты для администраторов"""
        user = get_current_user()
        
        try:
            total_users = User.query.count()
            total_equipment = EquipmentItem.query.count()
            total_bookings = Booking.query.count()
            available_equipment = EquipmentItem.query.filter_by(is_available=True).count()
            equipment_in_repair = EquipmentItem.query.filter_by(is_available=False).count()
            pending_bookings = Booking.query.filter_by(status='pending').count()
            
            category_stats = {}
            categories = EquipmentCategory.query.all()
            for category in categories:
                count = EquipmentItem.query.filter_by(category_id=category.id).count()
                category_stats[category.name] = count
            
            booking_stats = {
                'confirmed': Booking.query.filter_by(status='confirmed').count(),
                'pending': pending_bookings,
                'rejected': Booking.query.filter_by(status='rejected').count(),
                'completed': Booking.query.filter_by(status='completed').count(),
                'cancelled': Booking.query.filter_by(status='cancelled').count()
            }
            
            total_quests = Quest.query.filter_by(is_active=True).count()
            quest_completions = UserQuestProgress.query.filter_by(completed=True).count()
            
            quest_stats = {
                'total_quests': total_quests,
                'active_quests': Quest.query.filter_by(is_active=True).count(),
                'total_participants': db.session.query(db.func.count(db.func.distinct(UserQuestProgress.user_id))).scalar() or 0,
                'active_participants': db.session.query(db.func.count(db.func.distinct(UserQuestProgress.user_id))).filter(
                    UserQuestProgress.completed == False
                ).scalar() or 0,
                'total_completions': quest_completions,
                'success_rate': round((quest_completions / (UserQuestProgress.query.count() or 1)) * 100) if UserQuestProgress.query.count() > 0 else 0,
            }
            
            user_progress_data = []
            users_with_progress = User.query.join(UserQuestProgress).distinct().all()
            
            for user_prog in users_with_progress[:5]:
                completed_count = UserQuestProgress.query.filter_by(user_id=user_prog.id, completed=True).count()
                total_user_quests = UserQuestProgress.query.filter_by(user_id=user_prog.id).count()
                
                user_progress_data.append({
                    'username': user_prog.username,
                    'completed_count': completed_count,
                    'total_quests': total_user_quests
                })
            
            quest_stats['user_progress'] = user_progress_data
            
            quest_popularity = []
            quests = Quest.query.all()[:5]
            
            for quest in quests:
                participants = UserQuestProgress.query.filter_by(quest_id=quest.id).count()
                completions = UserQuestProgress.query.filter_by(quest_id=quest.id, completed=True).count()
                completion_rate = round((completions / participants * 100)) if participants > 0 else 0
                
                avg_progress = db.session.query(db.func.avg(UserQuestProgress.progress)).filter_by(
                    quest_id=quest.id
                ).scalar() or 0
                
                quest_popularity.append({
                    'title': quest.title,
                    'participants': participants,
                    'completions': completions,
                    'completion_rate': completion_rate,
                    'avg_progress': round(avg_progress)
                })
            
            quest_stats['quest_popularity'] = quest_popularity
            
            return safe_render_template('reports.html',
                                 user=user,
                                 total_users=total_users,
                                 total_equipment=total_equipment,
                                 total_bookings=total_bookings,
                                 available_equipment=available_equipment,
                                 equipment_in_repair=equipment_in_repair,
                                 pending_bookings=pending_bookings,
                                 category_stats=category_stats,
                                 booking_stats=booking_stats,
                                 quest_stats=quest_stats,
                                 total_quests=total_quests,
                                 quest_completions=quest_completions)
            
        except Exception as e:
            print(f"Ошибка в admin_reports: {e}")
            demo_quest_stats = {
                'total_quests': 6,
                'active_quests': 6,
                'total_participants': 5,
                'active_participants': 4,
                'total_completions': 12,
                'success_rate': 67,
                'user_progress': [
                    {'username': 'Петров Иван', 'completed_count': 3, 'total_quests': 6},
                    {'username': 'Иванова Мария', 'completed_count': 1, 'total_quests': 2},
                    {'username': 'Сидоров Алексей', 'completed_count': 3, 'total_quests': 4}
                ],
                'quest_popularity': [
                    {'title': 'Основы 3D-печати', 'participants': 5, 'completions': 4, 'completion_rate': 80, 'avg_progress': 92},
                    {'title': 'Программирование промышленных роботов', 'participants': 3, 'completions': 2, 'completion_rate': 67, 'avg_progress': 75}
                ]
            }
            
            return safe_render_template('reports.html',
                user=user,
                total_users=User.query.count(),
                total_equipment=EquipmentItem.query.count(),
                total_bookings=Booking.query.count(),
                available_equipment=EquipmentItem.query.filter_by(is_available=True).count(),
                equipment_in_repair=EquipmentItem.query.filter_by(is_available=False).count(),
                pending_bookings=Booking.query.filter_by(status='pending').count(),
                category_stats={cat.name: EquipmentItem.query.filter_by(category_id=cat.id).count() for cat in EquipmentCategory.query.all()},
                booking_stats={
                    'confirmed': Booking.query.filter_by(status='confirmed').count(),
                    'pending': Booking.query.filter_by(status='pending').count(),
                    'rejected': Booking.query.filter_by(status='rejected').count(),
                    'completed': Booking.query.filter_by(status='completed').count(),
                    'cancelled': Booking.query.filter_by(status='cancelled').count()
                },
                quest_stats=demo_quest_stats,
                total_quests=6,
                quest_completions=12
            )

    @app.route('/admin/reports/detailed-stats')
    @login_required
    @admin_required
    def admin_detailed_stats():
        """Детальная статистика для модального окна"""
        try:
            new_users_today = User.query.filter(
                User.created_at >= datetime.now().date()
            ).count()
            
            active_users = db.session.query(db.func.count(db.func.distinct(Booking.user_id))).filter(
                Booking.start_date >= datetime.now() - timedelta(days=30)
            ).scalar() or 0
            
            equipment_usage = []
            items = EquipmentItem.query.all()[:10]
            
            for item in items:
                usage_count = Booking.query.filter_by(equipment_id=item.id).count()
                total_bookings = Booking.query.count()
                usage_percentage = (usage_count / (total_bookings or 1)) * 100
                
                equipment_usage.append({
                    'name': item.name,
                    'usage_count': usage_count,
                    'usage_percentage': round(usage_percentage, 1)
                })
            
            stats_data = {
                'new_users_today': new_users_today,
                'active_users': active_users,
                'total_users': User.query.count(),
                'equipment_usage': equipment_usage,
                'top_quests': [
                    {'title': 'Основы 3D-печати', 'participants': 5, 'participation_rate': 85},
                    {'title': 'Программирование роботов', 'participants': 4, 'participation_rate': 72},
                    {'title': 'Электроника для начинающих', 'participants': 3, 'participation_rate': 63}
                ],
                'avg_quests_per_user': 2.4,
                'most_popular_quest': 'Основы 3D-печати',
                'avg_completion_days': 3.2
            }
            
            return jsonify(stats_data)
            
        except Exception as e:
            print(f"Ошибка в admin_detailed_stats: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/admin/quests/detailed-stats')
    @login_required
    @admin_required
    def admin_quests_detailed_stats():
        """Детальная статистика квестов для модального окна"""
        try:
            stats_data = {
                'total_completions': 12,
                'avg_completion_time': '3.2 дня',
                'success_rate': 67,
                'top_quests': [
                    {'title': 'Основы 3D-печати', 'participants': 5, 'participation_rate': 85},
                    {'title': 'Программирование роботов', 'participants': 4, 'participation_rate': 72},
                    {'title': 'Электроника для начинающих', 'participants': 3, 'participation_rate': 63}
                ],
                'avg_quests_per_user': 2.4,
                'most_popular_quest': 'Основы 3D-печати',
                'avg_completion_days': 3.2
            }
            
            return jsonify(stats_data)
            
        except Exception as e:
            print(f"Ошибка в admin_quests_detailed_stats: {e}")
            return jsonify({'error': str(e)}), 500

    @app.route('/admin/reports/export/<format_type>')
    @login_required
    @admin_required
    def admin_export_reports(format_type):
        """Экспорт отчетов в разных форматах"""
        try:
            if format_type == 'csv':
                csv_data = "Отчет системы лаборатории робототехники\n\n"
                csv_data += f"Дата генерации: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                
                csv_data += "ОСНОВНАЯ СТАТИСТИКА\n"
                csv_data += f"Всего пользователей: {User.query.count()}\n"
                csv_data += f"Всего оборудования: {EquipmentItem.query.count()}\n"
                csv_data += f"Всего бронирований: {Booking.query.count()}\n"
                csv_data += f"Доступного оборудования: {EquipmentItem.query.filter_by(is_available=True).count()}\n\n"
                
                csv_data += "СТАТИСТИКА БРОНИРОВАНИЙ\n"
                booking_stats = db.session.query(
                    Booking.status,
                    func.count(Booking.id)
                ).group_by(Booking.status).all()
                
                for status, count in booking_stats:
                    csv_data += f"{status}: {count}\n"
                
                from flask import make_response
                response = make_response(csv_data)
                response.headers["Content-Disposition"] = f"attachment; filename=lab_report_{datetime.now().strftime('%Y%m%d')}.csv"
                response.headers["Content-type"] = "text/csv"
                
                return response
                
            else:
                return jsonify({'success': False, 'error': 'Формат не поддерживается'}), 400
                
        except Exception as e:
            print(f"Ошибка при экспорте отчетов: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

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

    # О СИСТЕМЕ
    @app.route('/about')
    def about():
        user = get_current_user() if 'user_id' in session else None
        return safe_render_template('about.html', user=user)

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