# Background Removal Service Guide

This guide explains how to deploy and use your background removal microservice.

## How it Works (Technical)

The service utilizes the **rembg** library, configured with the **birefnet-general** (Bilateral Reference Network) model.

### The Algorithm
- **Segmentation**: The model performs pixel-level segmentation to identify foreground objects.
- **BiRefNet**: This specific model is designed for high-resolution background removal by focusing on both global context (to find the object) and local details (to refine edges like hair or glass).
- **Alpha Mask**: It generates an "alpha matte" (transparency map) which is then applied to the original image to create a transparent PNG.

---

## The API Process
1.  **POST Request**: Send a multipart/form-data request to the `/remove-background` endpoint.
2.  **Validation**: The server checks if the file is an image (JPG/PNG) and under 10MB.
3.  **Processing**: The AI model processes the image buffer in memory.
4.  **Response**: The server streams back the processed PNG image.

---

## Deployment Options

### Docker (Recommended)
You can deploy this as a Docker container to any cloud provider (Leapcell, Google Cloud Run, AWS App Runner).

1.  **Build the Image**:
    ```bash
    docker build -t rembg-service .
    ```
2.  **Run Locally**:
    ```bash
    docker run -p 7000:7000 rembg-service
    ```

### Leapcell / Serverless (Optimized)
This microservice is pre-configured for [Leapcell](https://leapcell.io):
1.  **Connect Repo**: Connect your GitHub repository.
2.  **Select Runtime**: Choose `Docker` (ensures system dependencies for `rembg` are met).
3.  **Environment Variables**:
    - `PORT`: Automatically handled.
    - `WORKERS`: Set to `1` or `2` (default `2`).
4.  **Health Check**: The service exposes `/kaithhealth` for Leapcell's required health checks.
5.  **Model Persistence**: The `Dockerfile` handles pre-downloading models, so deployment is ready out-of-the-box.


---

## Calling the Service from a Mobile App

To use this in your app (Flutter, React Native, etc.), you make a **POST** request with **FormData**.

### Flutter Example
```dart
import 'package:http/http.dart' as http;

Future<void> removeBackground(String imagePath) async {
  var request = http.MultipartRequest(
    'POST', 
    Uri.parse('https://your-service-url/remove-background')
  );
  
  // Add the image file
  request.files.add(await http.MultipartFile.fromPath('file', imagePath));

  var response = await request.send();

  if (response.statusCode == 200) {
    // Process the resulting image bytes
    final bytes = await response.stream.toBytes();
    // Save or display the image...
  }
}
```

### React Native Example
```javascript
const formData = new FormData();
formData.append('file', {
  uri: imageUri,
  type: 'image/jpeg',
  name: 'photo.jpg',
});

const response = await fetch('https://your-service-url/remove-background', {
  method: 'POST',
  headers: {
    'Content-Type': 'multipart/form-data',
  },
  body: formData,
});

const blob = await response.blob();
// Use the result...
```

---

## Testing Locally
You can test the API using `curl`:

```bash
curl -X POST "http://localhost:7000/remove-background" \
     -F "file=@image.jpg" \
     --output result.png
```
