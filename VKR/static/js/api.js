// static/js/api.js - Equipment API Client
console.log('🔧 Equipment API loading...');

class EquipmentAPI {
    constructor() {
        this.baseURL = '/api';
    }

    // Получить оборудование без клиентской пагинации (как было раньше)
    async getAllEquipment() {
        try {
            const response = await fetch(`${this.baseURL}/equipment`);
            if (!response.ok) throw new Error('Ошибка загрузки оборудования');
            
            const data = await response.json();
            console.log('📦 Оборудование загружено:', data.length, 'шт');
            
            return data;
            
        } catch (error) {
            console.error('EquipmentAPI.getAllEquipment error:', error);
            return [];
        }
    }

    // Получить оборудование по ID (для страницы подробнее)
    async getEquipmentById(id) {
        try {
            const response = await fetch(`${this.baseURL}/equipment/${id}`);
            if (!response.ok) throw new Error('Оборудование не найдено');
            
            const data = await response.json();
            console.log('🔍 Оборудование по ID:', data);
            
            return data;
            
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

    // Фильтрация оборудования
    async filterEquipment(filters = {}) {
        try {
            const params = new URLSearchParams(filters);
            const response = await fetch(`${this.baseURL}/equipment/filter?${params}`);
            if (!response.ok) throw new Error('Ошибка фильтрации');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.filterEquipment error:', error);
            return [];
        }
    }

    // Бронирования
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

    async createBooking(bookingData) {
        try {
            const response = await fetch(`${this.baseURL}/bookings`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
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

    // Избранное
    async toggleFavorite(equipmentId) {
        try {
            const response = await fetch(`${this.baseURL}/equipment/${equipmentId}/favorite`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error('Ошибка избранного');
            
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.toggleFavorite error:', error);
            return { success: false, error: error.message };
        }
    }

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

    // Статистика и отчеты
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

    async getReports() {
        try {
            const response = await fetch(`${this.baseURL}/reports`);
            if (!response.ok) throw new Error('Ошибка загрузки отчетов');
            return await response.json();
        } catch (error) {
            console.error('EquipmentAPI.getReports error:', error);
            return [];
        }
    }
}

// Создаем глобальный экземпляр
window.equipmentAPI = new EquipmentAPI();

// Инициализация избранного
window.initializeFavorites = function() {
    console.log('⭐ Инициализация избранного...');
    
    document.addEventListener('click', async function(e) {
        const favoriteBtn = e.target.closest('.favorite-btn');
        if (favoriteBtn) {
            e.preventDefault();
            const equipmentId = favoriteBtn.dataset.equipmentId;
            
            if (equipmentId) {
                try {
                    const result = await equipmentAPI.toggleFavorite(parseInt(equipmentId));
                    if (result.success) {
                        // Обновляем внешний вид кнопки
                        favoriteBtn.classList.toggle('favorited');
                        favoriteBtn.innerHTML = result.favorited ? 
                            '<i class="fas fa-heart"></i>' : 
                            '<i class="far fa-heart"></i>';
                    }
                } catch (error) {
                    console.error('Ошибка избранного:', error);
                }
            }
        }
    });
};

// Автоматическая инициализация
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Equipment API готов!');
    initializeFavorites();
});