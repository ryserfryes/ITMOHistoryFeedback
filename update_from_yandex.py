#!/usr/bin/env python3
"""
Скрипт для автоматического обновления данных из Яндекс.Формы
"""

import requests
import json
import os
from datetime import datetime

# Настройки (нужно будет заполнить)
YANDEX_FORM_API_URL = "https://api.forms.yandex.ru/v1/forms/{FORM_ID}/responses"
API_TOKEN = "YOUR_API_TOKEN_HERE"  # Токен от Яндекс.Формы
FORM_ID = "68713abe90fa7b9f66ab5c53"  # ID вашей формы

def download_responses():
    """Загружает ответы из Яндекс.Формы"""
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        print("Загрузка данных из Яндекс.Формы...")
        response = requests.get(YANDEX_FORM_API_URL.format(FORM_ID=FORM_ID), headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"Ошибка API: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"Ошибка при загрузке: {e}")
        return None

def convert_to_current_format(yandex_data):
    """Преобразует данные из формата Яндекс.Формы в текущий формат"""
    # Здесь нужно будет адаптировать под реальную структуру API Яндекс.Формы
    converted_data = []
    
    if 'responses' in yandex_data:
        for response in yandex_data['responses']:
            # Преобразуем каждый ответ в формат [[вопрос, ответ], ...]
            converted_response = []
            
            # Добавляем ID и время создания
            converted_response.append(['ID', response.get('id', '')])
            converted_response.append(['Время создания', response.get('created_at', '')])
            
            # Добавляем ответы на вопросы
            if 'answers' in response:
                for answer in response['answers']:
                    question = answer.get('question', {}).get('text', '')
                    value = answer.get('value', '')
                    converted_response.append([question, value])
            
            converted_data.append(converted_response)
    
    return converted_data

def save_data(data):
    """Сохраняет данные в JSON файл"""
    os.makedirs('data', exist_ok=True)
    
    with open('data/fidbek po istorii.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Данные сохранены: {len(data)} ответов")

def update_site():
    """Обновляет статический сайт"""
    print("Генерация статических файлов...")
    os.system('python generate_static.py')

def main():
    """Основная функция"""
    print(f"🔄 Обновление данных - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Проверяем наличие токена
    if API_TOKEN == "YOUR_API_TOKEN_HERE":
        print("❌ Необходимо настроить API_TOKEN в скрипте")
        print("📋 Инструкция:")
        print("1. Получите токен API в настройках Яндекс.Формы")
        print("2. Замените YOUR_API_TOKEN_HERE на ваш токен")
        return
    
    # Загружаем данные
    yandex_data = download_responses()
    if not yandex_data:
        print("❌ Не удалось загрузить данные")
        return
    
    # Преобразуем в нужный формат
    converted_data = convert_to_current_format(yandex_data)
    
    # Сохраняем данные
    save_data(converted_data)
    
    # Обновляем сайт
    update_site()
    
    print("🎉 Обновление завершено!")

if __name__ == '__main__':
    main()