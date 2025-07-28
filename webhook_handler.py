#!/usr/bin/env python3
"""
Webhook handler для автоматического обновления при новых ответах из Яндекс.Формы
Можно развернуть на Heroku, Railway, Vercel или другом сервисе
"""

from flask import Flask, request, jsonify
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)

# Настройки GitHub
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "YOUR_GITHUB_TOKEN")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "username/repo-name")  # Замените на ваш репозиторий
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"

# Настройки Яндекс.Формы
YANDEX_FORM_ID = "68713abe90fa7b9f66ab5c53"  # ID вашей формы
YANDEX_API_TOKEN = os.environ.get("YANDEX_API_TOKEN", "YOUR_YANDEX_TOKEN")

@app.route('/webhook/yandex-form', methods=['POST'])
def handle_yandex_webhook():
    """Обрабатывает JSON-RPC webhook от Яндекс.Формы"""
    try:
        # Получаем JSON-RPC данные от Яндекс.Формы
        webhook_data = request.json
        print(f"Получен JSON-RPC webhook: {json.dumps(webhook_data, indent=2, ensure_ascii=False)}")
        
        # Проверяем, что это правильный JSON-RPC запрос
        if not webhook_data or 'method' not in webhook_data:
            return jsonify({"error": "Invalid JSON-RPC request"}), 400
        
        # Обрабатываем разные типы событий
        method = webhook_data.get('method')
        params = webhook_data.get('params', {})
        
        if method == 'form.response.created':
            print("🆕 Новый ответ на форму!")
            # Получаем полные данные формы и обновляем сайт
            success = update_site_data()
            
            if success:
                # Возвращаем успешный JSON-RPC ответ
                return jsonify({
                    "jsonrpc": "2.0",
                    "result": {"status": "success", "message": "Site updated successfully"},
                    "id": webhook_data.get('id')
                })
            else:
                return jsonify({
                    "jsonrpc": "2.0",
                    "error": {"code": -1, "message": "Failed to update site"},
                    "id": webhook_data.get('id')
                }), 500
        
        elif method == 'form.response.updated':
            print("✏️ Ответ обновлен!")
            success = update_site_data()
            return jsonify({
                "jsonrpc": "2.0",
                "result": {"status": "success", "message": "Site updated after response update"},
                "id": webhook_data.get('id')
            })
        
        else:
            print(f"ℹ️ Неизвестный метод: {method}")
            return jsonify({
                "jsonrpc": "2.0",
                "result": {"status": "ignored", "message": f"Method {method} not handled"},
                "id": webhook_data.get('id')
            })
        
    except Exception as e:
        print(f"❌ Ошибка webhook: {e}")
        return jsonify({
            "jsonrpc": "2.0",
            "error": {"code": -32603, "message": f"Internal error: {str(e)}"},
            "id": webhook_data.get('id') if webhook_data else None
        }), 500

def update_site_data():
    """Загружает новые данные из Яндекс.Формы и обновляет сайт"""
    try:
        # Загружаем данные из формы
        form_data = download_yandex_form_data()
        if not form_data:
            return False
        
        # Обновляем файл данных в GitHub
        success = update_github_data_file(form_data)
        if not success:
            return False
        
        # Запускаем GitHub Action для регенерации сайта
        trigger_github_action()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления данных: {e}")
        return False

def download_yandex_form_data():
    """Загружает данные из Яндекс.Формы через API"""
    if YANDEX_API_TOKEN == "YOUR_YANDEX_TOKEN":
        print("⚠️ Токен Яндекс.Формы не настроен")
        return None
    
    try:
        # URL для получения ответов формы
        url = f"https://api.forms.yandex.ru/v1/forms/{YANDEX_FORM_ID}/responses"
        headers = {
            'Authorization': f'Bearer {YANDEX_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        print("📥 Загрузка данных из Яндекс.Формы...")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Загружено {len(data.get('responses', []))} ответов")
            return convert_yandex_to_current_format(data)
        else:
            print(f"❌ Ошибка API Яндекс.Формы: {response.status_code}")
            print(response.text)
            return None
            
    except Exception as e:
        print(f"❌ Ошибка загрузки данных: {e}")
        return None

def convert_yandex_to_current_format(yandex_data):
    """Преобразует данные из API Яндекс.Формы в текущий формат"""
    converted_data = []
    
    if 'responses' in yandex_data:
        for response in yandex_data['responses']:
            converted_response = []
            
            # Добавляем ID и время создания
            converted_response.append(['ID', str(response.get('id', ''))])
            converted_response.append(['Время создания', response.get('created_at', '')])
            
            # Добавляем ответы на вопросы
            if 'answers' in response:
                for answer in response['answers']:
                    question_text = answer.get('question', {}).get('text', '')
                    answer_value = answer.get('value', '')
                    
                    # Обрабатываем разные типы ответов
                    if isinstance(answer_value, list):
                        # Множественный выбор
                        for value in answer_value:
                            converted_response.append([question_text, str(value)])
                    else:
                        converted_response.append([question_text, str(answer_value)])
            
            converted_data.append(converted_response)
    
    return converted_data

def update_github_data_file(data):
    """Обновляет файл данных в GitHub репозитории"""
    if GITHUB_TOKEN == "YOUR_GITHUB_TOKEN":
        print("⚠️ GitHub токен не настроен")
        return False
    
    try:
        headers = {
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Получаем текущий файл для получения SHA
        file_path = 'data/fidbek po istorii.json'
        get_url = f"{GITHUB_API_URL}/contents/{file_path}"
        
        get_response = requests.get(get_url, headers=headers)
        
        # Подготавливаем новые данные
        import base64
        new_content = json.dumps(data, ensure_ascii=False, indent=2)
        encoded_content = base64.b64encode(new_content.encode('utf-8')).decode('utf-8')
        
        # Данные для обновления файла
        update_data = {
            'message': f'Auto-update form data - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            'content': encoded_content,
            'branch': 'main'
        }
        
        # Если файл существует, добавляем SHA
        if get_response.status_code == 200:
            current_file = get_response.json()
            update_data['sha'] = current_file['sha']
        
        # Обновляем файл
        put_response = requests.put(get_url, headers=headers, json=update_data)
        
        if put_response.status_code in [200, 201]:
            print("✅ Файл данных обновлен в GitHub")
            return True
        else:
            print(f"❌ Ошибка обновления файла: {put_response.status_code}")
            print(put_response.text)
            return False
            
    except Exception as e:
        print(f"❌ Ошибка обновления GitHub: {e}")
        return False

def trigger_github_action():
    """Запускает GitHub Action для обновления сайта"""
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    data = {
        'event_type': 'update-site',
        'client_payload': {
            'timestamp': str(datetime.now())
        }
    }
    
    response = requests.post(
        f"{GITHUB_API_URL}/dispatches",
        headers=headers,
        json=data
    )
    
    if response.status_code == 204:
        print("✅ GitHub Action запущен")
        return True
    else:
        print(f"❌ Ошибка запуска GitHub Action: {response.status_code}")
        return False

@app.route('/health')
def health_check():
    """Проверка работоспособности"""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)