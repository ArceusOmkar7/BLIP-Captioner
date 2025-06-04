#!/usr/bin/env python
"""
Test script to verify model loading behavior
"""
from io import BytesIO
import requests
from PIL import Image
from app.model import generate_caption_from_image, processor, model
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_model_loading():
    """Test that model loads correctly at startup"""
    print("Testing model loading...")

    # Import the model components (they should already be loaded at startup)
    print("Checking if model and processor are loaded...")
    from app.model import processor, model

    print(f"Processor type: {type(processor)}")
    print(f"Model type: {type(model)}")

    # Verify they are not None
    print(f"Processor loaded: {processor is not None}")
    print(f"Model loaded: {model is not None}")

    # Test with a simple image
    print("\nTesting caption generation...")
    try:
        # Create a simple test image
        test_image = Image.new('RGB', (100, 100), color='red')
        caption = generate_caption_from_image(test_image)
        print(f"Generated caption: {caption}")
        print("✅ Model loading and caption generation test passed!")
    except Exception as e:
        print(f"❌ Error during caption generation: {e}")


if __name__ == "__main__":
    test_model_loading()
