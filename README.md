# HB_bot
Бот для напоминания дней рождения.

![image_hb_bot](https://github.com/user-attachments/assets/ee323bf1-2753-4354-a8b5-3071fa4ff0e0)


## Стек технологий:

- Python 3.11.7
- Aiogram 3.10.0
- PostgreSQL 16
- Asyncpg 0.29.0
- SQLAlchemy 2.0.31
- Python-dotenv 1.0.1


> [!IMPORTANT]
> Перед всеми манипуляциями, предпологается, что Вы уже создали бота в Telegram через @BotFather.     
> Базу данных можно использовать и SQLite, просто заменив строку в настройках "DATABASE_URL" на: 
> DATABASE_URL=sqlite+aiosqlite:///db.sqlite3 


## Запуск проекта:

- Клонировать репозиторий и перейти в него в командной строке:

```python
git clone git@github.com:Saborrr/HB_bot.git
cd hb_bot
```

- Установить и активировать виртуальное окружение:

```python
python -m venv env
. env/scripts/activate
```

- Установить зависимости из файла requirements.txt

```python
python -m pip install --upgrade pip
pip install -r requirements.txt
```

- Создайте файл .env в папке hb_bot:

```python
touch .env
```

- Заполнить в настройках репозитория секреты .env:

```python
TOKEN=yourtoken_bot
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/database_name
ALLOWED_USERS=1234567,12345678
```

> [!TIP]
> Необходимо заполнить базу данных. Можно использовать SQLiteStudio или pgAdmin. 

- Запустить бота:

```python
python main.py
```

## Автор:
[Александр Санычев](https://github.com/Saborrr)
