// Получение CSRF токена
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Показ уведомлений
function showNotification(message, type = 'success', duration = 3000) {
    // Создаем контейнер если его нет
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
        `;
        document.body.appendChild(container);
    }
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        padding: 15px 25px;
        margin-bottom: 10px;
        border-radius: 10px;
        font-family: 'Rubik', sans-serif;
        font-weight: 500;
        font-size: 18px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        transform: translateX(100%);
        animation: slideIn 0.3s ease forwards;
        ${type === 'success' ? 'background-color: #4CAF50; color: white;' : ''}
        ${type === 'error' ? 'background-color: #f44336; color: white;' : ''}
        ${type === 'info' ? 'background-color: #2196F3; color: white;' : ''}
    `;
    
    container.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease forwards';
        setTimeout(() => {
            if (container.contains(notification)) {
                container.removeChild(notification);
            }
        }, 300);
    }, duration);
}

// Добавить товар в корзину
async function addToCart(productId) {
    try {
        const response = await fetch('/api/add-to-cart/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                product_id: productId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Товар добавлен в корзину!', 'success');
        } else {
            if (response.status === 401) {
                showNotification('Необходимо войти в систему', 'error');
                setTimeout(() => {
                    window.location.href = '/login/';
                }, 2000);
            } else {
                showNotification(data.error || 'Ошибка при добавлении в корзину', 'error');
            }
        }
    } catch (error) {
        console.error('Ошибка при добавлении в корзину:', error);
        showNotification('Произошла ошибка. Попробуйте позже.', 'error');
    }
}

// Получить бесплатный товар
async function getProduct(productId) {
    try {
        const response = await fetch('/api/get-product/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                product_id: productId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Товар добавлен в библиотеку!', 'success', 3000);
            // Перенаправляем на страницу скачивания
            setTimeout(() => {
                window.location.href = data.download_url || `/download/${data.product_slug}/`;
            }, 1500);
        } else {
            if (response.status === 401) {
                showNotification('Необходимо войти в систему', 'error');
                setTimeout(() => {
                    window.location.href = '/login/';
                }, 2000);
            } else {
                showNotification(data.error || 'Ошибка при получении товара', 'error');
            }
        }
    } catch (error) {
        console.error('Ошибка при получении товара:', error);
        showNotification('Произошла ошибка. Попробуйте позже.', 'error');
    }
}

