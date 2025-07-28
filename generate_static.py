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

def fix_github_pages_links(html_content, current_path=""):
    """Исправляет ссылки для работы на GitHub Pages"""
    import re
    
    # Определяем базовый путь в зависимости от текущей страницы
    if current_path == "":  # главная страница
        base_path = "./"
    elif current_path in ["lecturers", "reviews"]:  # страницы первого уровня
        base_path = "../"
    else:  # страницы лекторов (lecturers/name/)
        base_path = "../../"
    
    # Исправляем ссылки на статические файлы
    html_content = re.sub(r'href="/static/', f'href="{base_path}static/', html_content)
    html_content = re.sub(r'src="/static/', f'src="{base_path}static/', html_content)
    
    # Исправляем навигационные ссылки с учетом APPLICATION_ROOT
    # Заменяем абсолютные пути с APPLICATION_ROOT на относительные
    if current_path == "":
        html_content = re.sub(r'href="/ITMOHistoryFeedback/"', 'href="index.html"', html_content)
        html_content = re.sub(r'href="/ITMOHistoryFeedback/lecturers"', 'href="lecturers/"', html_content)
        html_content = re.sub(r'href="/ITMOHistoryFeedback/reviews"', 'href="reviews/"', html_content)
        # Также обрабатываем старые пути без APPLICATION_ROOT
        html_content = re.sub(r'href="/"', 'href="index.html"', html_content)
        html_content = re.sub(r'href="/lecturers"', 'href="lecturers/"', html_content)
        html_content = re.sub(r'href="/reviews"', 'href="reviews/"', html_content)
    elif current_path in ["lecturers", "reviews"]:
        html_content = re.sub(r'href="/ITMOHistoryFeedback/"', 'href="../"', html_content)
        html_content = re.sub(r'href="/ITMOHistoryFeedback/lecturers"', 'href="../lecturers/"', html_content)
        html_content = re.sub(r'href="/ITMOHistoryFeedback/reviews"', 'href="../reviews/"', html_content)
        # Также обрабатываем старые пути без APPLICATION_ROOT
        html_content = re.sub(r'href="/"', 'href="../"', html_content)
        html_content = re.sub(r'href="/lecturers"', 'href="../lecturers/"', html_content)
        html_content = re.sub(r'href="/reviews"', 'href="../reviews/"', html_content)
    else:  # страницы лекторов
        html_content = re.sub(r'href="/ITMOHistoryFeedback/"', 'href="../../"', html_content)
        html_content = re.sub(r'href="/ITMOHistoryFeedback/lecturers"', 'href="../../lecturers/"', html_content)
        html_content = re.sub(r'href="/ITMOHistoryFeedback/reviews"', 'href="../../reviews/"', html_content)
        # Также обрабатываем старые пути без APPLICATION_ROOT
        html_content = re.sub(r'href="/"', 'href="../../"', html_content)
        html_content = re.sub(r'href="/lecturers"', 'href="../../lecturers/"', html_content)
        html_content = re.sub(r'href="/reviews"', 'href="../../reviews/"', html_content)
    
    # Исправляем ссылки на лекторов
    for lecturer_name in LECTURERS.keys():
        safe_name = safe_filename(lecturer_name)
        encoded_name = quote(lecturer_name.encode('utf-8'))
        
        # Заменяем ссылки вида /lecturers/Имя%20Лектора на относительные пути
        pattern = f'href="/lecturers/{re.escape(encoded_name)}"'
        if current_path == "":  # с главной страницы
            replacement = f'href="lecturers/{safe_name}/"'
        elif current_path == "lecturers":  # со страницы списка лекторов
            replacement = f'href="{safe_name}/"'
        else:  # с других страниц
            replacement = f'href="../{safe_name}/"'
        
        html_content = re.sub(pattern, replacement, html_content)
        
        # Также обрабатываем не-encoded версии
        pattern2 = f'href="/lecturers/{re.escape(lecturer_name)}"'
        html_content = re.sub(pattern2, replacement, html_content)
    
    return html_content

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
            html_content = response.get_data(as_text=True)
            fixed_html = fix_github_pages_links(html_content, "")
            with open('docs/index.html', 'w', encoding='utf-8') as f:
                f.write(fixed_html)
        
        # Генерируем страницу лекторов
        print("Генерация страницы лекторов...")
        with app.test_client() as client:
            response = client.get('/lecturers')
            html_content = response.get_data(as_text=True)
            fixed_html = fix_github_pages_links(html_content, "lecturers")
            with open('docs/lecturers/index.html', 'w', encoding='utf-8') as f:
                f.write(fixed_html)
        
        # Генерируем страницу отзывов
        print("Генерация страницы отзывов...")
        with app.test_client() as client:
            response = client.get('/reviews')
            html_content = response.get_data(as_text=True)
            fixed_html = fix_github_pages_links(html_content, "reviews")
            with open('docs/reviews/index.html', 'w', encoding='utf-8') as f:
                f.write(fixed_html)
        
        # Генерируем страницы для каждого лектора
        print("Генерация страниц лекторов...")
        for lecturer_name in LECTURERS.keys():
            safe_name = safe_filename(lecturer_name)
            lecturer_dir = f'docs/lecturers/{safe_name}'
            os.makedirs(lecturer_dir, exist_ok=True)
            
            with app.test_client() as client:
                response = client.get(f'/lecturers/{lecturer_name}')
                if response.status_code == 200:
                    html_content = response.get_data(as_text=True)
                    fixed_html = fix_github_pages_links(html_content, f"lecturers/{safe_name}")
                    with open(f'{lecturer_dir}/index.html', 'w', encoding='utf-8') as f:
                        f.write(fixed_html)
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