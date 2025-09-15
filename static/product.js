// Функция для получения CSRF токена
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

// Переменные для полноэкранного просмотрщика
let currentViewerIndex = 0;

// Функция для смены основного изображения
function changeMainImage(imageSrc, index) {
    const mainImage = document.getElementById('mainImage');
    const thumbnails = document.querySelectorAll('.thumbnail');
    
    if (mainImage) {
        mainImage.src = imageSrc;
        currentViewerIndex = index; // Обновляем текущий индекс
        
        // Обновляем активный thumbnail
        thumbnails.forEach((thumb, i) => {
            if (i === index) {
                thumb.classList.add('active');
            } else {
                thumb.classList.remove('active');
            }
        });
    }
}

// Открыть полноэкранный просмотрщик
function openImageViewer(index) {
    if (window.productData.photos.length === 0) return;
    
    currentViewerIndex = index;
    const viewer = document.getElementById('imageViewer');
    const viewerImage = document.getElementById('viewerImage');
    const imageCounter = document.getElementById('imageCounter');
    
    // Устанавливаем изображение
    viewerImage.src = window.productData.photos[currentViewerIndex];
    viewerImage.alt = window.productData.title;
    
    // Обновляем счетчик
    imageCounter.textContent = `${currentViewerIndex + 1} / ${window.productData.photos.length}`;
    
    // Показываем просмотрщик
    viewer.classList.add('active');
    document.body.style.overflow = 'hidden'; // Блокируем прокрутку страницы
}

// Закрыть полноэкранный просмотрщик
function closeImageViewer() {
    const viewer = document.getElementById('imageViewer');
    viewer.classList.remove('active');
    document.body.style.overflow = ''; // Разблокируем прокрутку страницы
}

// Предыдущее изображение
function previousImage() {
    if (window.productData.photos.length <= 1) return;
    
    currentViewerIndex = currentViewerIndex > 0 ? currentViewerIndex - 1 : window.productData.photos.length - 1;
    updateViewerImage();
}

// Следующее изображение
function nextImage() {
    if (window.productData.photos.length <= 1) return;
    
    currentViewerIndex = currentViewerIndex < window.productData.photos.length - 1 ? currentViewerIndex + 1 : 0;
    updateViewerImage();
}

// Обновить изображение в просмотрщике
function updateViewerImage() {
    const viewerImage = document.getElementById('viewerImage');
    const imageCounter = document.getElementById('imageCounter');
    
    viewerImage.src = window.productData.photos[currentViewerIndex];
    imageCounter.textContent = `${currentViewerIndex + 1} / ${window.productData.photos.length}`;
}

// Функция для показа уведомлений
function showNotification(message, type = 'success', duration = 3000) {
    const container = document.getElementById('notification-container');
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    container.appendChild(notification);
    
    // Автоматическое скрытие
    setTimeout(() => {
        notification.classList.add('hiding');
        setTimeout(() => {
            if (container.contains(notification)) {
                container.removeChild(notification);
            }
        }, 300);
    }, duration);
}

// Обработчик для получения бесплатного товара
async function handleGetProduct(productId) {
    if (!window.userData.isAuthenticated) {
        showLoginRequired();
        return;
    }
    
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
            showNotification(`${window.productData.title} успешно добавлен в вашу библиотеку!`, 'success', 3000);
            // Перенаправляем на страницу скачивания
            setTimeout(() => {
                window.location.href = `/download/${window.productData.slug}/`;
            }, 1500);
        } else {
            showNotification(data.error || 'Ошибка при получении товара', 'error');
        }
    } catch (error) {
        console.error('Ошибка при получении товара:', error);
        showNotification('Произошла ошибка. Попробуйте позже.', 'error');
    }
}

// Обработчик для покупки товара
async function handleBuyProduct(productId) {
    if (!window.userData.isAuthenticated) {
        showLoginRequired();
        return;
    }
    
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
                showNotification(`${window.productData.title} успешно приобретен за ${window.productData.price}₽!`, 'success', 5000);
            }
        } else {
            showNotification(data.error || 'Ошибка при покупке товара', 'error');
        }
    } catch (error) {
        console.error('Ошибка при покупке товара:', error);
        showNotification('Произошла ошибка. Попробуйте позже.', 'error');
    }
}

