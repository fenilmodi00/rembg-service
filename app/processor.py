import io
from PIL import Image
from rembg import remove, new_session

# Global variable for the rembg session, initialized via FastAPI lifespan
SESSION = None

def load_model():
    """Explicitly load the model session."""
    global SESSION
    if SESSION is None:
        print("Loading Background Removal Model (birefnet-general)...")
        try:
            SESSION = new_session("birefnet-general")
            print("Background Removal Model loaded successfully.")
        except Exception as e:
            print(f"Error loading Background Removal Model: {e}")
            SESSION = None
    return SESSION

def process_image(image_bytes: bytes) -> bytes:
    """
    Remove background from an image using the birefnet-general model.
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
