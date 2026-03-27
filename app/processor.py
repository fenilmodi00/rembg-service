import io
from PIL import Image
from rembg import remove, new_session

# Initialize rembg session with birefnet-general
session = new_session("birefnet-general")

def process_image(image_bytes: bytes) -> bytes:
    """
    Remove background from an image using the birefnet-general model.
    :param image_bytes: Input image data as bytes.
    :return: Output image data as bytes (PNG format).
    """
    input_image = Image.open(io.BytesIO(image_bytes))
    
    # Process the image
    output_image = remove(input_image, session=session)
    
    # Convert back to bytes
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    return output_buffer.getvalue()
