import codecs
import os

os.makedirs('templates', exist_ok=True)

files = {
    'schedule.html': '''{% extends "base.html" %}
{% block title %}Расписание - ТИТЛП{% endblock %}
{% block content %}
<div class="container">
    <h1><i class="fas fa-calendar-alt"></i> Расписание занятий</h1>
    <div class="card">
        <form method="get" class="form-inline">
            <div class="form-group">
                <label>Группа:</label>
                <select name="group" class="form-control" onchange="this.form.submit()">
                    {% for group in groups %}
                    <option value="{{ group }}" {% if group == selected_group %}selected{% endif %}>{{ group }}</option>
                    {% endfor %}
                </select>
            </div>
            {% if current_user.role == 'admin' %}
            <button type="button" class="btn btn-success" onclick="document.getElementById('addModal').style.display='block'">
                <i class="fas fa-plus"></i> Добавить
            </button>
            {% endif %}
        </form>
    </div>
    {% if schedule_data %}
        {% for day, lessons in schedule_data.items() %}
        <div class="card">
            <h3>{{ day }}</h3>
            <table class="table">
                <thead><tr><th>Время</th><th>Предмет</th><th>Преподаватель</th><th>Ауд.</th>{% if current_user.role == 'admin' %}<th>Действия</th>{% endif %}</tr></thead>
                <tbody>
                    {% for lesson in lessons %}
                    <tr>
                        <td>{{ lesson.start_time }} - {{ lesson.end_time }}</td>
                        <td><strong>{{ lesson.subject }}</strong></td>
                        <td>{{ lesson.teacher or '-' }}</td>
                        <td>{{ lesson.room or '-' }}</td>
                        {% if current_user.role == 'admin' %}
                        <td><a href="{{ url_for('delete_schedule', id=lesson.id) }}" class="btn btn-danger btn-sm" onclick="return confirm('Удалить?')"><i class="fas fa-trash"></i></a></td>
                        {% endif %}
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endfor %}
    {% else %}
        <div class="card text-center"><p>Расписание пока не добавлено</p></div>
    {% endif %}
</div>
{% if current_user.role == 'admin' %}
<div id="addModal" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:2000;">
    <div style="background:white; max-width:500px; margin:50px auto; padding:2rem; border-radius:10px;">
        <h3>Добавить занятие</h3>
        <form method="post" action="{{ url_for('add_schedule') }}">
            <input type="hidden" name="group_name" value="{{ selected_group }}">
            <div class="form-group"><label>День</label><select name="day_of_week" class="form-control" required><option>Понедельник</option><option>Вторник</option><option>Среда</option><option>Четверг</option><option>Пятница</option><option>Суббота</option></select></div>
            <div class="form-group"><label>Предмет</label><input type="text" name="subject" class="form-control" required></div>
            <div class="form-group"><label>Преподаватель</label><input type="text" name="teacher" class="form-control"></div>
            <div class="form-group"><label>Аудитория</label><input type="text" name="room" class="form-control"></div>
            <div class="form-group"><label>Начало</label><input type="time" name="start_time" class="form-control" required></div>
            <div class="form-group"><label>Окончание</label><input type="time" name="end_time" class="form-control" required></div>
            <button type="submit" class="btn btn-primary">Сохранить</button>
            <button type="button" class="btn" onclick="document.getElementById('addModal').style.display='none'">Отмена</button>
        </form>
    </div>
</div>
{% endif %}
<style>.form-inline { display:flex; gap:1rem; align-items:flex-end; flex-wrap:wrap; } .btn-sm { padding:5px 10px; font-size:0.8rem; }</style>
{% endblock %}''',

    'files.html': '''{% extends "base.html" %}
{% block title %}Конспекты - ТИТЛП{% endblock %}
{% block content %}
<div class="container">
    <h1><i class="fas fa-file-alt"></i> Конспекты и файлы</h1>
    <div class="card">
        <form method="get" class="form-inline">
            <div class="form-group"><label>Курс:</label><select name="course" class="form-control"><option value="">Все</option>{% for c in courses %}<option value="{{ c }}" {% if request.args.get('course')|int == c %}selected{% endif %}>{{ c }} курс</option>{% endfor %}</select></div>
            <div class="form-group"><label>Предмет:</label><select name="subject" class="form-control"><option value="">Все</option>{% for s in subjects %}<option value="{{ s }}" {% if request.args.get('subject') == s %}selected{% endif %}>{{ s }}</option>{% endfor %}</select></div>
            <button type="submit" class="btn btn-primary">Фильтр</button>
        </form>
        {% if current_user.is_authenticated %}
        <hr><form method="post" action="{{ url_for('upload_file') }}" enctype="multipart/form-data" class="form-inline">
            <div class="form-group"><input type="file" name="file" class="form-control" required accept=".pdf,.docx,.png,.jpg"></div>
            <div class="form-group"><input type="number" name="course" placeholder="Курс" class="form-control" min="1" max="5"></div>
            <div class="form-group"><input type="text" name="subject" placeholder="Предмет" class="form-control"></div>
            <div class="form-group"><input type="text" name="description" placeholder="Описание" class="form-control"></div>
            <button type="submit" class="btn btn-success"><i class="fas fa-upload"></i> Загрузить</button>
        </form>{% endif %}
    </div>
    <div class="grid">
        {% for file in files %}
        <div class="card">
            <div style="font-size:3rem; text-align:center; color:var(--primary-color);">{% if file.filename.endswith('.pdf') %}<i class="fas fa-file-pdf"></i>{% elif file.filename.endswith('.docx') %}<i class="fas fa-file-word"></i>{% else %}<i class="fas fa-file-image"></i>{% endif %}</div>
            <h4>{{ file.original_name or file.filename }}</h4>
            <p><small>{{ file.subject or 'Без предмета' }} | {{ file.course or '?' }} курс</small></p>
            <p>{{ file.description or '' }}</p>
            <div style="display:flex; gap:0.5rem;">
                <a href="{{ url_for('download_file', id=file.id) }}" class="btn btn-primary" style="flex:1;"><i class="fas fa-download"></i> Скачать</a>
                {% if current_user.role == 'admin' %}<a href="{{ url_for('delete_file', id=file.id) }}" class="btn btn-danger" onclick="return confirm('Удалить файл?')"><i class="fas fa-trash"></i></a>{% endif %}
            </div>
        </div>{% else %}<p>Файлов пока нет</p>{% endfor %}
    </div>
</div>{% endblock %}''',

    'announcements.html': '''{% extends "base.html" %}
{% block title %}Объявления - ТИТЛП{% endblock %}
{% block content %}
<div class="container">
    <h1><i class="fas fa-bullhorn"></i> Объявления</h1>
    <div class="card" style="display:flex; gap:1rem; flex-wrap:wrap;">
        <a href="{{ url_for('announcements') }}" class="btn btn-primary">Все</a>
        <a href="{{ url_for('announcements', category='продам') }}" class="btn btn-success">Продам</a>
        <a href="{{ url_for('announcements', category='куплю') }}" class="btn btn-warning">Куплю</a>
        <a href="{{ url_for('announcements', category='ищу') }}" class="btn btn-info">Ищу</a>
        <a href="{{ url_for('announcements', category='работа') }}" class="btn btn-danger">Работа</a>
    </div>
    {% if current_user.is_authenticated %}
    <div class="card">
        <h3>Добавить объявление</h3>
        <form method="post" action="{{ url_for('add_announcement') }}">
            <div class="form-group"><input type="text" name="title" placeholder="Заголовок" class="form-control" required></div>
            <div class="form-group"><select name="category" class="form-control" required><option value="продам">Продам</option><option value="куплю">Куплю</option><option value="ищу">Ищу напарника</option><option value="работа">Подработка</option></select></div>
            <div class="form-group"><textarea name="content" placeholder="Описание" class="form-control" rows="3" required></textarea></div>
            <div class="form-group"><input type="text" name="contact_info" placeholder="Контакты" class="form-control" required></div>
            <button type="submit" class="btn btn-success">Опубликовать</button>
        </form>
    </div>{% endif %}
    {% for ann in announcements %}
    <div class="card" style="border-left:5px solid {% if ann.category == 'продам' %}#27ae60{% elif ann.category == 'куплю' %}#f39c12{% elif ann.category == 'ищу' %}#3498db{% else %}#e74c3c{% endif %};">
        <div style="display:flex; justify-content:space-between; align-items:start;">
            <div>
                <span style="background:{% if ann.category == 'продам' %}#27ae60{% elif ann.category == 'куплю' %}#f39c12{% elif ann.category == 'ищу' %}#3498db{% else %}#e74c3c{% endif %}; color:white; padding:3px 10px; border-radius:10px;">{{ ann.category }}</span>
                <h3 style="margin:0.5rem 0;">{{ ann.title }}</h3>
                <p>{{ ann.content }}</p><p><i class="fas fa-phone"></i> {{ ann.contact_info }}</p>
                <small class="text-muted">{{ ann.created_at.strftime('%d.%m.%Y %H:%M') }}</small>
            </div>
            {% if current_user.role == 'admin' or current_user.id == ann.user_id %}
            <a href="{{ url_for('delete_announcement', id=ann.id) }}" class="btn btn-danger btn-sm" onclick="return confirm('Удалить?')"><i class="fas fa-trash"></i></a>{% endif %}
        </div>
    </div>{% else %}<div class="card text-center"><p>Объявлений пока нет</p></div>{% endfor %}
</div>{% endblock %}''',

    'news.html': '''{% extends "base.html" %}
{% block title %}Новости - ТИТЛП{% endblock %}
{% block content %}
<div class="container">
    <h1><i class="fas fa-newspaper"></i> Новости</h1>
    {% if current_user.role == 'admin' %}
    <a href="{{ url_for('add_news') }}" class="btn btn-success" style="margin-bottom:1rem;"><i class="fas fa-plus"></i> Добавить новость</a>{% endif %}
    <div class="grid">
        {% for item in news %}
        <div class="card">
            {% if item.image_filename %}<img src="{{ url_for('static', filename='uploads/' + item.image_filename) }}" style="width:100%; height:200px; object-fit:cover; border-radius:5px; margin-bottom:1rem;">{% endif %}
            <h3>{{ item.title }}</h3>
            <p>{{ item.content[:200] }}{% if item.content|length > 200 %}...{% endif %}</p>
            <small class="text-muted">{{ item.created_at.strftime('%d.%m.%Y') }}</small><br><br>
            <a href="{{ url_for('news_detail', id=item.id) }}" class="btn btn-primary">Читать далее</a>
            {% if current_user.role == 'admin' %}<a href="{{ url_for('delete_news', id=item.id) }}" class="btn btn-danger" onclick="return confirm('Удалить новость?')"><i class="fas fa-trash"></i></a>{% endif %}
        </div>{% else %}<p>Новостей пока нет</p>{% endfor %}
    </div>
</div>{% endblock %}''',

    'add_news.html': '''{% extends "base.html" %}
{% block title %}Добавить новость - ТИТЛП{% endblock %}
{% block content %}
<div class="container">
    <div class="card" style="max-width:800px; margin:0 auto;">
        <h2><i class="fas fa-plus"></i> Добавить новость</h2>
        <form method="post" enctype="multipart/form-data">
            <div class="form-group"><label>Заголовок</label><input type="text" name="title" class="form-control" required></div>
            <div class="form-group"><label>Текст</label><textarea name="content" class="form-control" rows="10" required></textarea></div>
            <div class="form-group"><label>Изображение</label><input type="file" name="image" class="form-control" accept="image/*"></div>
            <button type="submit" class="btn btn-success">Опубликовать</button>
            <a href="{{ url_for('news') }}" class="btn">Отмена</a>
        </form>
    </div>
</div>{% endblock %}''',

    'news_detail.html': '''{% extends "base.html" %}
{% block title %}{{ news.title }} - ТИТЛП{% endblock %}
{% block content %}
<div class="container">
    <div class="card">
        {% if news.image_filename %}<img src="{{ url_for('static', filename='uploads/' + news.image_filename) }}" style="width:100%; max-height:400px; object-fit:cover; border-radius:10px; margin-bottom:2rem;">{% endif %}
        <h1>{{ news.title }}</h1>
        <small class="text-muted">{{ news.created_at.strftime('%d.%m.%Y') }}</small>
        <hr><p style="font-size:1.1rem; line-height:1.8;">{{ news.content }}</p><br>
        <a href="{{ url_for('news') }}" class="btn btn-primary"><i class="fas fa-arrow-left"></i> К списку</a>
    </div>
</div>{% endblock %}''',

    'gallery.html': '''{% extends "base.html" %}
{% block title %}Галерея - ТИТЛП{% endblock %}
{% block content %}
<div class="container">
    <h1><i class="fas fa-images"></i> Галерея</h1>
    {% if current_user.is_authenticated %}
    <div class="card">
        <form method="post" action="{{ url_for('upload_gallery') }}" enctype="multipart/form-data" class="form-inline">
            <div class="form-group"><input type="file" name="image" accept="image/*" class="form-control" required></div>
            <div class="form-group"><input type="text" name="caption" placeholder="Подпись" class="form-control"></div>
            <button type="submit" class="btn btn-success"><i class="fas fa-upload"></i> Загрузить</button>
        </form>
    </div>{% endif %}
    <div class="grid">
        {% for img in images %}
        <div class="card" style="padding:0; overflow:hidden;">
            <img src="{{ url_for('static', filename='uploads/' + img.filename) }}" style="width:100%; height:250px; object-fit:cover;">
            <div style="padding:1rem;"><p>{{ img.caption or 'Без подписи' }}</p><small class="text-muted">{{ img.uploaded_at.strftime('%d.%m.%Y') }}</small>
            {% if current_user.role == 'admin' %}<br><br><a href="{{ url_for('delete_gallery', id=img.id) }}" class="btn btn-danger btn-sm" onclick="return confirm('Удалить фото?')"><i class="fas fa-trash"></i> Удалить</a>{% endif %}</div>
        </div>{% else %}<p>Фотографий пока нет</p>{% endfor %}
    </div>
</div>{% endblock %}''',

    'admin.html': '''{% extends "base.html" %}
{% block title %}Админ-панель - ТИТЛП{% endblock %}
{% block content %}
<div class="container">
    <h1><i class="fas fa-cog"></i> Панель администратора</h1>
    <div class="grid">
        <div class="card text-center"><i class="fas fa-users fa-3x" style="color:var(--primary-color);"></i><h2>{{ stats.users }}</h2><p>Пользователей</p><a href="{{ url_for('admin_users') }}" class="btn btn-primary">Управление</a></div>
        <div class="card text-center"><i class="fas fa-file-alt fa-3x" style="color:#27ae60;"></i><h2>{{ stats.files }}</h2><p>Файлов</p><a href="{{ url_for('files') }}" class="btn btn-success">Перейти</a></div>
        <div class="card text-center"><i class="fas fa-bullhorn fa-3x" style="color:#f39c12;"></i><h2>{{ stats.announcements }}</h2><p>Объявлений</p><a href="{{ url_for('announcements') }}" class="btn btn-warning">Перейти</a></div>
        <div class="card text-center"><i class="fas fa-newspaper fa-3x" style="color:#e74c3c;"></i><h2>{{ stats.news }}</h2><p>Новостей</p><a href="{{ url_for('news') }}" class="btn btn-danger">Перейти</a></div>
    </div>
    <div class="card"><h3>Быстрые ссылки</h3><div style="display:flex; gap:1rem; flex-wrap:wrap;"><a href="{{ url_for('schedule') }}" class="btn btn-primary">Расписание</a><a href="{{ url_for('add_news') }}" class="btn btn-success">+ Новость</a><a href="{{ url_for('files') }}" class="btn btn-info">Файлы</a><a href="{{ url_for('gallery') }}" class="btn btn-warning">Галерея</a></div></div>
</div>{% endblock %}''',

    'admin_users.html': '''{% extends "base.html" %}
{% block title %}Управление пользователями - ТИТЛП{% endblock %}
{% block content %}
<div class="container">
    <h1><i class="fas fa-users"></i> Пользователи</h1>
    <div class="card">
        <table class="table">
            <thead><tr><th>ID</th><th>Имя</th><th>Роль</th><th>Дата</th></tr></thead>
            <tbody>
                {% for user in users %}
                <tr><td>{{ user.id }}</td><td>{{ user.username }}</td><td>{% if user.role == 'admin' %}<span style="background:#e74c3c; color:white; padding:3px 10px; border-radius:10px;">Админ</span>{% else %}<span style="background:#3498db; color:white; padding:3px 10px; border-radius:10px;">Пользователь</span>{% endif %}</td><td>{{ user.created_at.strftime('%d.%m.%Y') if user.created_at else '-' }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    <a href="{{ url_for('admin_panel') }}" class="btn btn-primary"><i class="fas fa-arrow-left"></i> Назад</a>
</div>{% endblock %}'''
}

for name, content in files.items():
    with codecs.open(f'templates/{name}', 'w', 'utf-8') as f:
        f.write(content)
    print(f'Created: {name}')

print('All files created successfully!')