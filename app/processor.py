import io
from PIL import Image
from rembg import remove, new_session

print("Loading Background Removal Model (u2net)...")
try:
    SESSION = new_session("u2net")
    print("Background Removal Model loaded successfully.")
except Exception as e:
    print(f"Error loading Background Removal Model: {e}")
    SESSION = None

def process_image(image_bytes: bytes) -> bytes:
    """
    Remove background from an image using the u2net model.
    :param image_bytes: Input image data as bytes.
    :return: Output image data as bytes (PNG format).
    """
    # 1. Convert to RGB PIL Image
    input_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    
    # 2. Process the image using the pre-loaded SESSION
    if SESSION is None:
        raise RuntimeError("Background Removal Model session is not initialized.")
        
    output_image = remove(input_image, session=SESSION)
    
    # 3. Convert back to bytes (PNG)
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    return output_buffer.getvalue()
