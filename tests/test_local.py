import requests
import time
import os
import argparse
from PIL import Image
import io

def run_test_local(url: str, img_path: str = None):
    # 1. Health check
    print(f"Testing {url}/health...")
    try:
        r = requests.get(f"{url}/health", timeout=10.0)
        r.raise_for_status()
        print(f"Health Response: {r.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return

    # 2. Upload dummy image if no path
    if not img_path:
        print("Creating dummy 64x64 image...")
        img = Image.new("RGB", (64, 64), color="blue")
        img_bytes_io = io.BytesIO()
        img.save(img_bytes_io, format="JPEG")
        file_bytes = img_bytes_io.getvalue()
        filename = "dummy.jpg"
        ctype = "image/jpeg"
    else:
        print(f"Reading image from {img_path}...")
        with open(img_path, "rb") as f:
            file_bytes = f.read()
            filename = os.path.basename(img_path)
            # detect content type
            if filename.endswith(".png"): ctype = "image/png"
            elif filename.endswith(".webp"): ctype = "image/webp"
            else: ctype = "image/jpeg"

    # 3. Post to /remove-background
    print(f"Uploading {filename} to /remove-background...")
    start_time = time.time()
    try:
        files = {"file": (filename, file_bytes, ctype)}
        r = requests.post(f"{url}/remove-background", files=files, timeout=300.0)
        dur = time.time() - start_time
        
        if r.status_code == 200:
            print(f"Success! Status Code: 200, Latency: {dur:.2f}s")
            print(f"Response Headers: {dict(r.headers)}")
            
            output_name = "processed_" + filename.split('.')[0] + ".png"
            with open(output_name, "wb") as f:
                f.write(r.content)
            print(f"SAVED: {output_name}")
        else:
            print(f"Error {r.status_code}: {r.text}")
            
    except Exception as e:
        print(f"Background removal failed: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:7000")
    parser.add_argument("--image", help="Optional path to real test image")
    args = parser.parse_args()
    
    run_test_local(args.url, args.image)
