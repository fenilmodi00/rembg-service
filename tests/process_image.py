import sys
import os
from rembg import remove, new_session
from PIL import Image
import time

def process():
    input_path = 'image.png'
    output_path = 'image_processed.png'
    
    if not os.path.exists(input_path):
        print(f"Error: {input_path} not found.")
        return

    print(f"Loading model and processing {input_path}...")
    start_time = time.time()
    
    # Use the high-quality BiRefNet model
    session = new_session("birefnet-general")
    
    with open(input_path, 'rb') as i:
        input_data = i.read()
        output_data = remove(input_data, session=session)
        
    with open(output_path, 'wb') as o:
        o.write(output_data)
        
    end_time = time.time()
    print(f"Done! Processed in {end_time - start_time:.2f} seconds.")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    process()
