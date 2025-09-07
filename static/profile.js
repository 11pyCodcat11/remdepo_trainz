const togglePassword = document.getElementById('togglePassword');
const passwordField = document.getElementById('passwordField');

togglePassword.addEventListener('click', () => {
    if (passwordField.type === 'password') {
        passwordField.type = 'text';
    } else {
        passwordField.type = 'password';
    }
});
