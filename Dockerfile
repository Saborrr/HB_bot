FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --system bot && useradd --system --gid bot --home-dir /app bot
WORKDIR /app

COPY pyproject.toml README.md LICENSE alembic.ini ./
COPY src ./src
RUN python -m pip install --disable-pip-version-check .

RUN mkdir -p /app/data && chown -R bot:bot /app
USER bot

CMD ["python", "-m", "hb_bot"]
