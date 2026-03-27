# Background Removal Microservice

FastAPI microservice using `rembg` (BiRefNet) to remove backgrounds from images. Optimized for deployment on Leapcell.

## Features
- **Engine**: uses `birefnet-general` (SOTA background removal).
- **Format**: Returns high-quality PNG with transparency.
- **Validation**: Strict file type (JPG/PNG) and size (10MB) validation.
- **Performance**: Returns processing time in `X-Processing-Time` header.
- **Leapcell Ready**: Configured for port 7000 with pre-downloaded models.

## Local Development

### 1. Installation
```bash
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

### 2. Run Locally
```bash
uvicorn app.main:app --host 0.0.0.0 --port 7000 --reload
```
The server will be available at `http://localhost:7000`.

## API Endpoints

### `GET /health`
Returns service status and model information.

### `POST /remove-background`
Accepts a multipart form file with the key `file`.
- **Allowed Types**: `image/jpeg`, `image/png`.
- **Max Size**: 10MB.
- **Returns**: PNG file.
- **Headers**:
    - `X-Processing-Time`: Server-side processing time (e.g., `1.2345s`).
    - `X-Model`: `birefnet-general`.

## Testing

### Automated Tests
```bash
pip install -r requirements-dev.txt
pytest
```

### Manual Test Script
1. Place a file named `sample.jpg` in the `rembg-service/` directory.
2. Run `python tests/test_local.py`.
3. Check `sample_processed.png`.

## Docker
Build and run locally with Docker:
```bash
docker build -t rembg-service .
docker run -p 7000:7000 rembg-service
```

## Deployment on Leapcell
1. Connect your repository to Leapcell.
2. Set the build command (if needed, though the Dockerfile is self-contained).
3. Set the port to `7000`.
4. The high-performance `birefnet-general` model is pre-downloaded during the Docker build stage for zero-latency first requests.
