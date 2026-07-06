# Stage 1 (builder)
FROM python:3.11-slim AS builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv sync (creates .venv)
RUN uv sync --no-dev

# Stage 2 (runtime)
FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

# Copy venv from builder
COPY --from=builder /app/.venv /app/.venv

# Copy app/ directory
COPY app/ app/

# Expose port
EXPOSE 8080

# Command to run uvicorn
CMD ["uvicorn", "app.fast_api_app:app", "--host", "0.0.0.0", "--port", "8080"]
