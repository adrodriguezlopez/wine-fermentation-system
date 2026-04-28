FROM python:3.11-slim

RUN pip install --upgrade pip && pip install poetry==1.8.3

WORKDIR /app

# Disable Poetry virtualenvs (we're already inside a container)
RUN poetry config virtualenvs.create false

# Mirror the full src/ tree so that:
#   - pyproject.toml path dep "../../shared" → /app/src/modules/fermentation/../../shared = /app/src/shared ✓
#   - runtime imports src.modules.fermentation.* and src.shared.* both resolve under PYTHONPATH=/app ✓
COPY shared/ ./src/shared/
COPY modules/fermentation/poetry.lock modules/fermentation/pyproject.toml ./src/modules/fermentation/

WORKDIR /app/src/modules/fermentation
RUN poetry install --no-root --no-interaction

WORKDIR /app
COPY modules/fermentation/src/ ./src/modules/fermentation/src/
ENV PYTHONPATH=/app

RUN useradd -m appuser
USER appuser

EXPOSE 8000
CMD ["uvicorn", "src.modules.fermentation.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
