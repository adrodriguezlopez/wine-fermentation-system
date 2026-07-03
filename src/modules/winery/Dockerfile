FROM python:3.11-slim

RUN pip install --upgrade pip && pip install poetry==1.8.3

WORKDIR /app

# Disable Poetry virtualenvs (we're already inside a container)
RUN poetry config virtualenvs.create false

# Mirror the full src/ tree so that:
#   - pyproject.toml path dep "../../shared" → /app/src/modules/winery/../../shared = /app/src/shared ✓
#   - runtime imports src.modules.winery.* and src.shared.* both resolve under PYTHONPATH=/app ✓
COPY shared/ ./src/shared/
COPY modules/winery/pyproject.toml ./src/modules/winery/

WORKDIR /app/src/modules/winery
RUN poetry install --no-root --no-interaction --without dev && pip install "uvicorn[standard]>=0.23.2"

WORKDIR /app
COPY modules/winery/src/ ./src/modules/winery/src/
ENV PYTHONPATH=/app

RUN useradd -m appuser
USER appuser

EXPOSE 8001
CMD ["uvicorn", "src.modules.winery.src.main:app", "--host", "0.0.0.0", "--port", "8001"]
