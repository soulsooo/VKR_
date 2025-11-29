// static/js/api.js - API клиент для оборудования
console.log('🚀 Equipment API загружен!');

class EquipmentAPI {
    constructor() {
        this.baseURL = '/api';
        this.debug = true;
    }

    // Универсальный метод для GET запросов
    async _get(endpoint, params = {}) {
        try {
            const url = new URL(endpoint, window.location.origin);
            Object.keys(params).forEach(key => {
                if (params[key] !== undefined && params[key] !== null) {
                    url.searchParams.append(key, params[key]);
                }
            });

            console.log(`🔍 GET ${url.toString()}`);
            const response = await fetch(url.toString());

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();
            console.log(`✅ GET success:`, data);
            return data;

        } catch (error) {
            console.error(`❌ GET error:`, error);
            throw error;
        }
    }

    // Получить все оборудование
    async getAllEquipment(page = 1, perPage = 12) {
        try {
            const data = await this._get(`${this.baseURL}/equipment`, {
                page: page,
                per_page: perPage
            });
            return this.normalizeEquipmentResponse(data);
        } catch (error) {
            console.error('❌ getAllEquipment error:', error);
            return this.getFallbackResponse();
        }
    }

    // Нормализация ответа оборудования
    normalizeEquipmentResponse(response) {
        const items = response.items || response.equipment || response.data || [];
        const pagination = response.pagination || response.meta || {};
        
        return {
            items: this.normalizeEquipmentData(items),
            total: response.total || pagination.total || items.length,
            pages: response.pages || pagination.total_pages || pagination.last_page || 1,
            current_page: response.current_page || pagination.current_page || 1,
            per_page: response.per_page || pagination.per_page || 12
        };
    }

    normalizeEquipmentData(equipment) {
        if (!equipment) return [];
        if (Array.isArray(equipment)) {
            return equipment.map(item => this.normalizeSingleEquipment(item));
        }
        return [this.normalizeSingleEquipment(equipment)];
    }

    normalizeSingleEquipment(item) {
        if (!item) return null;
        const normalized = { ...item };
        
        // Нормализуем изображения
        normalized.image_url = this.normalizeImagePath(
            normalized.image_url || normalized.image || normalized.image_path
        );
        normalized.image_alt = normalized.image_alt || normalized.name || 'Оборудование';
        
        return normalized;
    }

    normalizeImagePath(image) {
        if (!image) return '/static/images/placeholder.jpg';
        
        if (typeof image === 'string') {
            if (!image.startsWith('http') && !image.startsWith('/')) {
                return `/static/images/equipment/${image}`;
            }
            return image;
        }
        
        return '/static/images/placeholder.jpg';
    }

    getFallbackResponse() {
        return {
            items: [],
            total: 0,
            pages: 0,
            current_page: 1,
            per_page: 12
        };
    }

    // Диагностика API
    async diagnose() {
        console.log('🔍 Диагностика API...');
        
        const endpoints = [
            '/api/equipment',
            '/api/categories',
            '/api/equipment?page=1'
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint);
                console.log(`${endpoint}: ${response.status} ${response.statusText}`);
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('✅ Данные:', data);
                    
                    if (data.items && data.items[0]) {
                        console.log('📸 Первый элемент:', data.items[0]);
                        console.log('🖼️ Image URL:', data.items[0].image_url);
                    }
                }
            } catch (error) {
                console.log(`${endpoint}: ❌ ${error.message}`);
            }
        }
    }
}

// Создаем глобальный экземпляр
window.equipmentAPI = new EquipmentAPI();

// Глобальные функции
window.diagnoseAPI = function() {
    equipmentAPI.diagnose();
};

window.testEquipmentAPI = function() {
    equipmentAPI.getAllEquipment(1, 3).then(data => {
        console.log('🧪 Тест оборудования:', data);
    });
};

window.debugEquipmentAPI = function() {
    equipmentAPI.debug = !equipmentAPI.debug;
    console.log(`🔧 Debug mode: ${equipmentAPI.debug ? 'ON' : 'OFF'}`);
};

// Система уведомлений
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
        background: ${type === 'error' ? '#dc3545' : type === 'success' ? '#28a745' : '#667eea'};
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    `;
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
};

// Инициализация при загрузке
document.addEventListener('DOMContentLoaded', function() {
    console.log('✅ Equipment API инициализирован');
    
    // Обработка ошибок изображений
    document.addEventListener('error', function(e) {
        if (e.target.tagName === 'IMG') {
            console.log('❌ Ошибка загрузки изображения:', e.target.src);
            e.target.src = '/static/images/placeholder.jpg';
        }
    }, true);
});