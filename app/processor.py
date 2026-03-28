import io
import torch
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation

# Global variable for the BiRefNet model, initialized via FastAPI lifespan
MODEL = None
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

def load_model():
    """Explicitly load the BiRefNet model using Transformers/PyTorch."""
    global MODEL
    if MODEL is None:
        print("Loading BiRefNet Model (Torch Engine)...")
        try:
            # We use the native Transformers loader for memory efficiency and ARM64 compatibility
            # 'ZhengPeng7/BiRefNet' is the flagship general purpose model for high quality segmentation
            MODEL = AutoModelForImageSegmentation.from_pretrained(
                'ZhengPeng7/BiRefNet', 
                trust_remote_code=True
            ).to(DEVICE)
            MODEL.eval()
            print("Background Removal Model (BiRefNet) loaded successfully.")
        except Exception as e:
            print(f"Error loading Background Removal Model: {e}")
            MODEL = None
    return MODEL

def process_image(image_bytes: bytes) -> bytes:
    """
    Remove background from an image using the BiRefNet PyTorch model.
    100% equivalent in quality to 'rembg' with birefnet-general.
    :param image_bytes: Input image data as bytes.
    :return: Output image data as bytes (PNG format).
    """
    if MODEL is None:
        raise RuntimeError("Background Removal Model is not initialized.")

    # 1. Load image and keep original size for mask rescaling
    input_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    original_size = input_image.size

    # 2. Standard Pre-processing for BiRefNet
    transform_image = transforms.Compose([
        transforms.Resize((1024, 1024)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    # Process image through model
    input_tensor = transform_image(input_image).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        # BiRefNet returns a list of maps; the last one is the final result
        preds = MODEL(input_tensor)[-1].sigmoid().cpu()

    # 3. Create Alpha Mask and Post-process
    pred_mask = preds[0].squeeze()
    mask_pil = transforms.ToPILImage()(pred_mask).resize(original_size, Image.BILINEAR)

    # 4. Apply Mask to create transparent PNG
    output_image = input_image.copy()
    output_image.putalpha(mask_pil)

    # 5. Convert back to bytes (PNG)
    output_buffer = io.BytesIO()
    output_image.save(output_buffer, format="PNG")
    return output_buffer.getvalue()
