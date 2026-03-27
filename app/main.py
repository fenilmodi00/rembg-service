import time
import os
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.responses import StreamingResponse
import io
import onnxruntime as ort
from app.processor import process_image

# Suppress ONNX Runtime logging issues on ARM64 workers
try:
    ort.set_default_logger_severity(3)
except Exception:
    pass

app = FastAPI(title="Background Removal Microservice")

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png", "image/jpg"]

@app.get("/health")
async def health_check():
    return {"status": "ready", "model": "birefnet-general"}

@app.get("/kaithhealth")
async def leapcell_health_check():
    return {"status": "ok"}

@app.post("/remove-background")
async def remove_background(
    file: UploadFile = File(...)
):
    # 1. Validation: Content Type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type. Only JPG and PNG are allowed.")
    
    # 2. Validation: File Size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Max size is 10MB.")
    
    # 3. Processing
    start_time = time.time()
    try:
        result_bytes = process_image(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
    
    processing_time = time.time() - start_time
    
    # 4. Response with custom headers
    return StreamingResponse(
        io.BytesIO(result_bytes),
        media_type="image/png",
        headers={
            "X-Processing-Time": f"{processing_time:.4f}s",
            "X-Model": "birefnet-general"
        }
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 7000))
    uvicorn.run(app, host="0.0.0.0", port=port)
