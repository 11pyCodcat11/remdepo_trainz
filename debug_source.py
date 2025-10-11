#!/usr/bin/env python3
"""
Отладка source параметра
"""

def debug_source_parameter():
    """Отлаживаем source параметр"""
    
    print("Отладка source параметра...")
    
    def get_back_callback(source):
        """Логика из products.py"""
        print(f"\n=== Проверка source: '{source}' ===")
        print(f"source.startswith('cat:'): {source.startswith('cat:')}")
        print(f"source == 'popular': {source == 'popular'}")
        
        if source.startswith("cat:"):
            cat_id = source.split(":")[1]
            back_callback = f"catalog:cat:{cat_id}"
            print(f"✅ Использован блок 'cat:' → back_callback = '{back_callback}'")
            return back_callback
        elif source == "popular":
            back_callback = "popular:open"
            print(f"✅ Использован блок 'popular' → back_callback = '{back_callback}'")
            return back_callback
        else:
            back_callback = "catalog:open"
            print(f"⚠️ Использован блок 'else' → back_callback = '{back_callback}'")
            return back_callback
    
    print("\n=== Тест 1: source = 'cat:4' ===")
    result1 = get_back_callback("cat:4")
    print(f"Результат: '{result1}'")
    assert result1 == "catalog:cat:4", f"Ожидалось 'catalog:cat:4', получено '{result1}'"
    
    print("\n=== Тест 2: source = 'popular' ===")
    result2 = get_back_callback("popular")
    print(f"Результат: '{result2}'")
    assert result2 == "popular:open", f"Ожидалось 'popular:open', получено '{result2}'"
    
    print("\n=== Тест 3: source = 'unknown' ===")
    result3 = get_back_callback("unknown")
    print(f"Результат: '{result3}'")
    assert result3 == "catalog:open", f"Ожидалось 'catalog:open', получено '{result3}'"
    
    print("\n🎉 Все тесты прошли!")
    print("\n=== Возможные причины проблемы ===")
    print("1. source приходит не как 'cat:4', а как-то иначе")
    print("2. source приходит пустым или None")
    print("3. source приходит с пробелами или другими символами")
    print("4. Бот не перезапущен с новым кодом")
    print("\n=== Как проверить ===")
    print("Добавьте логирование в код:")
    print("print(f'DEBUG source: {source}')")
    print("print(f'DEBUG back_callback: {back_callback}')")

if __name__ == "__main__":
    debug_source_parameter()
