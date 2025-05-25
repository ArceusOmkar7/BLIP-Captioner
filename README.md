# BLIP Image Captioning Microservice

A microservice that generates captions for images using the Salesforce BLIP (Bootstrapping Language-Image Pre-training) model. This service is designed to receive image paths, process the images, and return generated captions. It can be run locally or as a containerized application.

## Features

*   Generates descriptive captions for images.
*   Supports single image captioning and batch processing.
*   Offers asynchronous batch captioning for non-blocking operations.
*   Configurable host, port, worker count, and logging level.
*   Includes Dockerfiles for CPU and GPU environments.
*   Basic health check endpoint.

## Architecture

This service is intended to function as a specialized microservice, potentially as part of a larger system:

-   **Image Source**: Assumes images are accessible via a file path. This path can be absolute or relative to a predefined directory if integrated with another service (e.g., `backend/uploads` as mentioned in original notes).
-   **BLIP Captioning Service**: This application, which loads the BLIP model and exposes API endpoints to generate captions.
-   **(Optional) Main Backend Service**: In a larger setup, another service might handle file uploads, user authentication, database interactions, and then call this microservice for captioning tasks.

## Prerequisites

*   Python 3.8+
*   pip (Python package installer)
*   Git (for cloning the repository)
*   Docker (optional, for containerized deployment)
*   NVIDIA GPU and NVIDIA drivers with CUDA support (optional, for GPU-accelerated inference with `Dockerfile.gpu`)

## Setup and Installation

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone <repository-url>
    cd BLIP-Captioner # Or your repository's directory name
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows
    venv\Scripts\activate
    # On macOS/Linux
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    The project uses `requirements.txt` to manage dependencies.
    ```bash
    pip install -r requirements.txt
    ```

## Running the Service

The service is started using the `run.py` script, which provides several command-line options for configuration.

### Using `run.py` script (recommended for local development)

Navigate to the root directory of the project (e.g., `BLIP-Captioner`) where `run.py` is located.

**Basic command:**
```bash
python run.py
```
This will start the service on `0.0.0.0:8000` by default.

**Available command-line arguments for `run.py`:**

*   `--host TEXT`: Host to bind the server to. (Default: `0.0.0.0`)
    ```bash
    python run.py --host 127.0.0.1
    ```
*   `--port INTEGER`: Port to bind the server to. (Default: `8000`)
    ```bash
    python run.py --port 8080
    ```
*   `--reload`: Enable auto-reload on code changes. Useful for development.
    ```bash
    python run.py --reload
    ```
*   `--workers INTEGER`: Number of worker processes for Uvicorn. (Default: `1`)
    ```bash
    python run.py --workers 4
    ```
*   `--log-level TEXT`: Logging level (e.g., `debug`, `info`, `warning`, `error`, `critical`). (Default: `info`)
    ```bash
    python run.py --log-level debug
    ```

**Example with multiple options:**
```bash
python run.py --host 127.0.0.1 --port 8080 --reload --workers 2 --log-level debug
```

### Using Uvicorn directly

