FROM python:3.11-slim

RUN pip install --upgrade pip && pip install poetry==1.8.3

WORKDIR /app

# Disable Poetry virtualenvs (we're already inside a container)
RUN poetry config virtualenvs.create false

# Mirror the full src/ tree so that:
#   - pyproject.toml path dep "../../shared" → /app/src/modules/fruit_origin/../../shared = /app/src/shared ✓
#   - runtime imports src.modules.fruit_origin.* and src.shared.* both resolve under PYTHONPATH=/app ✓
COPY shared/ ./src/shared/
COPY modules/fruit_origin/poetry.lock modules/fruit_origin/pyproject.toml ./src/modules/fruit_origin/

WORKDIR /app/src/modules/fruit_origin
RUN poetry install --no-root --no-interaction --without dev

WORKDIR /app
COPY modules/fruit_origin/src/ ./src/modules/fruit_origin/src/
ENV PYTHONPATH=/app

RUN useradd -m appuser
USER appuser

EXPOSE 8002
CMD ["uvicorn", "src.modules.fruit_origin.src.main:app", "--host", "0.0.0.0", "--port", "8002"]
