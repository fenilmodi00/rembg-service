import requests
import sys
import time

URL = "http://localhost:7000/remove-background"
INPUT_FILE = "sample.jpg"
OUTPUT_FILE = "sample_processed.png"

def test_local():
    try:
        with open(INPUT_FILE, "rb") as f:
            print(f"Uploading {INPUT_FILE}...")
            start = time.time()
            response = requests.post(URL, files={"file": f})
            
        if response.status_code == 200:
            processing_time = response.headers.get("X-Processing-Time")
            print(f"Success! Server-side processing time: {processing_time}")
            print(f"Total round-trip time: {time.time() - start:.2f}s")
            
            with open(OUTPUT_FILE, "wb") as f:
                f.write(response.content)
            print(f"Processed image saved to {OUTPUT_FILE}")
        else:
            print(f"Error {response.status_code}: {response.text}")
            
    except FileNotFoundError:
        print(f"Error: {INPUT_FILE} not found. Please place an image named {INPUT_FILE} in this directory.")
    except Exception as e:
        print(f"Connection failed: {e}. Is the server running on port 7000?")

if __name__ == "__main__":
    test_local()
