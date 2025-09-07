document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('registerForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const password2Input = document.getElementById('password2');
    const checkbox = document.getElementById('agreeCheckbox');

    const eye1 = document.getElementById('eyeToggle1').querySelector('svg');
    const eye2 = document.getElementById('eyeToggle2').querySelector('svg');

    // Иконки (используем те же, что и во втором примере для консистентности)
    const eyeOpen = '<path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5zM12 17c-2.76 0-5-2.24-5-5s2.24-5 5-5 5 2.24 5 5-2.24 5-5 5z"/>';
    const eyeClosed = '<path d="M12 7c2.76 0 5 2.24 5 5 0 .65-.13 1.26-.36 1.83l2.92 2.92c1.51-1.26 2.7-2.89 3.43-4.75-1.73-4.39-6-7.5-11-7.5-1.4 0-2.74.25-3.98.7l2.16 2.16C10.74 7.13 11.35 7 12 7zM2 4.27l2.28 2.28.46.46C3.08 8.3 1.78 10.02 1 12c1.73 4.39 6 7.5 11 7.5 1.55 0 3.03-.3 4.38-.84l.42.42L19.73 22 21 20.73 3.27 3 2 4.27zM7.53 9.8l1.55 1.55c-.05.21-.08.43-.08.65 0 1.66 1.34 3 3 3 .22 0 .44-.03.65-.08l1.55 1.55c-.67.33-1.41.53-2.2.53-2.76 0-5-2.24-5-5 0-.79.2-1.53.53-2.2zm4.31-.78l3.15 3.15.02-.16c0-1.66-1.34-3-3-3l-.17.01z"/>';

    // Функция переключения видимости пароля
    function toggleEye(input, icon) {
        if (input.type === 'password') {
            input.type = 'text';
            icon.innerHTML = eyeOpen;
        } else {
            input.type = 'password';
            icon.innerHTML = eyeClosed;
        }
    }

    // Инициализация глазков
    eye1.innerHTML = eyeClosed;
    eye2.innerHTML = eyeClosed;

    // Навешиваем обработчики на глазки
    document.getElementById('eyeToggle1').addEventListener('click', () => toggleEye(passwordInput, eye1));
    document.getElementById('eyeToggle2').addEventListener('click', () => toggleEye(password2Input, eye2));

    // Функция для проверки совпадения паролей и показа ошибки
    function validatePasswords() {
        const errorElement = document.getElementById('password2Error');
        // Проверяем, только если оба поля не пустые
        if (passwordInput.value && password2Input.value) {
            if (passwordInput.value !== password2Input.value) {
                errorElement.textContent = 'Пароли не совпадают';
                password2Input.classList.add('error');
                return false;
            } else {
                errorElement.textContent = '';
                password2Input.classList.remove('error');
                return true;
            }
        } else {
            // Если какое-то из полей пустое, просто чистим ошибку
            errorElement.textContent = '';
            password2Input.classList.remove('error');
            return false;
        }
    }

    // Живая валидация паролей при вводе
    passwordInput.addEventListener('input', validatePasswords);
    password2Input.addEventListener('input', validatePasswords);

    // Валидация при отправке формы
    form.addEventListener('submit', function(e) {
        let valid = true;
        // Очищаем предыдущие ошибки
        document.getElementById('usernameError').textContent = '';
        document.getElementById('passwordError').textContent = '';
        document.getElementById('password2Error').textContent = '';
        document.getElementById('checkboxError').textContent = '';
        usernameInput.classList.remove('error');
        passwordInput.classList.remove('error');
        password2Input.classList.remove('error');

        // Проверяем логин
        if (!usernameInput.value.trim()) {
            document.getElementById('usernameError').textContent = 'Заполните логин';
            usernameInput.classList.add('error');
            valid = false;
        }
        // Проверяем основной пароль
        if (!passwordInput.value) {
            document.getElementById('passwordError').textContent = 'Введите пароль';
            passwordInput.classList.add('error');
            valid = false;
        }
        // Проверяем совпадение паролей с помощью нашей функции
        const passwordsMatch = validatePasswords();
        if (!passwordsMatch) {
            valid = false; // validatePasswords уже показала ошибку
        }
        // Проверяем чекбокс
        if (!checkbox.checked) {
            document.getElementById('checkboxError').textContent = 'Необходимо согласие';
            valid = false;
        }

        if (!valid) {
            e.preventDefault(); // Отменяем отправку формы, если есть ошибки
        }
    });

    // Живая валидация для других полей (опционально, но рекомендуется)
    usernameInput.addEventListener('input', function() {
        if (usernameInput.value.trim()) {
            usernameInput.classList.remove('error');
            document.getElementById('usernameError').textContent = '';
        }
    });
    passwordInput.addEventListener('input', function() {
        if (passwordInput.value) {
            passwordInput.classList.remove('error');
            document.getElementById('passwordError').textContent = '';
            // При вводе в основном пароле тоже запускаем проверку совпадения
            validatePasswords();
        }
    });
    checkbox.addEventListener('change', function() {
        if (checkbox.checked) {
            document.getElementById('checkboxError').textContent = '';
        }
    });
});