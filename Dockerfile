FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for rembg/onnxruntime
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    libatomic1 \
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
ENV PORT=8080
ENV HOST=0.0.0.0
ENV WORKERS=1
ENV OMP_NUM_THREADS=1
ENV MKL_NUM_THREADS=1
ENV OMP_DYNAMIC=TRUE

# Expose the configured port
EXPOSE 8080

# Start uvicorn without multiple workers to avoid fork-related onnxruntime issues
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]

