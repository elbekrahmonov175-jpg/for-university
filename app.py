import os
import uuid
from flask import Flask, render_template, redirect, url_for, flash, request, abort, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from config import Config
from models import db, User, News, File, Announcement, GalleryImage

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в аккаунт.'
login_manager.login_message_category = 'warning'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def safe_filename(filename):
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return f"{uuid.uuid4().hex}.{ext}"


# ─── Главная ─────────────────────────────────────────────
@app.route('/')
def index():
    latest_news = News.query.order_by(News.created_at.desc()).limit(5).all()
    latest_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(5).all()
    return render_template('index.html', news=latest_news, announcements=latest_announcements)


# ─── Авторизация ─────────────────────────────────────────
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm = request.form.get('confirm', '')

        if not username or not email or not password:
            flash('Заполните все поля.', 'danger')
            return redirect(url_for('register'))
        if len(password) < 6:
            flash('Пароль должен быть не менее 6 символов.', 'danger')
            return redirect(url_for('register'))
        if password != confirm:
            flash('Пароли не совпадают.', 'danger')
            return redirect(url_for('register'))
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Пользователь с таким именем или email уже существует.', 'danger')
            return redirect(url_for('register'))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Войдите в аккаунт.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Добро пожаловать!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        flash('Неверный email или пароль.', 'danger')
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта.', 'info')
    return redirect(url_for('index'))


# ─── Новости ─────────────────────────────────────────────
@app.route('/news')
def news_list():
    page = request.args.get('page', 1, type=int)
    news = News.query.order_by(News.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('news_list.html', news=news)


@app.route('/news/<int:news_id>')
def news_detail(news_id):
    article = News.query.get_or_404(news_id)
    return render_template('news_detail.html', article=article)


@app.route('/news/add', methods=['GET', 'POST'])
@login_required
def news_add():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        if not title or not content:
            flash('Заполните все поля.', 'danger')
            return redirect(url_for('news_add'))
        article = News(title=title, content=content, user_id=current_user.id)
        db.session.add(article)
        db.session.commit()
        flash('Новость опубликована!', 'success')
        return redirect(url_for('news_list'))
    return render_template('news_add.html')


# ─── Файлы и конспекты ──────────────────────────────────
@app.route('/files')
def files_list():
    course = request.args.get('course', type=int)
    subject = request.args.get('subject', '')
    query = File.query
    if course:
        query = query.filter_by(course=course)
    if subject:
        query = query.filter_by(subject=subject)
    files = query.order_by(File.uploaded_at.desc()).all()
    subjects = db.session.query(File.subject).distinct().all()
    subjects = [s[0] for s in subjects]
    return render_template('files_list.html', files=files, subjects=subjects,
                           current_course=course, current_subject=subject)


@app.route('/files/upload', methods=['GET', 'POST'])
@login_required
def files_upload():
    if request.method == 'POST':
        file = request.files.get('file')
        course = request.form.get('course', type=int)
        subject = request.form.get('subject', '').strip()
        description = request.form.get('description', '').strip()

        if not file or not course or not subject:
            flash('Заполните все обязательные поля.', 'danger')
            return redirect(url_for('files_upload'))
        if not allowed_file(file.filename, app.config['ALLOWED_FILE_EXTENSIONS']):
            flash('Недопустимый формат файла.', 'danger')
            return redirect(url_for('files_upload'))

        original_name = secure_filename(file.filename)
        filename = safe_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER_FILES'], filename)
        file.save(filepath)

        new_file = File(filename=filename, original_name=original_name or file.filename,
                        course=course, subject=subject, description=description,
                        user_id=current_user.id)
        db.session.add(new_file)
        db.session.commit()
        flash('Файл загружен!', 'success')
        return redirect(url_for('files_list'))
    return render_template('files_upload.html')


@app.route('/files/download/<int:file_id>')
def files_download(file_id):
    f = File.query.get_or_404(file_id)
    return send_from_directory(app.config['UPLOAD_FOLDER_FILES'], f.filename,
                               as_attachment=True, download_name=f.original_name)


# ─── Объявления ──────────────────────────────────────────
@app.route('/announcements')
def announcements_list():
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements_list.html', announcements=announcements)


@app.route('/announcements/add', methods=['GET', 'POST'])
@login_required
def announcements_add():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        category = request.form.get('category', 'Общее').strip()
        if not title or not content:
            flash('Заполните все поля.', 'danger')
            return redirect(url_for('announcements_add'))
        ann = Announcement(title=title, content=content, category=category, user_id=current_user.id)
        db.session.add(ann)
        db.session.commit()
        flash('Объявление опубликовано!', 'success')
        return redirect(url_for('announcements_list'))
    return render_template('announcements_add.html')


# ─── Галерея ─────────────────────────────────────────────
@app.route('/gallery')
def gallery():
    images = GalleryImage.query.order_by(GalleryImage.uploaded_at.desc()).all()
    return render_template('gallery.html', images=images)


@app.route('/gallery/upload', methods=['GET', 'POST'])
@login_required
def gallery_upload():
    if request.method == 'POST':
        file = request.files.get('image')
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        if not file or not title:
            flash('Заполните все обязательные поля.', 'danger')
            return redirect(url_for('gallery_upload'))
        if not allowed_file(file.filename, app.config['ALLOWED_IMAGE_EXTENSIONS']):
            flash('Недопустимый формат изображения.', 'danger')
            return redirect(url_for('gallery_upload'))
        filename = safe_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], filename)
        file.save(filepath)
        img = GalleryImage(filename=filename, title=title, description=description,
                           user_id=current_user.id)
        db.session.add(img)
        db.session.commit()
        flash('Изображение загружено!', 'success')
        return redirect(url_for('gallery'))
    return render_template('gallery_upload.html')


# ─── Админ-панель ────────────────────────────────────────
@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        abort(403)
    news = News.query.order_by(News.created_at.desc()).all()
    files = File.query.order_by(File.uploaded_at.desc()).all()
    announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
    images = GalleryImage.query.order_by(GalleryImage.uploaded_at.desc()).all()
    return render_template('admin.html', news=news, files=files,
                           announcements=announcements, images=images)


@app.route('/admin/delete/<string:item_type>/<int:item_id>', methods=['POST'])
@login_required
def admin_delete(item_type, item_id):
    if not current_user.is_admin:
        abort(403)
    model_map = {'news': News, 'file': File, 'announcement': Announcement, 'image': GalleryImage}
    model = model_map.get(item_type)
    if not model:
        abort(404)
    item = model.query.get_or_404(item_id)

    # Delete physical file if applicable
    if item_type == 'file':
        path = os.path.join(app.config['UPLOAD_FOLDER_FILES'], item.filename)
        if os.path.exists(path):
            os.remove(path)
    elif item_type == 'image':
        path = os.path.join(app.config['UPLOAD_FOLDER_IMAGES'], item.filename)
        if os.path.exists(path):
            os.remove(path)

    db.session.delete(item)
    db.session.commit()
    flash('Удалено.', 'success')
    return redirect(url_for('admin_panel'))


# ─── Обработка ошибок ────────────────────────────────────
@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html', code=403, message='Доступ запрещён'), 403

@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', code=404, message='Страница не найдена'), 404


# ─── Инициализация БД ────────────────────────────────────
def init_db():
    with app.app_context():
        db.create_all()
        # Создаём админа если его нет
        if not User.query.filter_by(is_admin=True).first():
            admin = User(username='admin', email='admin@titlp.uz', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('✅ Админ создан: admin@titlp.uz / admin123')


if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
