from app import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

class User(UserMixin, db.Model):
    """Модель пользователя"""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='student', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Связи
    bookings = db.relationship('Booking', backref='user', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        """Установка хеша пароля"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def is_admin(self):
        """Проверка является ли пользователь администратором"""
        return self.role == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'


class EquipmentCategory(db.Model):
    """Модель категории оборудования"""
    __tablename__ = 'equipment_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text)
    # slug временно удален - его нет в базе
    # slug = db.Column(db.String(100), unique=True, nullable=True)
    
    # Связи
    items = db.relationship('EquipmentItem', backref='category', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'items_count': len(self.items) if self.items else 0
        }
    
    def __repr__(self):
        return f'<EquipmentCategory {self.name}>'


class EquipmentItem(db.Model):
    """Модель единицы оборудования"""
    __tablename__ = 'equipment_item'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    specifications = db.Column(db.Text)
    requirements = db.Column(db.Text)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('equipment_category.id'), nullable=False)
    
    # Временные поля (закомментированы - их нет в базе)
    # usage_instructions = db.Column(db.Text)
    # created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    bookings = db.relationship('Booking', backref='equipment', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='equipment', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'image_url': self.image_url,
            'specifications': self.specifications,
            'requirements': self.requirements,
            'is_available': self.is_available,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else 'Без категории',
            'active_bookings': len([b for b in self.bookings if b.status in ['pending', 'confirmed']]) if self.bookings else 0
        }
    
    def get_status(self):
        """Получить статус оборудования"""
        if not self.is_available:
            return 'maintenance'
        
        active_bookings = [b for b in self.bookings if b.status in ['pending', 'confirmed']]
        if active_bookings:
            return 'busy'
        
        return 'available'
    
    def can_be_booked(self):
        """Можно ли забронировать оборудование"""
        return self.is_available and self.get_status() == 'available'
    
    def __repr__(self):
        return f'<EquipmentItem {self.name}>'


class Booking(db.Model):
    """Модель бронирования оборудования"""
    __tablename__ = 'booking'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment_item.id'), nullable=False, index=True)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    purpose = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, confirmed, rejected, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Временное поле (закомментировано - его нет в базе)
    # updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else 'Unknown',
            'equipment_id': self.equipment_id,
            'equipment_name': self.equipment.name if self.equipment else 'Unknown',
            'equipment_image': self.equipment.image_url if self.equipment else None,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'purpose': self.purpose,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'duration_hours': int((self.end_date - self.start_date).total_seconds() / 3600)
        }
    
    def is_active(self):
        """Является ли бронирование активным"""
        return self.status in ['pending', 'confirmed']
    
    def is_upcoming(self):
        """Предстоящее ли бронирование"""
        return self.is_active() and self.start_date > datetime.utcnow()
    
    def is_ongoing(self):
        """Текущее ли бронирование"""
        now = datetime.utcnow()
        return self.is_active() and self.start_date <= now <= self.end_date
    
    def __repr__(self):
        return f'<Booking {self.id} - {self.status}>'


class Favorite(db.Model):
    """Модель избранного оборудования"""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment_item.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Уникальный constraint
    __table_args__ = (
        db.UniqueConstraint('user_id', 'equipment_id', name='unique_user_equipment_favorite'),
    )
    
    def to_dict(self):
        """Сериализация в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'equipment_id': self.equipment_id,
            'created_at': self.created_at.isoformat(),
            'equipment': self.equipment.to_dict() if self.equipment else None
        }
    
    def __repr__(self):
        return f'<Favorite user:{self.user_id} equipment:{self.equipment_id}>'


# Дополнительные модели для будущего расширения
class Quest(db.Model):
    """Модель квеста/обучения"""
    __tablename__ = 'quest'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), default='beginner')  # beginner, intermediate, advanced
    experience_points = db.Column(db.Integer, default=100)
    required_role = db.Column(db.String(20), default='student')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'difficulty': self.difficulty,
            'experience_points': self.experience_points,
            'required_role': self.required_role,
            'is_active': self.is_active
        }


class UserQuestProgress(db.Model):
    """Прогресс пользователя по квестам"""
    __tablename__ = 'user_quest_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quest.id'), nullable=False)
    progress = db.Column(db.Integer, default=0)  # 0-100%
    completed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Связи
    user = db.relationship('User', backref=db.backref('quest_progress', lazy=True))
    quest = db.relationship('Quest', backref=db.backref('user_progress', lazy=True))
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'quest_id', name='unique_user_quest'),
    )