// Обработчик для добавления в корзину
async function handleAddToCart(productId) {
    if (!window.userData.isAuthenticated) {
        showLoginRequired();
        return;
    }
    
    try {
        const response = await fetch('/api/add-to-cart/', {
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
            showNotification(`${window.productData.title} добавлен в корзину!`, 'success', 4000);
        } else {
            showNotification(data.error || 'Ошибка при добавлении в корзину', 'error');
        }
    } catch (error) {
        console.error('Ошибка при добавлении в корзину:', error);
        showNotification('Произошла ошибка. Попробуйте позже.', 'error');
    }
}

// Показать сообщение о необходимости авторизации
function showLoginRequired() {
    showNotification('Для выполнения этого действия необходимо войти в систему', 'info', 4000);
    
    // Через небольшую задержку предложим перейти на страницу входа
    setTimeout(() => {
        const shouldLogin = confirm('Перейти на страницу входа?');
        if (shouldLogin) {
            window.location.href = '/login/';
        }
    }, 1000);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Добавляем обработчики клавиатуры для галереи
    if (window.productData.photos.length > 1) {
        let currentImageIndex = 0;
        
        document.addEventListener('keydown', function(e) {
            const viewer = document.getElementById('imageViewer');
            const isViewerOpen = viewer.classList.contains('active');
            
            if (e.key === 'ArrowLeft') {
                e.preventDefault();
                if (isViewerOpen) {
                    previousImage();
                } else {
                    currentImageIndex = currentImageIndex > 0 ? currentImageIndex - 1 : window.productData.photos.length - 1;
                    changeMainImage(window.productData.photos[currentImageIndex], currentImageIndex);
                }
            } else if (e.key === 'ArrowRight') {
                e.preventDefault();
                if (isViewerOpen) {
                    nextImage();
                } else {
                    currentImageIndex = currentImageIndex < window.productData.photos.length - 1 ? currentImageIndex + 1 : 0;
                    changeMainImage(window.productData.photos[currentImageIndex], currentImageIndex);
                }
            } else if (e.key === 'Escape' && isViewerOpen) {
                e.preventDefault();
                closeImageViewer();
            } else if (e.key === 'Enter' || e.key === ' ') {
                if (!isViewerOpen) {
                    e.preventDefault();
                    openImageViewer(currentImageIndex);
                }
            }
        });
        
        // Добавляем свайп для мобильных устройств
        let startX = 0;
        let endX = 0;
        
        const mainImage = document.getElementById('mainImage');
        if (mainImage) {
            mainImage.addEventListener('touchstart', function(e) {
                startX = e.touches[0].clientX;
            });
            
            mainImage.addEventListener('touchend', function(e) {
                endX = e.changedTouches[0].clientX;
                const diffX = startX - endX;
                
                if (Math.abs(diffX) > 50) { // минимальное расстояние для свайпа
                    if (diffX > 0) {
                        // свайп влево - следующее изображение
                        currentImageIndex = currentImageIndex < window.productData.photos.length - 1 ? currentImageIndex + 1 : 0;
                    } else {
                        // свайп вправо - предыдущее изображение
                        currentImageIndex = currentImageIndex > 0 ? currentImageIndex - 1 : window.productData.photos.length - 1;
                    }
                    changeMainImage(window.productData.photos[currentImageIndex], currentImageIndex);
                }
            });
        }
    }
    
    // Закрытие просмотрщика по клику на фон
    const imageViewer = document.getElementById('imageViewer');
    if (imageViewer) {
        imageViewer.addEventListener('click', function(e) {
            if (e.target === imageViewer) {
                closeImageViewer();
            }
        });
    }
    
    // Добавляем плавную прокрутку для мобильных миниатюр
    const thumbnailsContainer = document.querySelector('.thumbnails-container');
    if (thumbnailsContainer && window.innerWidth <= 480) {
        thumbnailsContainer.style.scrollBehavior = 'smooth';
    }
    
    console.log('Product page initialized');
    console.log('Product data:', window.productData);
    console.log('User data:', window.userData);
});
