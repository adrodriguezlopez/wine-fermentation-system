# Use multi-stage build for smaller final image
FROM python:3.9-slim as builder

# Install poetry
RUN pip install poetry

# Copy only requirements to cache them in docker layer
WORKDIR /app
COPY poetry.lock pyproject.toml ./

# Export requirements to requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Build final image
FROM python:3.9-slim

WORKDIR /app

# Copy requirements from builder
COPY --from=builder /app/requirements.txt .

# Install production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Run as non-root user
RUN useradd -m appuser
USER appuser

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
