FROM python:3.9-slim

RUN pip install --upgrade pip && pip install poetry==1.6.1

WORKDIR /app

# Desactiva virtualenvs de Poetry
RUN poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-interaction

COPY src/ ./src/

RUN useradd -m appuser
USER appuser

CMD ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]