# HB_bot
Бот для напоминания дней рождения.



## Стек технологий:

- Python 3.11.7
- Aiogram 3.10.0
- PostgreSQL 16
- Asyncpg 0.29.0
- SQLAlchemy 2.0.31
- Python-dotenv 1.0.1

> [!IMPORTANT]
> Перед всеми манипуляциями, предпологается, что Вы уже создали бота в Telegram через @BotFather.
> Базу данных можно использовать и SQLite, просто заменив строку в настройках "DATABASE_URL".


## Запуск проекта:

- Клонировать репозиторий и перейти в него в командной строке:

```
git clone git@github.com:Saborrr/HB_bot.git
cd hb_bot
```

- Установить и активировать виртуальное окружение:

```
python -m venv env
. env/scripts/activate
```

- Установить зависимости из файла requirements.txt

```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

- Создайте файл .env в папке hb_bot:

```
touch .env
```

- Заполнить в настройках репозитория секреты .env:

```python
TOKEN=yourtoken_bot
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/database_name
ALLOWED_USERS=1234567,12345678
```
