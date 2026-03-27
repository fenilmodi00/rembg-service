FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for rembg/onnxruntime
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the model to avoid slow first request
# We run a small script to trigger the download
ENV U2NET_HOME=/models
RUN mkdir -p /models && python -c "from rembg import new_session; new_session('birefnet-general')"

# Copy application code
COPY . .

# Environment variables
ENV PORT=7000
ENV HOST=0.0.0.0
ENV WORKERS=2

# Expose the configured port
EXPOSE 7000

# Start uvicorn with configured workers
# Leapcell provides the PORT environment variable
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7000} --workers ${WORKERS:-2}

