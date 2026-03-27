# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libglib2.0-0 \
    libgl1mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies to a prefix
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Install runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY app/ /app/app/

# Pre-download the u2net model during build time
# This ensures it's baked into the image and prevents cold starts
RUN python -c "from rembg import new_session; new_session('u2net')"

# Model is cached in /root/.u2net/ by default in rembg
# Set environment variables for production
ENV PORT=8080
ENV LOG_LEVEL=info
ENV PYTHONUNBUFFERED=1
ENV DEFAULT_MODEL=u2net

# Expose the API port
EXPOSE 8080

# Run using shell form to support environment variable expansion ($PORT)
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --workers ${WORKERS:-1}"
