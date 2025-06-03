# BLIP Image Captioning Microservice

A microservice that generates captions for images using the Salesforce BLIP (Bootstrapping Language-Image Pre-training) model. This service is designed to receive image paths, process the images, and return generated captions. It can be run locally or as a containerized application.

## Features

*   Generates descriptive captions for images using BLIP model.
*   Extracts meaningful tags from captions using spaCy NLP processing.
*   Supports single image captioning and batch processing.
*   Offers asynchronous batch captioning for non-blocking operations.
*   Configurable host, port, worker count, and logging level.
*   Includes Dockerfiles for CPU and GPU environments.
*   Basic health check endpoint.
*   Robust error handling and edge case management.

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

4.  **Install spaCy English model:**
    The tags extraction feature requires the English language model for spaCy.
    ```bash
    python -m spacy download en_core_web_sm
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
*   **Description:** Generates a caption and extracts tags for a single image.
*   **Request Body:** Form data with image file upload
*   **Response (200 OK):**
    ```json
    {
      "filename": "your_image.jpg",
      "caption": "A descriptive caption of the image.",
      "tags": ["tag1", "tag2", "tag3"],
      "processing_time": 1.23
    }
    ```
*   **Error Response (e.g., 400 Bad Request for invalid file, 500 for processing errors):**
    ```json
    {
      "detail": "Error message"
    }
    ```

### Caption Multiple Images (Batch Processing)

*   **Endpoint:** `POST /batch-caption`
*   **Description:** Generates captions and extracts tags for multiple images in a single request. Processed sequentially in the request-response cycle.
*   **Request Body:** Form data with multiple image file uploads
*   **Response (200 OK):**
    ```json
    {
      "results": [
        {
          "image_path": "image1.jpg",
          "caption": "Caption for image 1.",
          "tags": ["tag1", "tag2"]
        },
        {
          "image_path": "image2.jpg",
          "caption": "Caption for image 2.",
          "tags": ["tag3", "tag4"]
        }
      ],
      "total_processing_time": 2.45
    }
    ```

### Asynchronous Batch Captioning

*   **Endpoint:** `POST /async-batch-caption`
*   **Description:** Accepts multiple images for captioning and tags extraction, processing them asynchronously using background tasks. This endpoint returns immediately with a task ID.
*   **Request Body:** Form data with multiple image file uploads
*   **Response (202 Accepted):**
    ```json
    {
      "message": "Batch captioning task accepted. X files queued. Check status for details.",
      "task_id": "task_1672531200_a1b2c3d4"
    }
    ```

    **Update (June 2025):** The asynchronous batch captioning endpoint has been enhanced for robustness. Uploaded images are now saved to temporary storage before being queued for background processing. This ensures that the image files are reliably available to the background worker, mitigating issues with temporary file lifecycles. The service now also generates tags alongside captions using spaCy NLP processing.

### Check Asynchronous Task Status

*   **Endpoint:** `GET /async-batch-caption/status/{task_id}`
*   **Description:** Checks the status of an asynchronous captioning task and retrieves results if completed.
*   **Path Parameter:**
    *   `task_id`: The ID of the task returned by the `/async-batch-caption` endpoint.
*   **Response (200 OK):**
    ```json
    {
      "task_id": "task_1672531200_a1b2c3d4",
      "status": "COMPLETED",
      "message": "Processing complete. 2/2 images captioned successfully in background. Total results: 2.",
      "result": [
        {
          "image_path": "image1.jpg",
          "caption": "Caption for image 1.",
          "tags": ["tag1", "tag2", "tag3"]
        },
        {
          "image_path": "image2.jpg",
          "caption": "Caption for image 2.",
          "tags": ["tag4", "tag5"]
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

## Tags Extraction

The service now includes intelligent tags extraction from generated captions using spaCy's natural language processing capabilities.

### How It Works

1. **Caption Generation**: The BLIP model generates a descriptive caption for the image
2. **NLP Processing**: The caption is processed using spaCy's English language model (`en_core_web_sm`)
3. **Noun Phrase Extraction**: The system identifies meaningful noun phrases and individual nouns
4. **Tag Cleaning**: Tags are cleaned by:
   - Converting to lowercase and lemmatized forms
   - Removing determiners (a, the) and pronouns
   - Filtering out stop words and punctuation
   - Removing generic terms like "image", "picture", "photo"
   - Ensuring minimum tag length

### Features

- **Robust Error Handling**: Gracefully handles None inputs, empty captions, and very long text
- **Edge Case Management**: Automatically truncates captions longer than 1000 characters
- **Modular Design**: Tags extraction is separated into its own module for maintainability
- **Fallback Behavior**: Returns empty tag list if extraction fails, preventing service crashes

### Example

For a caption like "A young woman wearing a red dress standing in a beautiful garden", the system might extract tags such as:
- `woman`
- `dress`
- `garden`
- `young woman`
- `red dress`
- `beautiful garden`

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
│   ├── api/                # API specific modules
│   │   ├── __init__.py
│   │   └── routes.py       # API endpoint definitions
│   ├── core/               # Core components like configuration
│   │   ├── __init__.py
│   │   ├── config.py       # Configuration settings
│   │   ├── tags_extractor.py # spaCy-based tags extraction from captions
│   │   └── utils.py        # Utility functions
│   ├── models/             # Pydantic models for request/response schemas
│   │   ├── __init__.py
│   │   └── schemas.py      # Data models and validation schemas
│   └── __pycache__/        # Python bytecode cache
├── static/                 # Static files (e.g., for a simple frontend)
│   └── index.html          # Example HTML page
└── ...                     # Other files and directories
```

-   **`app/main.py`**: Contains the FastAPI application instance and includes the API routes.
-   **`app/model.py`**: Handles the loading of the BLIP model, caption generation, and tags extraction logic.
-   **`app/api/routes.py`**: Defines all API endpoints for single, batch, and async image processing.
-   **`app/core/config.py`**: Application configuration and logging setup.
-   **`app/core/tags_extractor.py`**: spaCy-based NLP processing for extracting meaningful tags from captions.
-   **`app/core/utils.py`**: Utility functions for image processing and file handling.
-   **`app/models/schemas.py`**: Defines Pydantic models for request and response data validation.
-   **`run.py`**: The main entry point to start the application using Uvicorn, parsing command-line arguments.
-   **`static/index.html`**: A web interface for testing the API endpoints with file uploads.

## Logging

Logging is handled by Uvicorn and FastAPI. The log level can be configured using the `--log-level` argument when using `run.py`. Logs will typically be output to the console.

## Important Notes

-   **Image Access**: This service handles file uploads directly through multipart form data. For asynchronous batch processing, images are uploaded, temporarily stored by the server, and then processed in the background.
-   **Model Loading**: The BLIP model and spaCy English model are loaded into memory when the service starts. This can take some time and consume significant memory.
-   **spaCy Dependency**: The tags extraction feature requires the spaCy English model (`en_core_web_sm`). Make sure to install it using `python -m spacy download en_core_web_sm` after installing the requirements.
-   **Error Handling**: The API endpoints include comprehensive error handling with graceful fallbacks for tags extraction failures. Check the API responses for specific error messages.
-   **Tags Quality**: The quality of extracted tags depends on the quality of the generated caption. More descriptive captions will yield better tags.

## Future Enhancements

*   ✅ Endpoint to check the status and retrieve results of asynchronous tasks. (Implemented)
*   ✅ More robust configuration management using environment variables and pydantic-settings. (Implemented)
*   ✅ Intelligent tags extraction from captions using NLP. (Implemented)
*   ✅ Comprehensive error handling with graceful fallbacks. (Implemented)
*   Advanced tag filtering and categorization
*   Support for multiple languages in tags extraction
*   Caching mechanisms for improved performance
*   Unit and integration tests
*   Database integration for persistent storage
*   Rate limiting and authentication
*   Improved robustness of asynchronous processing by pre-saving files. (Implemented)