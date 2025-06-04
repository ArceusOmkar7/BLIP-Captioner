#!/usr/bin/env python
"""
Test script to verify model loading behavior
"""
from io import BytesIO
import requests
from PIL import Image
from app.model import generate_caption_from_image, load_model
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_model_loading():
    """Test that model loads correctly and only once"""
    print("Testing model loading...")

    # First call should load the model
    print("First call to load_model()...")
    processor1, model1 = load_model()
    print(f"Processor type: {type(processor1)}")
    print(f"Model type: {type(model1)}")

    # Second call should return same instances
    print("\nSecond call to load_model()...")
    processor2, model2 = load_model()

    # Check if they are the same instances (should be due to global variables)
    print(f"Same processor instance: {processor1 is processor2}")
    print(f"Same model instance: {model1 is model2}")

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
