// static/js/api.js - Клиентский API для работы с оборудованием

class EquipmentAPI {
    constructor() {
        this.baseURL = '/api';
    }

    // Получить все оборудование
    async getAllEquipment() {
        try {
            const response = await fetch(`${this.baseURL}/equipment`);
            if (!response.ok) throw new Error('Ошибка загрузки оборудования');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getAllEquipment error:', error);
            return [];
        }
    }

    // Получить конкретное оборудование по ID
    async getEquipmentById(id) {
        try {
            const response = await fetch(`${this.baseURL}/equipment/${id}`);
            if (!response.ok) throw new Error('Оборудование не найдено');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getEquipmentById error:', error);
            return null;
        }
    }

    // Получить категории
    async getCategories() {
        try {
            const response = await fetch(`${this.baseURL}/categories`);
            if (!response.ok) throw new Error('Ошибка загрузки категорий');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getCategories error:', error);
            return [];
        }
    }

    // Получить бронирования пользователя
    async getUserBookings() {
        try {
            const response = await fetch(`${this.baseURL}/bookings`);
            if (!response.ok) throw new Error('Ошибка загрузки бронирований');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getUserBookings error:', error);
            return [];
        }
    }

    // Создать бронирование
    async createBooking(bookingData) {
        try {
            const response = await fetch(`${this.baseURL}/bookings`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(bookingData)
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Ошибка бронирования');
            }
            
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.createBooking error:', error);
            throw error;
        }
    }

    // Проверить доступность оборудования
    async checkAvailability(equipmentId) {
        try {
            const response = await fetch(`${this.baseURL}/equipment/${equipmentId}/availability`);
            if (!response.ok) throw new Error('Ошибка проверки доступности');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.checkAvailability error:', error);
            return { available: false, error: error.message };
        }
    }

    // Получить избранное
    async getFavorites() {
        try {
            const response = await fetch(`${this.baseURL}/favorites`);
            if (!response.ok) throw new Error('Ошибка загрузки избранного');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getFavorites error:', error);
            return [];
        }
    }

    // Добавить в избранное
    async addToFavorites(equipmentId) {
        try {
            const response = await fetch(`${this.baseURL}/favorites`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ equipment_id: equipmentId })
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Ошибка добавления в избранное');
            }
            
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.addToFavorites error:', error);
            throw error;
        }
    }

    // Удалить из избранного
    async removeFromFavorites(equipmentId) {
        try {
            const response = await fetch(`${this.baseURL}/favorites`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ equipment_id: equipmentId })
            });
            
            if (!response.ok) throw new Error('Ошибка удаления из избранного');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.removeFromFavorites error:', error);
            throw error;
        }
    }

    // Фильтровать оборудование
    async filterEquipment(filters = {}) {
        try {
            const params = new URLSearchParams();
            
            if (filters.category) params.append('category', filters.category);
            if (filters.status) params.append('status', filters.status);
            if (filters.search) params.append('search', filters.search);
            if (filters.page) params.append('page', filters.page);
            if (filters.per_page) params.append('per_page', filters.per_page);
            
            const response = await fetch(`${this.baseURL}/equipment/filter?${params}`);
            if (!response.ok) throw new Error('Ошибка фильтрации оборудования');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.filterEquipment error:', error);
            return { items: [], total: 0, pages: 0, current_page: 1 };
        }
    }

    // Получить уведомления
    async getNotifications() {
        try {
            const response = await fetch(`${this.baseURL}/notifications`);
            if (!response.ok) throw new Error('Ошибка загрузки уведомлений');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getNotifications error:', error);
            return [];
        }
    }

    // Получить статистику
    async getStats() {
        try {
            const response = await fetch(`${this.baseURL}/stats`);
            if (!response.ok) throw new Error('Ошибка загрузки статистики');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getStats error:', error);
            return {};
        }
    }

    // Поиск оборудования
    async searchEquipment(query) {
        try {
            const response = await fetch(`${this.baseURL}/equipment/filter?search=${encodeURIComponent(query)}`);
            if (!response.ok) throw new Error('Ошибка поиска оборудования');
            const data = await response.json();
            return data.items;
        } catch (error) {
            console.error('EquipmentAPI.searchEquipment error:', error);
            return [];
        }
    }

    // === НОВЫЕ ФУНКЦИИ ДЛЯ ИЗБРАННОГО ===

    // Получить избранное пользователя
    async getUserFavorites() {
        try {
            const response = await fetch(`${this.baseURL}/user/favorites`);
            if (!response.ok) throw new Error('Ошибка загрузки избранного');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getUserFavorites error:', error);
            return { success: false, favorites: [] };
        }
    }

    // Добавить/удалить из избранного
    async toggleFavorite(equipmentId) {
        try {
            // Сначала проверяем, есть ли уже в избранном
            const favorites = await this.getUserFavorites();
            const isFavorited = favorites.favorites?.some(fav => fav.id === equipmentId);
            
            const method = isFavorited ? 'DELETE' : 'POST';
            const url = `${this.baseURL}/equipment/${equipmentId}/favorite`;
            
            const response = await fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            });
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Ошибка обновления избранного');
            }
            
            const result = await response.json();
            return {
                success: true,
                favorited: !isFavorited,
                message: result.message
            };
            
        } catch (error) {
            console.error('EquipmentAPI.toggleFavorite error:', error);
            return { success: false, error: error.message };
        }
    }

    // Проверить, находится ли оборудование в избранном
    async isEquipmentFavorited(equipmentId) {
        try {
            const favorites = await this.getUserFavorites();
            if (favorites.success) {
                return favorites.favorites.some(fav => fav.id === equipmentId);
            }
            return false;
        } catch (error) {
            console.error('EquipmentAPI.isEquipmentFavorited error:', error);
            return false;
        }
    }

    // Получить количество избранного для оборудования
    async getFavoritesCount(equipmentId) {
        try {
            const response = await fetch(`${this.baseURL}/equipment/${equipmentId}/favorites/count`);
            if (!response.ok) throw new Error('Ошибка загрузки количества избранного');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getFavoritesCount error:', error);
            return { success: false, count: 0 };
        }
    }

    // Получить популярное оборудование (по количеству избранного)
    async getPopularEquipment(limit = 6) {
        try {
            const response = await fetch(`${this.baseURL}/equipment/popular?limit=${limit}`);
            if (!response.ok) throw new Error('Ошибка загрузки популярного оборудования');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getPopularEquipment error:', error);
            return [];
        }
    }

    // Получить рекомендации на основе избранного
    async getRecommendations() {
        try {
            const response = await fetch(`${this.baseURL}/user/recommendations`);
            if (!response.ok) throw new Error('Ошибка загрузки рекомендаций');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getRecommendations error:', error);
            return [];
        }
    }
}