// Купить товар
async function buyProduct(productId) {
    try {
        const response = await fetch('/api/buy-product/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                product_id: productId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.success && data.payment_url) {
                if (data.demo_mode) {
                    showNotification('Демо-режим: Переходим к имитации оплаты', 'info', 3000);
                } else {
                    showNotification('Переходим к оплате через ЮKassa...', 'info', 3000);
                }
                
                // Перенаправляем на страницу оплаты
                setTimeout(() => {
                    window.location.href = data.payment_url;
                }, 1500);
            } else {
                showNotification('Товар успешно приобретен!', 'success', 5000);
            }
        } else {
            if (response.status === 401) {
                showNotification('Необходимо войти в систему', 'error');
                setTimeout(() => {
                    window.location.href = '/login/';
                }, 2000);
            } else {
                showNotification(data.error || 'Ошибка при покупке товара', 'error');
            }
        }
    } catch (error) {
        console.error('Ошибка при покупке товара:', error);
        showNotification('Произошла ошибка. Попробуйте позже.', 'error');
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем стили для анимации
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            to {
                transform: translateX(0);
            }
        }
        @keyframes slideOut {
            to {
                transform: translateX(100%);
            }
        }
    `;
    document.head.appendChild(style);
    
    // Burger menu toggle
    const burgerBtn = document.querySelector('.burger-btn');
    const mobileNav = document.getElementById('mobile-menu');
    if (burgerBtn && mobileNav) {
        burgerBtn.addEventListener('click', () => {
            const isExpanded = burgerBtn.getAttribute('aria-expanded') === 'true';
            burgerBtn.setAttribute('aria-expanded', String(!isExpanded));
            mobileNav.classList.toggle('open');
        });
        // Close on ESC
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && burgerBtn.getAttribute('aria-expanded') === 'true') {
                burgerBtn.setAttribute('aria-expanded', 'false');
                mobileNav.classList.remove('open');
            }
        });
        // Toggle submenus
        mobileNav.querySelectorAll('.submenu-toggle').forEach(btn => {
            btn.addEventListener('click', () => {
                const expanded = btn.getAttribute('aria-expanded') === 'true';
                btn.setAttribute('aria-expanded', String(!expanded));
                const submenu = btn.nextElementSibling;
                if (submenu) {
                    const isHidden = submenu.hasAttribute('hidden');
                    if (isHidden) submenu.removeAttribute('hidden'); else submenu.setAttribute('hidden', '');
                }
            });
        });
    }

    // Обработчики для кнопок "В корзину"
    document.querySelectorAll('.garbej-btn').forEach(button => {
        button.addEventListener('click', function() {
            // Находим ближайшую карточку товара
            const card = this.closest('.card, .card-rolling_stock, .card-maps, .card-scenarios');
            if (card) {
                // Извлекаем ID товара из данных или URL
                const productId = card.dataset.productId;
                if (productId) {
                    addToCart(parseInt(productId));
                } else {
                    showNotification('Не удалось найти ID товара', 'error');
                }
            }
        });
    });
    
    // Обработчики для кнопок "Получить"
    document.querySelectorAll('.get-btn').forEach(button => {
        if (button.textContent.trim() === 'Получить') {
            button.addEventListener('click', function() {
                const card = this.closest('.card, .card-rolling_stock, .card-maps, .card-scenarios');
                if (card) {
                    const productId = card.dataset.productId;
                    if (productId) {
                        getProduct(parseInt(productId));
                    } else {
                        showNotification('Не удалось найти ID товара', 'error');
                    }
                }
            });
        } else if (button.textContent.trim() === 'Приобрести') {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                const card = this.closest('.card, .card-rolling_stock, .card-maps, .card-scenarios');
                if (card) {
                    const productId = card.dataset.productId;
                    if (productId) {
                        buyProduct(parseInt(productId));
                    } else {
                        showNotification('Не удалось найти ID товара', 'error');
                    }
                }
            });
        }
    });
});

// Функции для покупки товаров (копия из product.js)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function showNotification(message, type = 'success', duration = 3000) {
    // Создаем контейнер для уведомлений, если его нет
    let container = document.getElementById('notification-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notification-container';
        container.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
        `;
        document.body.appendChild(container);
    }
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        background: ${type === 'error' ? '#ff4444' : type === 'info' ? '#4488ff' : '#44ff44'};
        color: white;
        padding: 12px 20px;
        margin: 5px 0;
        border-radius: 5px;
        font-size: 18px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    `;
    
    container.appendChild(notification);
    
    // Автоматическое скрытие
    setTimeout(() => {
        notification.style.opacity = '0';
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (container.contains(notification)) {
                container.removeChild(notification);
            }
        }, 300);
    }, duration);
}

function showLoginRequired() {
    // Просто перенаправляем на страницу входа без уведомлений
    window.location.href = '/login/';
}

// Обработчик для получения бесплатного товара
async function handleGetProduct(productId) {
    try {
        const response = await fetch('/api/get-product/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('Товар успешно добавлен в вашу библиотеку!', 'success', 3000);
            // Перенаправляем на страницу скачивания
            setTimeout(() => {
                window.location.href = `/download/${window.productData.slug}/`;
            }, 1500);
        } else {
            if (response.status === 401) {
                showNotification('Необходимо войти в систему', 'error');
                setTimeout(() => {
                    window.location.href = '/login/';
                }, 2000);
            } else {
                showNotification(data.error || 'Ошибка при получении товара', 'error');
            }
        }
    } catch (error) {
        console.error('Ошибка при получении товара:', error);
        showNotification('Произошла ошибка. Попробуйте позже.', 'error');
    }
}

// Обработчик для покупки товара
async function handleBuyProduct(productId) {
    try {
        const response = await fetch('/api/buy-product/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                product_id: productId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            if (data.success && data.payment_url) {
                if (data.demo_mode) {
                    showNotification('Демо-режим: Переходим к имитации оплаты', 'info', 3000);
                } else {
                    showNotification('Переходим к оплате через ЮKassa...', 'info', 3000);
                }
                
                // Перенаправляем на страницу оплаты
                setTimeout(() => {
                    window.location.href = data.payment_url;
                }, 1500);
            } else {
                showNotification('Товар успешно приобретен!', 'success', 5000);
            }
        } else {
            if (response.status === 401) {
                showNotification('Необходимо войти в систему', 'error');
                setTimeout(() => {
                    window.location.href = '/login/';
                }, 2000);
            } else {
                showNotification(data.error || 'Ошибка при покупке товара', 'error');
            }
        }
    } catch (error) {
        console.error('Ошибка при покупке товара:', error);
        showNotification('Произошла ошибка. Попробуйте позже.', 'error');
    }
}
