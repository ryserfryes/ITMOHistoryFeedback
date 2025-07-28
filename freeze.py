from flask_frozen import Freezer
from main import app, LECTURERS
import os
import shutil
from urllib.parse import quote

# Настройка Freezer
app.config['FREEZER_DESTINATION'] = 'docs'  # GitHub Pages читает из папки docs
app.config['FREEZER_RELATIVE_URLS'] = True
app.config['FREEZER_DESTINATION_IGNORE'] = ['.git*']
app.config['FREEZER_DEFAULT_MIMETYPE'] = 'text/html'
freezer = Freezer(app)

@freezer.register_generator
def lecturer_detail():
    """Генерирует URL для всех страниц лекторов"""
    for lecturer_name in LECTURERS.keys():
        yield {'name': lecturer_name}

if __name__ == '__main__':
    # Удаляем старую папку docs если она существует
    if os.path.exists('docs'):
        shutil.rmtree('docs')
        print("Старая папка 'docs' удалена")
    
    # Создаем новую папку docs
    os.makedirs('docs')
    print("Создана новая папка 'docs'")
    
    try:
        # Генерируем статические файлы
        print("Генерация статических файлов...")
        freezer.freeze()
        print("✅ Статические файлы успешно созданы в папке 'docs'")
        print("📁 Структура файлов:")
        
        # Показываем структуру созданных файлов
        for root, dirs, files in os.walk('docs'):
            level = root.replace('docs', '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        print("\n🚀 Теперь можно загрузить содержимое папки 'docs' на GitHub Pages")
        
    except Exception as e:
        print(f"❌ Ошибка при генерации: {e}")
        print("Попробуйте запустить скрипт еще раз")