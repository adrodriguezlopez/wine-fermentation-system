FROM python:3.11-slim

RUN pip install --upgrade pip && pip install poetry==1.8.3

WORKDIR /app

# Disable Poetry virtualenvs (we're already inside a container)
RUN poetry config virtualenvs.create false

# Mirror the full src/ tree so that:
#   - pyproject.toml path dep "../../shared" → /app/src/modules/analysis_engine/../../shared = /app/src/shared ✓
#   - runtime imports src.modules.analysis_engine.* and src.shared.* both resolve under PYTHONPATH=/app ✓
COPY shared/ ./src/shared/
COPY modules/analysis_engine/pyproject.toml ./src/modules/analysis_engine/

WORKDIR /app/src/modules/analysis_engine
RUN poetry install --no-root --no-interaction --without dev && pip install "uvicorn[standard]>=0.23.2"

WORKDIR /app
COPY modules/analysis_engine/src/ ./src/modules/analysis_engine/src/
ENV PYTHONPATH=/app

RUN useradd -m appuser
USER appuser

EXPOSE 8003
CMD ["uvicorn", "src.modules.analysis_engine.src.main:app", "--host", "0.0.0.0", "--port", "8003"]
