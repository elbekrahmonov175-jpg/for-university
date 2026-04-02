[README (1).md](https://github.com/user-attachments/files/26445712/README.1.md)
# 🎓 ТИТЛП — Студенческий портал

Портал русскоязычных студентов Ташкентского института текстильной и лёгкой промышленности.

## Функционал

- 📰 **Новости** — публикация и просмотр новостей с пагинацией
- 📁 **Файлы и конспекты** — загрузка/скачивание файлов с фильтрацией по курсу и предмету
- 📢 **Объявления** — доска объявлений с категориями
- 🖼 **Галерея** — загрузка и просмотр студенческих работ
- 👤 **Авторизация** — регистрация, вход, выход
- ⚙ **Админ-панель** — управление всем контентом

## Запуск локально

### 1. Клонируйте или скачайте проект

```bash
cd student-portal
```

### 2. Создайте виртуальное окружение

```bash
python -m venv venv
source venv/bin/activate    # Linux/Mac
venv\Scripts\activate       # Windows
```

### 3. Установите зависимости

```bash
pip install -r requirements.txt
```

### 4. Запустите сервер

```bash
python app.py
```

Сервер запустится на **http://localhost:5000**

### Аккаунт администратора (создаётся автоматически)

- **Email:** `admin@titlp.uz`
- **Пароль:** `admin123`

> ⚠️ Обязательно смените пароль администратора в продакшене!

---

## Деплой на Railway

### 1. Подготовка

```bash
git init
git add .
git commit -m "Initial commit"
```

### 2. Создайте проект на Railway

1. Зайдите на [railway.app](https://railway.app/) и войдите через GitHub
2. Нажмите **"New Project"** → **"Deploy from GitHub Repo"**
3. Подключите репозиторий с проектом

### 3. Настройте переменные окружения

В разделе **Variables** добавьте:

| Переменная | Значение |
|------------|----------|
| `SECRET_KEY` | Любая длинная случайная строка (например: `python -c "import secrets; print(secrets.token_hex(32))"`) |
| `PORT` | `5000` (Railway обычно задаёт автоматически) |

### 4. Деплой

Railway автоматически обнаружит `Procfile` и `requirements.txt` и задеплоит приложение.

Сайт будет доступен по ссылке вида: `https://your-project.up.railway.app`

---

## Структура проекта

```
student-portal/
├── app.py              # Главное приложение Flask
├── config.py           # Конфигурация
├── models.py           # Модели базы данных
├── requirements.txt    # Зависимости Python
├── Procfile            # Для Railway/Heroku
├── runtime.txt         # Версия Python
├── static/
│   ├── css/style.css   # Стили
│   ├── js/main.js      # JavaScript
│   └── uploads/        # Загруженные файлы
└── templates/          # HTML-шаблоны
    ├── base.html
    ├── index.html
    ├── login.html
    ├── register.html
    ├── news_*.html
    ├── files_*.html
    ├── announcements_*.html
    ├── gallery*.html
    ├── admin.html
    └── error.html
```

## Безопасность

- Пароли хешируются через Werkzeug (pbkdf2)
- Загруженные файлы получают UUID-имена (защита от path traversal)
- Проверка расширений файлов (whitelist)
- Ограничение размера файлов — 16 МБ
- CSRF-защита через Flask-WTF (SECRET_KEY)
- Админ-панель доступна только администраторам