// Создаем глобальный экземпляр API
window.equipmentAPI = new EquipmentAPI();

// Вспомогательные функции для тестирования
window.testAllAPI = async function() {
    console.log('🧪 Тестирование всех API функций...');
    
    try {
        const stats = await equipmentAPI.getStats();
        console.log('📊 Статистика:', stats);
        
        const equipment = await equipmentAPI.getAllEquipment();
        console.log('📦 Оборудование:', equipment.length, 'шт');
        
        const categories = await equipmentAPI.getCategories();
        console.log('📁 Категории:', categories.length, 'шт');
        
        const notifications = await equipmentAPI.getNotifications();
        console.log('🔔 Уведомления:', notifications.length, 'шт');
        
        console.log('✅ Все API функции работают корректно!');
        showNotification('✅ Все API функции работают!', 'success');
        
    } catch (error) {
        console.error('❌ Ошибка тестирования API:', error);
        showNotification('❌ Ошибка тестирования API', 'error');
    }
};

// Функция для показа уведомлений
window.showNotification = function(message, type = 'info') {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateX(400px);
        transition: transform 0.3s ease;
    `;
    
    if (type === 'success') {
        notification.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
    } else if (type === 'error') {
        notification.style.background = 'linear-gradient(135deg, #dc3545, #e83e8c)';
    } else {
        notification.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    setTimeout(() => {
        notification.style.transform = 'translateX(400px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 4000);
};

// Функция для инициализации системы избранного на страницах
window.initializeFavorites = function() {
    console.log('⭐️ Инициализация системы избранного...');
    
    // Добавляем обработчики для кнопок избранного
    document.addEventListener('click', async function(e) {
        if (e.target.closest('.favorite-btn') || e.target.classList.contains('favorite-btn')) {
            e.preventDefault();
            const btn = e.target.closest('.favorite-btn') || e.target;
            const equipmentId = btn.dataset.equipmentId;
            
            if (equipmentId) {
                await toggleFavoriteHandler(equipmentId, btn);
            }
        }
    });
};

// Обработчик переключения избранного
async function toggleFavoriteHandler(equipmentId, button) {
    try {
        // Показываем состояние загрузки
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        const result = await equipmentAPI.toggleFavorite(parseInt(equipmentId));
        
        if (result.success) {
            // Обновляем внешний вид кнопки
            if (result.favorited) {
                button.innerHTML = '<i class="fas fa-heart"></i>';
                button.classList.add('favorited');
                showNotification('Добавлено в избранное ❤️', 'success');
            } else {
                button.innerHTML = '<i class="far fa-heart"></i>';
                button.classList.remove('favorited');
                showNotification('Удалено из избранного', 'info');
            }
            
            // Анимация
            button.style.transform = 'scale(1.2)';
            setTimeout(() => {
                button.style.transform = 'scale(1)';
            }, 200);
            
        } else {
            showNotification('Ошибка: ' + result.error, 'error');
        }
        
    } catch (error) {
        console.error('Toggle favorite error:', error);
        showNotification('Ошибка обновления избранного', 'error');
    } finally {
        button.disabled = false;
    }
}

// Функция для обновления всех кнопок избранного на странице
window.updateFavoriteButtons = async function() {
    const favoriteButtons = document.querySelectorAll('[data-equipment-id]');
    
    for (const button of favoriteButtons) {
        const equipmentId = button.dataset.equipmentId;
        const isFavorited = await equipmentAPI.isEquipmentFavorited(parseInt(equipmentId));
        
        if (isFavorited) {
            button.innerHTML = '<i class="fas fa-heart"></i>';
            button.classList.add('favorited');
        } else {
            button.innerHTML = '<i class="far fa-heart"></i>';
            button.classList.remove('favorited');
        }
    }
};

// Автоматическая инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initializeFavorites();
    
    // Обновляем кнопки избранного если они есть на странице
    if (document.querySelector('[data-equipment-id]')) {
        updateFavoriteButtons();
    }
});

// Функция для переключения избранного
async function toggleFavorite(equipmentId, button) {
    try {
        // Показываем состояние загрузки
        button.disabled = true;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        
        // Определяем метод (добавить или удалить)
        const isCurrentlyFavorited = button.classList.contains('favorited');
        const method = isCurrentlyFavorited ? 'DELETE' : 'POST';
        
        const response = await fetch(`/api/equipment/${equipmentId}/favorite`, {
            method: method
        });
        
        const result = await response.json();
        
        if (result.success) {
            if (result.favorited) {
                // Добавили в избранное
                button.innerHTML = '<i class="fas fa-heart"></i>';
                button.classList.add('favorited');
                showNotification('❤️ Добавлено в избранное', 'success');
            } else {
                // Удалили из избранного
                button.innerHTML = '<i class="far fa-heart"></i>';
                button.classList.remove('favorited');
                showNotification('Удалено из избранного', 'info');
            }
            
            // Анимация
            button.style.transform = 'scale(1.2)';
            setTimeout(() => {
                button.style.transform = 'scale(1)';
            }, 200);
            
        } else {
            showNotification('Ошибка: ' + result.error, 'error');
        }
        
    } catch (error) {
        console.error('Toggle favorite error:', error);
        showNotification('Ошибка обновления избранного', 'error');
    } finally {
        button.disabled = false;
    }
}

// Функция для загрузки текущего состояния избранного
async function loadFavoriteStates() {
    try {
        const response = await fetch('/api/user/favorites');
        const data = await response.json();
        
        if (data.success) {
            // Для каждого оборудования проверяем, есть ли оно в избранном
            document.querySelectorAll('.favorite-btn').forEach(button => {
                const equipmentId = button.dataset.equipmentId;
                const isFavorited = data.favorites.some(fav => fav.id == equipmentId);
                
                if (isFavorited) {
                    button.innerHTML = '<i class="fas fa-heart"></i>';
                    button.classList.add('favorited');
                } else {
                    button.innerHTML = '<i class="far fa-heart"></i>';
                    button.classList.remove('favorited');
                }
            });
        }
    } catch (error) {
        console.error('Error loading favorite states:', error);
    }
}

// Добавляем обработчики событий для кнопок
document.addEventListener('DOMContentLoaded', function() {
    // Загружаем текущее состояние избранного
    loadFavoriteStates();
    
    // Добавляем обработчики клика на кнопки избранного
    document.addEventListener('click', function(e) {
        if (e.target.closest('.favorite-btn')) {
            const button = e.target.closest('.favorite-btn');
            const equipmentId = button.dataset.equipmentId;
            toggleFavorite(equipmentId, button);
        }
    });
});

// Функция показа уведомлений (если её нет)
function showNotification(message, type = 'info') {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 10000;
        max-width: 300px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        transform: translateX(400px);
        transition: transform 0.3s ease;
    `;
    
    if (type === 'success') {
        notification.style.background = 'linear-gradient(135deg, #28a745, #20c997)';
    } else if (type === 'error') {
        notification.style.background = 'linear-gradient(135deg, #dc3545, #e83e8c)';
    } else {
        notification.style.background = 'linear-gradient(135deg, #667eea, #764ba2)';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    // Анимация появления
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Автоматическое скрытие
    setTimeout(() => {
        notification.style.transform = 'translateX(400px)';
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 300);
    }, 3000);
}