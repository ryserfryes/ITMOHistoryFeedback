# Настройка автоматического обновления через Яндекс.Формы

## 🎯 Как это работает

1. **Студент заполняет форму** → Яндекс.Формы отправляют JSON-RPC webhook
2. **Webhook handler получает уведомление** → Загружает новые данные через API
3. **Обновляет файл данных в GitHub** → Запускает GitHub Action
4. **GitHub Action регенерирует сайт** → Новый отзыв появляется на сайте

**Время обновления:** 2-3 минуты после заполнения формы

## 📋 Пошаговая настройка

### Шаг 1: Получение токенов

#### Токен GitHub:
1. Перейдите в [GitHub Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
2. Создайте новый токен с правами:
   - `repo` (полный доступ к репозиториям)
   - `workflow` (запуск GitHub Actions)
3. Сохраните токен - он понадобится для webhook

#### Токен Яндекс.Формы:
1. Откройте вашу форму в [Яндекс.Формах](https://forms.yandex.ru/)
2. Перейдите в настройки формы
3. Найдите раздел "API" или "Интеграции"
4. Создайте API токен для доступа к ответам

### Шаг 2: Развертывание webhook handler

#### Вариант A: Heroku (бесплатно)
```bash
# 1. Установите Heroku CLI
# 2. Создайте приложение
heroku create your-webhook-app-name

# 3. Установите переменные окружения
heroku config:set GITHUB_TOKEN=your_github_token
heroku config:set GITHUB_REPO=username/repo-name
heroku config:set YANDEX_API_TOKEN=your_yandex_token

# 4. Создайте Procfile
echo "web: python webhook_handler.py" > Procfile

# 5. Создайте requirements.txt
echo -e "flask\nrequests" > requirements.txt

# 6. Деплой
git add .
git commit -m "Deploy webhook handler"
git push heroku main
```

#### Вариант B: Railway (рекомендуемый)
1. Перейдите на [Railway.app](https://railway.app/)
2. Подключите ваш GitHub репозиторий
3. Установите переменные окружения:
   - `GITHUB_TOKEN` = ваш GitHub токен
   - `GITHUB_REPO` = username/repo-name
   - `YANDEX_API_TOKEN` = ваш токен Яндекс.Формы
4. Railway автоматически развернет webhook

#### Вариант C: Vercel
1. Установите Vercel CLI: `npm i -g vercel`
2. В корне проекта создайте `vercel.json`:
```json
{
  "functions": {
    "webhook_handler.py": {
      "runtime": "python3.9"
    }
  },
  "routes": [
    { "src": "/webhook/yandex-form", "dest": "/webhook_handler.py" },
    { "src": "/health", "dest": "/webhook_handler.py" }
  ]
}
```
3. Деплой: `vercel --prod`

### Шаг 3: Настройка webhook в Яндекс.Формах

1. **Откройте настройки формы** в Яндекс.Формах
2. **Найдите раздел "Действия"** или "Интеграции"
3. **Выберите "JSON-RPC"** или "Webhook"
4. **Настройте параметры:**
   - **URL:** `https://your-webhook-app.herokuapp.com/webhook/yandex-form`
   - **Метод:** `POST`
   - **Выполнять действия:** `всегда` или `при условии`
   - **Показывать сообщение о результате действия:** `Не показывать`

5. **Сохраните настройки**

### Шаг 4: Тестирование

1. **Проверьте webhook endpoint:**
```bash
curl https://your-webhook-app.herokuapp.com/health
# Должен вернуть: {"status": "ok"}
```

2. **Заполните тестовый ответ** в форме
3. **Проверьте логи webhook:**
   - Heroku: `heroku logs --tail -a your-webhook-app-name`
   - Railway: в панели управления
   - Vercel: в dashboard

4. **Проверьте GitHub Actions:**
   - Перейдите в ваш репозиторий → Actions
   - Должен запуститься workflow "Update Site Data"

## 🔧 Структура JSON-RPC запроса

Яндекс.Формы отправляют webhook в таком формате:
```json
{
  "jsonrpc": "2.0",
  "method": "form.response.created",
  "params": {
    "form_id": "68713abe90fa7b9f66ab5c53",
    "response_id": "12345",
    "created_at": "2025-01-28T10:30:00Z"
  },
  "id": "webhook-123"
}
```

## 🐛 Отладка проблем

### Webhook не срабатывает:
- Проверьте URL webhook в настройках формы
- Убедитесь, что сервис доступен: `curl https://your-app.com/health`
- Проверьте логи сервиса

### GitHub Action не запускается:
- Проверьте права токена GitHub
- Убедитесь, что `GITHUB_REPO` указан правильно (username/repo-name)
- Проверьте, что в репозитории есть файл `.github/workflows/update-data.yml`

### Данные не обновляются:
- Проверьте токен Яндекс.Формы
- Убедитесь, что ID формы правильный
- Проверьте логи webhook handler

### Проверка переменных окружения:
```bash
# Heroku
heroku config -a your-app-name

# Railway - в веб-интерфейсе
# Vercel - в dashboard
```

## 📊 Мониторинг

### Логи webhook:
- **Heroku:** `heroku logs --tail -a your-app-name`
- **Railway:** Logs в панели управления
- **Vercel:** Functions logs в dashboard

### GitHub Actions:
- Перейдите в репозиторий → Actions
- Смотрите статус последних запусков

## 🔒 Безопасность

1. **Используйте HTTPS** для webhook URL
2. **Не коммитьте токены** в код - только через переменные окружения
3. **Ограничьте права токенов** до минимально необходимых
4. **Регулярно обновляйте токены**

## 🎉 Готово!

После настройки ваш сайт будет автоматически обновляться при каждом новом ответе в форме:

1. **Студент заполняет форму** ✅
2. **Webhook получает уведомление** ✅  
3. **Данные загружаются через API** ✅
4. **GitHub обновляет файл данных** ✅
5. **Сайт перегенерируется** ✅
6. **Новый отзыв появляется на сайте** 🎯

**Время полного обновления:** 2-3 минуты