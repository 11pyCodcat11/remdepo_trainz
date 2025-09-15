// Переменная для хранения реального пароля (в реальном приложении это должно приходить с сервера)
let realPassword = '********';
let isPasswordVisible = false;
let currentUserPassword = window.userData ? window.userData.lastKnownPassword : 'testpass123'; // Текущий пароль пользователя

const eyeToggle = document.getElementById('eyeToggle');
const passwordText = document.getElementById('passwordText');
const eyeIcon = document.querySelector('.eye-icon');

// Функция для получения реального пароля
async function getRealPassword() {
    // Показываем модальное окно для подтверждения пароля
    return new Promise((resolve) => {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content">
                <h2>Подтвердите пароль</h2>
                <p style="color: #5C3A00; margin-bottom: 20px; text-align: center;">
                    Введите ваш пароль для просмотра
                </p>
                <form id="passwordConfirmForm">
                    <div class="form-group">
                        <label for="confirmPasswordInput">Ваш пароль:</label>
                        <input type="password" id="confirmPasswordInput" required autofocus>
                    </div>
                    <div class="modal-buttons">
                        <button type="button" class="btn-cancel">Отмена</button>
                        <button type="submit" class="btn-save">Показать пароль</button>
                    </div>
                </form>
            </div>
        `;
        
        document.body.appendChild(modal);
        
        // Добавляем иконку глаза к полю пароля
        const passwordInput = modal.querySelector('#confirmPasswordInput');
        addPasswordToggle(passwordInput);
        
        // Обработчики для модального окна
        modal.querySelector('.btn-cancel').addEventListener('click', () => {
            document.body.removeChild(modal);
            resolve('********');
        });
        
        modal.querySelector('#passwordConfirmForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const password = document.getElementById('confirmPasswordInput').value;
            
            try {
                const response = await fetch('/api/get-real-password/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': getCookie('csrftoken'),
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        confirm_password: password
                    })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    document.body.removeChild(modal);
                    // Сохраняем пароль для дальнейшего использования
                    currentUserPassword = data.password;
                    sessionStorage.setItem('userPassword', data.password);
                    resolve(data.password);
                } else {
                    showNotification(data.error || 'Неверный пароль', 'error');
                }
            } catch (error) {
                console.error('Ошибка при получении пароля:', error);
                showNotification('Ошибка при получении пароля', 'error');
            }
        });
        
        // Закрытие по клику вне модального окна
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                document.body.removeChild(modal);
                resolve('********');
            }
        });
    });
}

// Функция для показа красивых уведомлений
function showNotification(message, type = 'success', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <span>${message}</span>
        <button class="close-btn" onclick="this.parentElement.remove()">×</button>
    `;
    
    document.body.appendChild(notification);
    
    // Показываем уведомление с анимацией
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Автоматически убираем уведомление
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            if (notification.parentElement) {
                notification.parentElement.removeChild(notification);
            }
        }, 300);
    }, duration);
}

// Функция для добавления иконки глаза к полю пароля
function addPasswordToggle(inputElement, containerId) {
    const container = inputElement.parentElement;
    container.style.position = 'relative';
    
    const toggleButton = document.createElement('button');
    toggleButton.type = 'button';
    toggleButton.className = 'password-eye-toggle';
    toggleButton.innerHTML = `
        <svg viewBox="0 0 24 24" class="password-eye-icon">
            <path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>
        </svg>
    `;
    
    container.appendChild(toggleButton);
    
    // Обработчик клика
    toggleButton.addEventListener('click', () => {
        const icon = toggleButton.querySelector('.password-eye-icon');
        if (inputElement.type === 'password') {
            inputElement.type = 'text';
            // Открытый глаз
            icon.innerHTML = '<path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>';
        } else {
            inputElement.type = 'password';
            // Закрытый глаз
            icon.innerHTML = '<path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>';
        }
    });
}

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

// Обработчик клика по иконке глаза
eyeToggle.addEventListener('click', async () => {
    if (!isPasswordVisible) {
        // Показываем пароль
        try {
            realPassword = await getRealPassword();
            passwordText.textContent = realPassword;
            passwordText.classList.add('selectable');
            passwordText.style.userSelect = 'text';
            passwordText.style.cursor = 'text';
            passwordText.title = 'Нажмите для копирования';
            
            // Меняем иконку на открытый глаз (пароль видно)
            eyeIcon.innerHTML = '<path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5zm0-8c-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3-1.34-3-3-3z"/>';
            isPasswordVisible = true;
        } catch (error) {
            console.error('Ошибка при получении пароля:', error);
            alert('Ошибка при получении пароля');
        }
    } else {
        // Скрываем пароль
        passwordText.textContent = '********';
        passwordText.classList.remove('selectable');
        passwordText.style.userSelect = 'none';
        passwordText.style.cursor = 'default';
        passwordText.title = '';
        
        // Меняем иконку на закрытый глаз (пароль скрыт)
        eyeIcon.innerHTML = '<path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>';
        isPasswordVisible = false;
    }
});

// Добавляем возможность копирования пароля при клике
passwordText.addEventListener('click', async () => {
    if (isPasswordVisible && realPassword && realPassword !== '********') {
        try {
            await navigator.clipboard.writeText(realPassword);
            showNotification('📋 Пароль скопирован в буфер обмена!', 'info', 2000);
        } catch (error) {
            console.error('Ошибка при копировании:', error);
            // Fallback для старых браузеров
            const textArea = document.createElement('textarea');
            textArea.value = realPassword;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            showNotification('📋 Пароль скопирован в буфер обмена!', 'info', 2000);
        }
    }
});

