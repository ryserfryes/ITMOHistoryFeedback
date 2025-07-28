#!/usr/bin/env python3
"""
Генератор статических HTML файлов для GitHub Pages
"""

import os
import shutil
from urllib.parse import quote
from main import app, LECTURERS

def safe_filename(name):
    """Создает безопасное имя файла из имени лектора"""
    # Заменяем проблемные символы
    safe_name = name.replace(' ', '_').replace('/', '_').replace('\\', '_')
    return safe_name

def generate_static_site():
    """Генерирует статический сайт"""
    
    # Удаляем старую папку docs
    if os.path.exists('docs'):
        shutil.rmtree('docs')
        print("Старая папка 'docs' удалена")
    
    # Создаем структуру папок
    os.makedirs('docs', exist_ok=True)
    os.makedirs('docs/lecturers', exist_ok=True)
    os.makedirs('docs/reviews', exist_ok=True)
    
    # Копируем статические файлы (CSS)
    if os.path.exists('static'):
        shutil.copytree('static', 'docs/static', dirs_exist_ok=True)
        print("Статические файлы (CSS/JS) скопированы")
    
    with app.app_context():
        # Генерируем главную страницу
        print("Генерация главной страницы...")
        with app.test_client() as client:
            response = client.get('/')
            with open('docs/index.html', 'w', encoding='utf-8') as f:
                f.write(response.get_data(as_text=True))
        
        # Генерируем страницу лекторов
        print("Генерация страницы лекторов...")
        with app.test_client() as client:
            response = client.get('/lecturers')
            with open('docs/lecturers/index.html', 'w', encoding='utf-8') as f:
                f.write(response.get_data(as_text=True))
        
        # Генерируем страницу отзывов
        print("Генерация страницы отзывов...")
        with app.test_client() as client:
            response = client.get('/reviews')
            with open('docs/reviews/index.html', 'w', encoding='utf-8') as f:
                f.write(response.get_data(as_text=True))
        
        # Генерируем страницы для каждого лектора
        print("Генерация страниц лекторов...")
        for lecturer_name in LECTURERS.keys():
            safe_name = safe_filename(lecturer_name)
            lecturer_dir = f'docs/lecturers/{safe_name}'
            os.makedirs(lecturer_dir, exist_ok=True)
            
            with app.test_client() as client:
                response = client.get(f'/lecturers/{lecturer_name}')
                if response.status_code == 200:
                    with open(f'{lecturer_dir}/index.html', 'w', encoding='utf-8') as f:
                        f.write(response.get_data(as_text=True))
                    print(f"  ✓ {lecturer_name}")
                else:
                    print(f"  ✗ Ошибка для {lecturer_name}: {response.status_code}")
    
    print("\n✅ Генерация завершена!")
    print("📁 Структура файлов:")
    
    # Показываем структуру
    for root, dirs, files in os.walk('docs'):
        level = root.replace('docs', '').count(os.sep)
        indent = '  ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '  ' * (level + 1)
        for file in files:
            print(f"{subindent}{file}")

def create_url_mapping():
    """Создает файл с маппингом URL для правильных ссылок"""
    mapping = {}
    for lecturer_name in LECTURERS.keys():
        safe_name = safe_filename(lecturer_name)
        mapping[lecturer_name] = safe_name
    
    # Создаем JavaScript файл с маппингом
    js_content = f"""
// URL mapping for GitHub Pages
const URL_MAPPING = {str(mapping).replace("'", '"')};

// Функция для получения правильного URL лектора
function getLecturerUrl(lecturerName) {{
    const safeName = URL_MAPPING[lecturerName];
    return safeName ? `lecturers/${{safeName}}/` : '#';
}}

// Обновляем все ссылки на лекторов при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {{
    const lecturerLinks = document.querySelectorAll('a[href*="/lecturers/"]');
    lecturerLinks.forEach(link => {{
        const href = link.getAttribute('href');
        const lecturerName = decodeURIComponent(href.split('/lecturers/')[1]);
        const newUrl = getLecturerUrl(lecturerName);
        if (newUrl !== '#') {{
            link.setAttribute('href', newUrl);
        }}
    }});
}});
"""
    
    with open('docs/static/url-mapping.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
    
    print("📝 Создан файл маппинга URL")

if __name__ == '__main__':
    generate_static_site()
    create_url_mapping()
    print("\n🚀 Сайт готов для GitHub Pages!")
    print("📋 Следующие шаги:")
    print("1. Загрузите содержимое папки 'docs' в ваш GitHub репозиторий")
    print("2. В настройках репозитория включите GitHub Pages из папки 'docs'")
    print("3. Ваш сайт будет доступен по адресу: https://[username].github.io/[repo-name]/")