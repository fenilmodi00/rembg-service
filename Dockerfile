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

COPY requirements.txt .
# Install packages into a prefix to keep the image clean
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

# Set Hugging Face cache directory to a local path in the container
# This is used at build for pre-downloading and at runtime for serving
ENV HF_HOME=/app/models

# Install runtime system libraries (required for PIL and Torch)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /install
ENV PATH="/install/bin:$PATH"
ENV PYTHONPATH="/install/lib/python3.11/site-packages:$PYTHONPATH"

# Copy application code
COPY app/ /app/app/

# Pre-download the BIREFNET model during build time
# This ensures it's baked into the image and prevents cold starts on serverless
RUN python -c "from transformers import AutoModelForImageSegmentation; AutoModelForImageSegmentation.from_pretrained('ZhengPeng7/BiRefNet', trust_remote_code=True)"

# Environment variables for production
ENV PORT=7000
ENV LOG_LEVEL=info
ENV PYTHONUNBUFFERED=1

# Expose the API port
EXPOSE 7000

# Run the FastAPI application
CMD sh -c "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7000} --workers ${WORKERS:-1}"
