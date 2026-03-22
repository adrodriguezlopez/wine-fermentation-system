FROM python:3.11-slim

RUN pip install --upgrade pip && pip install poetry==1.8.3

WORKDIR /app

RUN poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml ./
RUN poetry install --no-root --no-interaction --without dev

COPY src/ ./src/

RUN useradd -m appuser
USER appuser

EXPOSE 8003
CMD ["uvicorn", "src.modules.analysis_engine.src.main:app", "--host", "0.0.0.0", "--port", "8003"]
