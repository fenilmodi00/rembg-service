import os
# Set environment variables BEFORE importing onnxruntime
os.environ['ORT_LOGGING_LEVEL'] = '3'
os.environ['ONNXRUNTIME_LOGGER_SEVERITY'] = '3'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['ORT_ENABLE_MEM_PATTERN'] = '0'

import time
from fastapi import FastAPI, UploadFile, File, HTTPException, Response
import io

# Explicitly try to silence ONNX Runtime if possible
try:
    import onnxruntime as ort
    ort.set_default_logger_severity(3)
except Exception:
    pass

from app.processor import process_image

# Load environment variables early
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(
    title="rembg Background Removal API",
    version="1.0.0",
    description="CPU-based background removal using u2net model"
)

# Configuration from environment
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 10))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png", "image/webp"]

@app.get("/health")
@app.get("/kaithhealthcheck") # Match Leapcell proxy
async def health_check():
    """Health check endpoint for Leapcell and internal monitoring."""
    return {
        "status": "ok", 
        "model": "u2net", 
        "ready": True
    }

@app.post("/remove-background")
async def remove_background(file: UploadFile = File(...)):
    """
    Remove background from the uploaded image.
    Accepts: jpg, png, webp.
    Returns: Transparent PNG.
    """
    start_time = time.time()
    
    # 1. Validation: Content Type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type: {file.content_type}. Supported types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )
    
    # 2. Validation: File Size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large. Maximum size allowed is {MAX_FILE_SIZE_MB}MB."
        )
    
    try:
        # 3. Process the image
        processed_bytes = process_image(content)
        
        processing_time = round(time.time() - start_time, 3)
        print(f"Processed {file.filename} in {processing_time}s")
        
        # 4. Return the processed image with required headers
        return Response(
            content=processed_bytes,
            media_type="image/png",
            headers={
                "X-Processing-Time": f"{processing_time}s",
                "X-Model": "u2net"
            }
        )
        
    except Exception as e:
        print(f"Error processing image {file.filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Make default port 7000 to match current dashboard/proxy config
    port = int(os.getenv("PORT", 7000))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level=log_level)