// Обработчики для кнопок изменения данных
document.addEventListener('DOMContentLoaded', function() {
    const changePasswordBtn = document.querySelector('.change-btns:nth-child(1)');
    const changeLoginBtn = document.querySelector('.change-btns:nth-child(2)');
    const cartBtn = document.querySelector('.change-btns:nth-child(3)');
    const historyBtn = document.querySelector('.change-btns:nth-child(4)');

    changePasswordBtn.addEventListener('click', function() {
        showChangePasswordModal();
    });

    changeLoginBtn.addEventListener('click', function() {
        showChangeLoginModal();
    });

    cartBtn.addEventListener('click', function() {
        window.location.href = '/cart/';
    });

    historyBtn.addEventListener('click', function() {
        window.location.href = '/purchases/';
    });

    cartBtn.addEventListener('click', function() {
        window.location.href = '/cart/';
    });

    historyBtn.addEventListener('click', function() {
        window.location.href = '/history/';
    });
});

// Функция для показа модального окна смены пароля
function showChangePasswordModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <h2>Смена пароля</h2>
            <form id="changePasswordForm">
                <div class="form-group">
                    <label for="currentPassword">Текущий пароль:</label>
                    <input type="password" id="currentPassword" required>
                </div>
                <div class="form-group">
                    <label for="newPassword">Новый пароль:</label>
                    <input type="password" id="newPassword" required>
                </div>
                <div class="form-group">
                    <label for="confirmPassword">Подтвердите пароль:</label>
                    <input type="password" id="confirmPassword" required>
                </div>
                <div class="modal-buttons">
                    <button type="button" class="btn-cancel">Отмена</button>
                    <button type="submit" class="btn-save">Сохранить</button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Обработчики для модального окна
    modal.querySelector('.btn-cancel').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    modal.querySelector('#changePasswordForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await handlePasswordChange();
        document.body.removeChild(modal);
    });
    
    // Добавляем иконки глаз к полям паролей
    const currentPasswordInput = modal.querySelector('#currentPassword');
    const newPasswordInput = modal.querySelector('#newPassword');
    const confirmPasswordInput = modal.querySelector('#confirmPassword');
    
    addPasswordToggle(currentPasswordInput);
    addPasswordToggle(newPasswordInput);
    addPasswordToggle(confirmPasswordInput);
}

// Функция для показа модального окна смены логина
function showChangeLoginModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content">
            <h2>Смена логина</h2>
            <form id="changeLoginForm">
                <div class="form-group">
                    <label for="currentPasswordLogin">Текущий пароль:</label>
                    <input type="password" id="currentPasswordLogin" required>
                </div>
                <div class="form-group">
                    <label for="newLogin">Новый логин:</label>
                    <input type="text" id="newLogin" required>
                </div>
                <div class="modal-buttons">
                    <button type="button" class="btn-cancel">Отмена</button>
                    <button type="submit" class="btn-save">Сохранить</button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Обработчики для модального окна
    modal.querySelector('.btn-cancel').addEventListener('click', () => {
        document.body.removeChild(modal);
    });
    
    modal.querySelector('#changeLoginForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        await handleLoginChange();
        document.body.removeChild(modal);
    });
    
    // Добавляем иконку глаза к полю пароля
    const currentPasswordLoginInput = modal.querySelector('#currentPasswordLogin');
    addPasswordToggle(currentPasswordLoginInput);
}

// Функция для обработки смены пароля
async function handlePasswordChange() {
    const currentPassword = document.getElementById('currentPassword').value;
    const newPassword = document.getElementById('newPassword').value;
    const confirmPassword = document.getElementById('confirmPassword').value;
    
    if (newPassword !== confirmPassword) {
        showNotification('Пароли не совпадают!', 'error');
        return;
    }
    
    if (newPassword.length < 6) {
        showNotification('Пароль должен содержать минимум 6 символов!', 'error');
        return;
    }
    
    try {
        const response = await fetch('/change-password/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_password: newPassword
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Обновляем текущий пароль в переменной и сохраняем в sessionStorage
            currentUserPassword = newPassword;
            sessionStorage.setItem('userPassword', newPassword);
            
            // Если пароль сейчас виден, обновляем его отображение
            if (isPasswordVisible) {
                passwordText.textContent = newPassword;
            }
            
            showNotification('🎉 Пароль успешно изменен!', 'success', 4000);
        } else {
            showNotification(data.error || 'Ошибка при смене пароля', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('Произошла ошибка при смене пароля', 'error');
    }
}

// Функция для обработки смены логина
async function handleLoginChange() {
    const currentPassword = document.getElementById('currentPasswordLogin').value;
    const newLogin = document.getElementById('newLogin').value;
    
    if (newLogin.length < 3) {
        showNotification('Логин должен содержать минимум 3 символа!', 'error');
        return;
    }
    
    if (!/^[a-zA-Z0-9_]+$/.test(newLogin)) {
        showNotification('Логин может содержать только буквы, цифры и подчеркивание!', 'error');
        return;
    }
    
    try {
        const response = await fetch('/change-login/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken'),
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                current_password: currentPassword,
                new_login: newLogin
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('✨ Логин успешно изменен!', 'success', 4000);
            // Обновляем отображение логина на странице
            document.querySelector('.info-item:first-child span:last-child').textContent = newLogin;
        } else {
            showNotification(data.error || 'Ошибка при смене логина', 'error');
        }
    } catch (error) {
        console.error('Ошибка:', error);
        showNotification('Произошла ошибка при смене логина', 'error');
    }
}
