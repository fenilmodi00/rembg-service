import io
import os
import gc
import time
from threading import Lock
from PIL import Image

# Global variables
MODEL = None
DEVICE = None
MODEL_READY = False
MODEL_LOCK = Lock()

def load_model():
    """Lazy-initialize model and libraries to prevent startup timeout."""
    global MODEL, MODEL_READY, DEVICE
    
    with MODEL_LOCK:
        if MODEL_READY:
            return
            
        print("DEBUG: Starting lazy library imports...")
        import torch
        from transformers import AutoModelForImageSegmentation
        
        # Stability flags
        torch.set_num_threads(1)
        torch.set_grad_enabled(False)
        DEVICE = torch.device('cpu')
        
        print(f"DEBUG: Loading BiRefNet weights from {os.getenv('HF_HOME', '/app/models')}...")
        
        # Ensure directory exists if we ever write to it (logs etc)
        os.makedirs(os.getenv('HF_HOME', '/app/models'), exist_ok=True)
        
        try:
            MODEL = AutoModelForImageSegmentation.from_pretrained(
                'ZhengPeng7/BiRefNet', 
                trust_remote_code=True,
                cache_dir='/app/models', 
                local_files_only=True,
                low_cpu_mem_usage=True
            ).to(DEVICE)
            MODEL.eval()
            MODEL_READY = True
            print("SUCCESS: BiRefNet loaded and ready.")
        except Exception as e:
            print(f"ERROR: Model loading failed: {e}")

def process_image(img_bytes):
    """Remove background with lazy loading check."""
    if not MODEL_READY:
        load_model()
    
    import torch
    from torchvision import transforms
    
    input_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    original_size = input_image.size
    
    transform = transforms.Compose([
        transforms.Resize((1024, 1024)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    input_tensor = transform(input_image).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        preds = MODEL(input_tensor)[-1].sigmoid().cpu()
    
    mask = transforms.ToPILImage()(preds[0].squeeze()).resize(original_size)
    output_image = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    output_image.putalpha(mask)
    
    # Cleanup
    del input_tensor, preds
    gc.collect()
    
    img_io = io.BytesIO()
    output_image.save(img_io, format='PNG', optimize=True)
    return img_io.getvalue()
