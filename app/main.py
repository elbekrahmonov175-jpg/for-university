from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import engine
from .models import Base

# Создание таблиц
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Подключение static
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Шаблоны
templates = Jinja2Templates(directory="app/templates")

# Главная страница
@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )
