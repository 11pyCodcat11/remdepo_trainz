# РемДепо — Django + SQLAlchemy (async) + aiosqlite

## Быстрый старт
```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

# применяем миграции Django (для сессий/админки)
python manage.py migrate

# Запуск
python manage.py runserver 0.0.0.0:8000
```
Открой `http://localhost:8000`

### Где данные каталога?
Каталог хранится в `db_catalog.sqlite3` (SQLAlchemy + aiosqlite). При первом запросе таблицы создаются автоматически и наполняются демо-данными.

### Структура
- `catalog/models.py` — модели SQLAlchemy
- `catalog/repository.py` — асинхронные функции для чтения/записи
- `catalog/views.py` — асинхронные Django views
- `templates/` — базовые шаблоны главной и карточки товара
- `static/styles.css` — простой тёмный стиль

### Дальше
- Добавь корзину и оплату (Stripe/ЮKassa).
- Подружи Django Admin с SQLAlchemy (или перенеси каталог на Django ORM, если так удобнее).
- Разнеси категории на отдельные страницы/фильтры.