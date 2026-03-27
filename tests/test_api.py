import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
import io
from PIL import Image

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "birefnet-general" in response.json()["model"]

@pytest.mark.asyncio
async def test_remove_background_validation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Invalid Content-Type
        files = {"file": ("test.txt", b"hello world", "text/plain")}
        response = await ac.post("/remove-background", files=files)
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

        # 2. Too large file
        # Default is 10MB. Let's send 11MB.
        files = {"file": ("large.jpg", b"0" * (11 * 1024 * 1024), "image/jpeg")}
        response = await ac.post("/remove-background", files=files)
        assert response.status_code == 400
        assert "File too large" in response.json()["detail"]

@pytest.mark.asyncio
async def test_remove_background_success():
    # Needs actual model loading which is slow.
    # In a real CI environment, we might mock `process_image`.
    # But for a full test, we send a 1x1 JPG.
    img = Image.new("RGB", (10, 10), color="red")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=30.0) as ac:
        files = {"file": ("small.jpg", img_bytes, "image/jpeg")}
        response = await ac.post("/remove-background", files=files)
        
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "X-Processing-Time" in response.headers
    assert response.headers["X-Model"] == "birefnet-general"
    
    # Check if we got a valid PNG back
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.format == "PNG"
