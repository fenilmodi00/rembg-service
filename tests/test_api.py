import pytest
from fastapi.testclient import TestClient
from app.main import app
import io
from PIL import Image

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "model": "birefnet-general"}

def test_remove_background_valid_image():
    # Create a small valid white square image
    img = Image.new('RGB', (100, 100), color='white')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_bytes = img_byte_arr.getvalue()

    response = client.post(
        "/remove-background",
        files={"file": ("test.jpg", img_bytes, "image/jpeg")}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert "X-Processing-Time" in response.headers
    assert response.headers["X-Model"] == "birefnet-general"
    
    # Verify it's a valid PNG
    output_img = Image.open(io.BytesIO(response.content))
    assert output_img.format == "PNG"

def test_remove_background_invalid_type():
    response = client.post(
        "/remove-background",
        files={"file": ("test.txt", b"not an image", "text/plain")}
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

def test_remove_background_large_file():
    # Create a fake large file (11MB)
    large_content = b"0" * (11 * 1024 * 1024)
    response = client.post(
        "/remove-background",
        files={"file": ("large.jpg", large_content, "image/jpeg")}
    )
    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]
