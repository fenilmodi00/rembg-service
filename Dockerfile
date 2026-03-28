# Stage 1: Builder
FROM python:3.12-slim-bookworm as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
# Install packages into a prefix to keep the image clean
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: Runtime
FROM python:3.12-slim-bookworm

WORKDIR /app

# Set Hugging Face cache directory to a local path in the container
ENV HF_HOME=/app/models

# ARM64 Fix: satisfying the cpuinfo library used by torch/onnxruntime
# This prevents crashes/hangs in restricted serverless environments
RUN mkdir -p /sys/devices/system/cpu && \
    echo "0" > /sys/devices/system/cpu/possible && \
    echo "0" > /sys/devices/system/cpu/present && \
    echo "0" > /sys/devices/system/cpu/online

# Install runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /install
ENV PATH="/install/bin:$PATH"
ENV PYTHONPATH="/install/lib/python3.11/site-packages:/install/lib/python3.12/site-packages:$PYTHONPATH"

# Copy application code
COPY app/ /app/app/

# Pre-download the model during build time
RUN python -c "from transformers import AutoModelForImageSegmentation; AutoModelForImageSegmentation.from_pretrained('ZhengPeng7/BiRefNet', trust_remote_code=True)"

# Environment variables for production
ENV PORT=7000
ENV LOG_LEVEL=info
ENV PYTHONUNBUFFERED=1
ENV HF_HUB_OFFLINE=1

# Expose the API port
EXPOSE 7000

# Run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000", "--workers", "1"]
