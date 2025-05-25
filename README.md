# BLIP Image Captioning Microservice

A microservice that generates captions for images using the BLIP model. This service is designed to work with images that have been uploaded to the main backend service.

## Architecture

This service follows a microservice architecture:

- **Main Backend Service**: Handles file uploads, storage management, and metadata in MongoDB
- **BLIP Captioning Service**: Generates captions for images already stored in the backend/uploads directory

## API Endpoints

### Health Check
```
GET /health
```
Checks if the service is running.

### Caption a Single Image
```
POST /caption
```
Generates a caption for a single image.

**Request Body:**
```json
{
  "image_path": "path/to/image.jpg"
}
```
The `image_path` can be either:
- A full absolute path to the image
- A path relative to the backend/uploads directory

### Caption Multiple Images
```
POST /batch-caption
```
Generates captions for multiple images.

**Request Body:**
```json
{
  "image_paths": ["path/to/image1.jpg", "path/to/image2.jpg"]
}
```

### Asynchronous Batch Captioning
```
POST /async-batch-caption
```
Processes multiple images asynchronously using background tasks.

**Request Body:**
```json
{
  "image_paths": ["path/to/image1.jpg", "path/to/image2.jpg"]
}
```

## Running the Service

### Method 1: Using run.py script (recommended)
```bash
cd blip_container
python run.py
```

Additional options available:
```bash
python run.py --host 127.0.0.1 --port 8080 --reload --workers 4 --log-level debug
```

### Method 2: Using Uvicorn directly
```bash
cd blip_container
uvicorn app.main:app --reload
```

## Integration with Main Backend

This microservice is designed to be called by the main backend application when image caption generation is needed. It reads from the same `backend/uploads` directory where the main application stores uploaded files.

## Important Notes

- This service does NOT handle file uploads directly
- File uploads should be managed by the main backend service
- This service assumes images are already present in the backend/uploads directory
- The service can work with both absolute paths and paths relative to the backend/uploads directory 