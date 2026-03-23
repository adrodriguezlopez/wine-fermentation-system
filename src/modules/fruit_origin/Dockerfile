FROM python:3.11-slim

RUN pip install --upgrade pip && pip install poetry==1.8.3

WORKDIR /app

RUN poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-interaction --without dev

COPY src/ ./src/
ENV PYTHONPATH=/app

RUN useradd -m appuser
USER appuser

EXPOSE 8002
CMD ["uvicorn", "src.modules.fruit_origin.src.main:app", "--host", "0.0.0.0", "--port", "8002"]