You can also run the application directly with Uvicorn, though `run.py` is preferred as it ensures the correct working directory.
```bash
# Ensure you are in the directory containing the 'app' folder
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

The service exposes the following API endpoints:

### Health Check

*   **Endpoint:** `GET /health`
*   **Description:** Checks if the service is running and responsive.
*   **Response (200 OK):**
    ```json
    {
      "status": "healthy"
    }
    ```

### Caption a Single Image

*   **Endpoint:** `POST /caption`
*   **Description:** Generates a caption for a single image.
*   **Request Body:**
    ```json
    {
      "image_path": "path/to/your/image.jpg"
    }
    ```
    The `image_path` should be an absolute path or a path accessible by the server.
*   **Response (200 OK):**
    ```json
    {
      "image_path": "path/to/your/image.jpg",
      "caption": "A descriptive caption of the image."
    }
    ```
*   **Error Response (e.g., 404 Not Found if image_path is invalid, 500 for processing errors):**
    ```json
    {
      "detail": "Error message"
    }
    ```

### Caption Multiple Images (Batch Processing)

*   **Endpoint:** `POST /batch-caption`
*   **Description:** Generates captions for multiple images in a single request. Processed sequentially in the request-response cycle.
*   **Request Body:**
    ```json
    {
      "image_paths": [
        "path/to/image1.jpg",
        "path/to/image2.jpg",
        "path/to/another/image.png"
      ]
    }
    ```
*   **Response (200 OK):**
    ```json
    [
      {
        "image_path": "path/to/image1.jpg",
        "caption": "Caption for image 1."
      },
      {
        "image_path": "path/to/image2.jpg",
        "caption": "Caption for image 2."
      },
      {
        "image_path": "path/to/another/image.png",
        "caption": "Caption for another image."
      }
    ]
    ```

### Asynchronous Batch Captioning

*   **Endpoint:** `POST /async-batch-caption`
*   **Description:** Accepts multiple images for captioning and processes them asynchronously using background tasks. This endpoint returns immediately with a task ID.
*   **Request Body:**
    ```json
    {
      "image_paths": [
        "path/to/image1.jpg",
        "path/to/image2.jpg"
      ]
    }
    ```
*   **Response (202 Accepted):**
    ```json
    {
      "message": "Batch captioning started in the background.",
      "task_id": "some-unique-task-id"
      // You might need another endpoint to check the status/result of this task_id
    }
    ```
    *(Note: The actual implementation of task status checking is not detailed here but would be a common pattern for async tasks.)*

    **Update (May 2024):** The asynchronous batch captioning endpoint has been enhanced for robustness. Uploaded images are now saved to temporary storage before being queued for background processing. This ensures that the image files are reliably available to the background worker, mitigating issues with temporary file lifecycles. The `task_id` returned can be used with the `/async-batch-caption/status/{task_id}` endpoint to retrieve results.

### Check Asynchronous Task Status

*   **Endpoint:** `GET /task-status/{task_id}`
*   **Description:** Checks the status of an asynchronous captioning task and retrieves results if completed.
*   **Path Parameter:**
    *   `task_id`: The ID of the task returned by the `/async-batch-caption` endpoint.
*   **Response (200 OK):**
    ```json
    {
      "task_id": "some-unique-task-id",
      "status": "completed",  // or "in_progress", "failed", etc.
      "results": [
        {
          "image_path": "path/to/image1.jpg",
          "caption": "Caption for image 1."
        },
        {
          "image_path": "path/to/image2.jpg",
          "caption": "Caption for image 2."
        }
      ]
    }
    ```
*   **Error Response (e.g., 404 Not Found if task_id is invalid):**
    ```json
    {
      "detail": "Error message"
    }
    ```

## Docker Deployment

The project includes Dockerfiles for building container images for both CPU and GPU environments.

### `Dockerfile.cpu` (CPU-based inference)

This Dockerfile sets up the environment for running the service on a CPU.

**Build the image:**
```bash
docker build -t blip-captioner-cpu -f Dockerfile.cpu .
```

**Run the container:**
```bash
docker run -p 8000:8000 -v /path/to/your/images:/app/images blip-captioner-cpu
```
*   `-p 8000:8000`: Maps port 8000 of the host to port 8000 of the container (where the app runs).
*   `-v /path/to/your/images:/app/images`: (Optional) Mounts a local directory containing images into the container at `/app/images`. Adjust paths as needed. Image paths provided to the API should then be relative to this mount point within the container (e.g., `/app/images/my_image.jpg`).

You can also pass arguments to `run.py` when starting the container:
```bash
docker run -p 8000:8000 blip-captioner-cpu python run.py --port 8000 --workers 2
```

### `Dockerfile.gpu` (GPU-accelerated inference)

This Dockerfile sets up the environment for running the service on an NVIDIA GPU, which can significantly speed up model inference. Ensure you have NVIDIA drivers, CUDA, and `nvidia-docker` (or Docker version >= 19.03) installed on your host machine.

**Build the image:**
```bash
docker build -t blip-captioner-gpu -f Dockerfile.gpu .
```

**Run the container:**
```bash
docker run --gpus all -p 8000:8000 -v /path/to/your/images:/app/images blip-captioner-gpu
```
*   `--gpus all`: Exposes all available GPUs to the container.
*   Other arguments are similar to the CPU version.

## Project Structure

A brief overview of the project's directory structure:

```
.
├── Dockerfile.cpu          # Dockerfile for CPU-based deployment
├── Dockerfile.gpu          # Dockerfile for GPU-based deployment
├── README.md               # This file
├── requirements.txt        # Python dependencies
├── run.py                  # Script to run the Uvicorn server
├── app/                    # Main application directory
│   ├── __init__.py
│   ├── main.py             # FastAPI application setup, API routes
│   ├── model.py            # BLIP model loading and captioning logic
│   ├── api/                # API specific modules (if further structured)
│   │   ├── __init__.py
│   │   └── routes.py       # (Potentially where routes are defined, or in main.py)
│   ├── core/               # Core components like configuration
│   │   ├── __init__.py
│   │   └── config.py
│   ├── models/             # Pydantic models for request/response schemas
│   │   ├── __init__.py
│   │   └── schemas.py
│   └── __pycache__/        # Python bytecode cache
├── static/                 # Static files (e.g., for a simple frontend)
│   └── index.html          # Example HTML page
└── ...                     # Other files and directories
```

-   **`app/main.py`**: Contains the FastAPI application instance and defines the API endpoints.
-   **`app/model.py`**: Handles the loading of the BLIP model and the core caption generation logic.
-   **`app/core/config.py`**: (Likely) For application settings, though `run.py` handles runtime args.
-   **`app/models/schemas.py`**: Defines Pydantic models for request and response data validation.
-   **`run.py`**: The main entry point to start the application using Uvicorn, parsing command-line arguments.
-   **`static/index.html`**: A simple HTML file. If served by the application (e.g., via `StaticFiles` in FastAPI), it could be used for testing or simple interactions. The current `main.py` would need to be checked to confirm if it's being served.

## Logging

Logging is handled by Uvicorn and FastAPI. The log level can be configured using the `--log-level` argument when using `run.py`. Logs will typically be output to the console.

## Important Notes

-   **Image Access**: This service requires direct file system access to the images for synchronous endpoints. For the asynchronous batch endpoint, images are uploaded, temporarily stored by the server, and then processed. It does not handle file uploads itself in the sense of persistent storage beyond the scope of a request or background task. If integrating with a web application, that application would typically handle uploads and then provide this service with the path to the stored image for synchronous operations, or upload directly for asynchronous ones.
-   **Model Loading**: The BLIP model is loaded into memory when the service starts. This can take some time and consume significant memory, especially the larger versions of the model.
-   **Error Handling**: The API endpoints include basic error handling (e.g., for file not found or invalid file types). Check the API responses for specific error messages. Asynchronous tasks will report errors through the status endpoint.

## Future Enhancements (Suggestions)

*   Endpoint to check the status and retrieve results of asynchronous tasks. (Implemented)
*   More robust configuration management (e.g., using environment variables or a config file via `pydantic-settings`). (Implemented)
*   More detailed error reporting and standardized error codes. (Partially addressed with per-image errors and async task status)
*   Unit and integration tests.
*   Improved robustness of asynchronous processing by pre-saving files. (Implemented)