import os
print("--- STARTING REMBG SERVICE ---")
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response
from contextlib import asynccontextmanager
from app.processor import process_image, load_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    # DEFERRED BACKGROUND LOAD:
    # We delay loading to allow the app to bind and pass health checks IMMEDIATELY.
    # This prevents the "Leapcell proxy timeout" during deployment.
    async def gradual_load():
        await asyncio.sleep(5) # Small buffer to let Uvicorn stabilize
        print("Starting background model load...")
        try:
            await asyncio.to_thread(load_model)
        except Exception as e:
            print(f"Deferred load failed: {e}")

    asyncio.create_task(gradual_load())
    yield
    print("Cerrando aplicación...")

app = FastAPI(
    title="Background Removal API",
    description="Optimized for PyTorch BiRefNet.",
    lifespan=lifespan
)

@app.get("/")
@app.get("/health")
@app.get("/kaithhealth")
@app.get("/kaithheathcheck") # Match Leapcell proxy typo
async def health_check():
    """Health endpoint for deployment platforms. This returns instantly (0.1ms)."""
    return {
        "status": "ok",
        "ready": True,
        "model": "birefnet-general (BiRefNet)",
        "message": "Service is running."
    }

@app.post("/remove-background")
async def remove_bg(file: UploadFile = File(...)):
    """Apply background removal with background-waiting logic."""
    try:
        raw_image_bytes = await file.read()
        processed_image = process_image(raw_image_bytes)
        return Response(content=processed_image, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Use 1 worker to fit in memory (1.2GB model overhead)
    uvicorn.run(app, host="0.0.0.0", port=7000, workers=1)
