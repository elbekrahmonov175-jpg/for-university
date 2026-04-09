from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from datetime import datetime

app = Flask(__name__)

# ===== КОНФИГУРАЦИЯ =====
app.config['SECRET_KEY'] = 'rus_tex_secret_key_2026'

# База данных (абсолютный путь)
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, 'database', 'database.db').replace('\\', '/')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Папка для загрузок
upload_folder = os.path.join(basedir, 'uploads')
app.config['UPLOAD_FOLDER'] = upload_folder
os.makedirs(upload_folder, exist_ok=True)

# Разрешенные расширения файлов
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'png', 'jpg', 'jpeg', 'gif', 'mp4'}

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'

# ===== МОДЕЛИ =====
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_name = db.Column(db.String(50), nullable=False)
    day_of_week = db.Column(db.String(20), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    teacher = db.Column(db.String(100))
    room = db.Column(db.String(20))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    original_name = db.Column(db.String(200))
    course = db.Column(db.Integer)
    subject = db.Column(db.String(100))
    description = db.Column(db.Text)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50))
    contact_info = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image_filename = db.Column(db.String(300))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Gallery(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    caption = db.Column(db.String(300))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Доступ запрещен. Требуются права администратора.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ===== МАРШРУТЫ =====

# --- Главная ---
@app.route('/')
def index():
    latest_news = News.query.order_by(News.created_at.desc()).limit(3).all()
    return render_template('index.html', latest_news=latest_news)

# --- Авторизация ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Добро пожаловать, {user.username}!', 'success')
            return redirect(next_page if next_page else url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Пароли не совпадают', 'danger')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Такое имя пользователя уже существует', 'danger')
            return redirect(url_for('register'))
        
        user = User(
            username=username,
            password_hash=generate_password_hash(password),
            role='user'
        )
        db.session.add(user)
        db.session.commit()
        flash('Регистрация успешна! Теперь вы можете войти.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

# --- Расписание ---
@app.route('/schedule')
def schedule():
    groups = db.session.query(Schedule.group_name).distinct().all()
    groups = [g[0] for g in groups]
    selected_group = request.args.get('group', groups[0] if groups else None)
    
    schedule_data = {}
    if selected_group:
        days = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота']
        for day in days:
            lessons = Schedule.query.filter_by(
                group_name=selected_group, 
                day_of_week=day
            ).order_by(Schedule.start_time).all()
            if lessons:
                schedule_data[day] = lessons
    
    return render_template('schedule.html', 
                         groups=groups, 
                         selected_group=selected_group, 
                         schedule_data=schedule_data)

@app.route('/schedule/add', methods=['POST'])
@login_required
def add_schedule():
    if current_user.role != 'admin':
        flash('Только администратор может добавлять расписание', 'danger')
        return redirect(url_for('schedule'))
    
    lesson = Schedule(
        group_name=request.form['group_name'],
        day_of_week=request.form['day_of_week'],
        subject=request.form['subject'],
        teacher=request.form['teacher'],
        room=request.form['room'],
        start_time=request.form['start_time'],
        end_time=request.form['end_time'],
        created_by=current_user.id
    )
    db.session.add(lesson)
    db.session.commit()
    flash('Занятие добавлено', 'success')
    return redirect(url_for('schedule', group=request.form['group_name']))

@app.route('/schedule/delete/<int:id>')
@login_required
@admin_required
def delete_schedule(id):
    lesson = Schedule.query.get_or_404(id)
    group = lesson.group_name
    db.session.delete(lesson)
    db.session.commit()
    flash('Занятие удалено', 'success')
    return redirect(url_for('schedule', group=group))

# --- Файлы ---
@app.route('/files')
def files():
    course = request.args.get('course', type=int)
    subject = request.args.get('subject')
    
    query = File.query
    if course:
        query = query.filter_by(course=course)
    if subject:
        query = query.filter_by(subject=subject)
    
    files = query.order_by(File.uploaded_at.desc()).all()
    courses = db.session.query(File.course).distinct().all()
    subjects = db.session.query(File.subject).distinct().all()
    
    return render_template('files.html', 
                         files=files, 
                         courses=[c[0] for c in courses if c[0]],
                         subjects=[s[0] for s in subjects if s[0]])

@app.route('/files/upload', methods=['POST'])
@login_required
def upload_file():
    if 'file' not in request.files:
        flash('Файл не выбран', 'danger')
        return redirect(url_for('files'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Файл не выбран', 'danger')
        return redirect(url_for('files'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Добавляем timestamp чтобы избежать дублей
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        new_file = File(
            filename=filename,
            original_name=file.filename,
            course=request.form.get('course', type=int),
            subject=request.form.get('subject'),
            description=request.form.get('description'),
            uploaded_by=current_user.id
        )
        db.session.add(new_file)
        db.session.commit()
        flash('Файл загружен успешно', 'success')
    else:
        flash('Недопустимый формат файла', 'danger')
    
    return redirect(url_for('files'))

@app.route('/files/download/<int:id>')
@login_required
def download_file(id):
    file = File.query.get_or_404(id)
    return send_from_directory(app.config['UPLOAD_FOLDER'], 
                              file.filename, 
                              as_attachment=True,
                              download_name=file.original_name)

@app.route('/files/delete/<int:id>')
@login_required
@admin_required
def delete_file(id):
    file = File.query.get_or_404(id)
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    except:
        pass
    db.session.delete(file)
    db.session.commit()
    flash('Файл удален', 'success')
    return redirect(url_for('files'))

# --- Объявления ---
@app.route('/announcements')
def announcements():
    category = request.args.get('category')
    query = Announcement.query.filter_by(is_active=True)
    if category:
        query = query.filter_by(category=category)
    announcements = query.order_by(Announcement.created_at.desc()).all()
    return render_template('announcements.html', announcements=announcements)

@app.route('/announcements/add', methods=['POST'])
@login_required
def add_announcement():
    ann = Announcement(
        title=request.form['title'],
        content=request.form['content'],
        category=request.form['category'],
        contact_info=request.form['contact_info'],
        user_id=current_user.id
    )
    db.session.add(ann)
    db.session.commit()
    flash('Объявление добавлено', 'success')
    return redirect(url_for('announcements'))

@app.route('/announcements/delete/<int:id>')
@login_required
def delete_announcement(id):
    ann = Announcement.query.get_or_404(id)
    if current_user.role != 'admin' and current_user.id != ann.user_id:
        flash('У вас нет прав для удаления этого объявления', 'danger')
        return redirect(url_for('announcements'))
    db.session.delete(ann)
    db.session.commit()
    flash('Объявление удалено', 'success')
    return redirect(url_for('announcements'))

# --- Новости ---
@app.route('/news')
def news():
    all_news = News.query.order_by(News.created_at.desc()).all()
    return render_template('news.html', news=all_news)

@app.route('/news/<int:id>')
def news_detail(id):
    news_item = News.query.get_or_404(id)
    return render_template('news_detail.html', news=news_item)

@app.route('/news/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_news():
    if request.method == 'POST':
        image_filename = None
        if 'image' in request.files:
            file = request.files['image']
            if file and allowed_file(file.filename):
                image_filename = secure_filename(file.filename)
                image_filename = f"news_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image_filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        
        news = News(
            title=request.form['title'],
            content=request.form['content'],
            image_filename=image_filename,
            created_by=current_user.id
        )
        db.session.add(news)
        db.session.commit()
        flash('Новость добавлена', 'success')
        return redirect(url_for('news'))
    
    return render_template('add_news.html')

@app.route('/news/delete/<int:id>')
@login_required
@admin_required
def delete_news(id):
    news = News.query.get_or_404(id)
    if news.image_filename:
        try:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], news.image_filename))
        except:
            pass
    db.session.delete(news)
    db.session.commit()
    flash('Новость удалена', 'success')
    return redirect(url_for('news'))

# --- Галерея ---
@app.route('/gallery')
def gallery():
    images = Gallery.query.order_by(Gallery.uploaded_at.desc()).all()
    return render_template('gallery.html', images=images)

@app.route('/gallery/upload', methods=['POST'])
@login_required
def upload_gallery():
    if 'image' not in request.files:
        flash('Изображение не выбрано', 'danger')
        return redirect(url_for('gallery'))
    
    file = request.files['image']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filename = f"gallery_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        
        img = Gallery(
            filename=filename,
            caption=request.form.get('caption'),
            uploaded_by=current_user.id
        )
        db.session.add(img)
        db.session.commit()
        flash('Изображение добавлено', 'success')
    return redirect(url_for('gallery'))

@app.route('/gallery/delete/<int:id>')
@login_required
@admin_required
def delete_gallery(id):
    img = Gallery.query.get_or_404(id)
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], img.filename))
    except:
        pass
    db.session.delete(img)
    db.session.commit()
    flash('Изображение удалено', 'success')
    return redirect(url_for('gallery'))

# --- Админ-панель ---
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    stats = {
        'users': User.query.count(),
        'files': File.query.count(),
        'announcements': Announcement.query.count(),
        'news': News.query.count()
    }
    return render_template('admin.html', stats=stats)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

# ===== ИНИЦИАЛИЗАЦИЯ =====
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin)
        db.session.commit()
        print("="*50)
        print("✅ Администратор создан:")
        print("   Логин: admin")
        print("   Пароль: admin123")
        print("="*50)

if __name__ == '__main__':
    print("🚀 Сервер запускается...")
    print("Открывай в браузере: http://127.0.0.1:5000")
    app.run(debug=True, host='127.0.0.1', port=5000)