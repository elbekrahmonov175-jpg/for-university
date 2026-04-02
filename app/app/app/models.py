from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from .database import Base

# Пользователи
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    password = Column(String)
    role = Column(String, default="user")

# Новости
class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# Файлы
class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True)
    filename = Column(String)
    course = Column(String)
    subject = Column(String)

# Объявления
class Ad(Base):
    __tablename__ = "ads"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(Text)

# Галерея
class Gallery(Base):
    __tablename__ = "gallery"

    id = Column(Integer, primary_key=True)
    image = Column(String)
