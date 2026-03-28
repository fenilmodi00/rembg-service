import io
import os
import torch
import gc
import time
from threading import Lock
from PIL import Image
from torchvision import transforms
from transformers import AutoModelForImageSegmentation

# 1. OPTIMIZATION: Limit PyTorch to 1 thread for serverless stability
torch.set_num_threads(1)
torch.set_grad_enabled(False)

# 2. RUNTIME CACHE: Use /tmp for lock files and metadata (writable)
# These will be used for runtime overhead, but the actual model is pre-baked in /app/models
os.environ['HF_HOME'] = '/tmp/hf_cache'
os.environ['TRANSFORMERS_CACHE'] = '/tmp/hf_cache'

# Global variables
MODEL = None
DEVICE = torch.device('cpu') 
MODEL_READY = False
MODEL_LOCK = Lock()

def load_model():
    """Explicitly load the BiRefNet model into memory from the pre-baked directory."""
    global MODEL, MODEL_READY
    
    with MODEL_LOCK:
        if MODEL_READY:
            return
            
        print(f"Loading BiRefNet Model from pre-baked cache at /app/models...")
        
        # Ensure the writable cache dir exists for HF metadata/locks
        os.makedirs('/tmp/hf_cache', exist_ok=True)
        
        try:
            # Load model pointing to the /app/models directory we created during build
            MODEL = AutoModelForImageSegmentation.from_pretrained(
                'ZhengPeng7/BiRefNet', 
                trust_remote_code=True,
                cache_dir='/app/models', 
                local_files_only=True,    # Force use of build-time cache
                low_cpu_mem_usage=True    # Requires 'accelerate'
            ).to(DEVICE)
            MODEL.eval()
            MODEL_READY = True
            print("SUCCESS: BiRefNet loaded from read-only image layer.")
        except Exception as e:
            print(f"Error loading model from image layer: {e}")
            print("Fallback: Attempting full download to /tmp... (This will be slow)")
            try:
                # Standard load as fallback if build-time cache failed
                MODEL = AutoModelForImageSegmentation.from_pretrained(
                    'ZhengPeng7/BiRefNet', 
                    trust_remote_code=True,
                    cache_dir='/tmp/models'
                ).to(DEVICE)
                MODEL.eval()
                MODEL_READY = True
                print("SUCCESS: BiRefNet loaded via fallback download.")
            except Exception as e2:
                print(f"FATAL: Model loading failed completely: {e2}")

def process_image(img_bytes):
    """
    Remove background using BiRefNet.
    Wait if the model is still loading in the background.
    """
    # Wait loop if model is loading (max 30s)
    wait_time = 0
    while not MODEL_READY and wait_time < 30:
        if wait_time == 0:
            print("Request received while model is loading... waiting.")
        time.sleep(2)
        wait_time += 2
        
    if not MODEL_READY:
        raise Exception("Model not loaded in time. Please try again in a moment.")
    
    input_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    original_size = input_image.size
    
    # Model expected input size
    input_size = (1024, 1024)
    transform = transforms.Compose([
        transforms.Resize(input_size),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    
    input_tensor = transform(input_image).unsqueeze(0).to(DEVICE)
    
    # Run inference without tracking gradients
    with torch.no_grad():
        preds = MODEL(input_tensor)[-1].sigmoid().cpu()
    
    # Process the mask
    mask = transforms.ToPILImage()(preds[0].squeeze())
    mask = mask.resize(original_size)
    
    # Create final image with transparency
    output_image = Image.open(io.BytesIO(img_bytes)).convert("RGBA")
    output_image.putalpha(mask)
    
    # Memory cleanup
    del input_tensor
    del preds
    gc.collect()
    
    img_io = io.BytesIO()
    output_image.save(img_io, format='PNG', optimize=True)
    return img_io.getvalue()
