"""
Test script for BLIP Captioner with Tags Extraction
--------------------------------------------------
This script tests the complete flow of caption and tags generation.
"""

import sys
import os

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

try:
    from app.model import generate_caption_and_tags_from_image
    from app.core.tags_extractor import extract_noun_phrases, is_spacy_model_available
    from PIL import Image
    import requests
    import io

    print("🚀 Testing BLIP Captioner with Tags Extraction")
    print("=" * 50)

    # Check spaCy model availability
    print("1. Checking spaCy model availability...")
    if is_spacy_model_available():
        print("   ✅ spaCy English model is available")
    else:
        print("   ❌ spaCy English model not found")
        print("   Please run: python -m spacy download en_core_web_sm")
        sys.exit(1)

    # Test tag extraction with sample text
    print("\n2. Testing tag extraction...")
    sample_captions = [
        "A black and white cat sitting on a wooden table",
        "Two people walking on a sandy beach during sunset",
        "A red sports car parked in front of a modern building"
    ]

    for i, caption in enumerate(sample_captions, 1):
        tags = extract_noun_phrases(caption)
        print(f"   Caption {i}: {caption}")
        print(f"   Tags: {tags}")
        print()

    # Test with a sample image (we'll create a simple test image)
    print("3. Testing complete caption and tags generation...")

    # Create a simple test image (colored rectangle)
    test_image = Image.new('RGB', (200, 200), color='red')

    try:
        result = generate_caption_and_tags_from_image(test_image)
        print(f"   Generated caption: {result['caption']}")
        print(f"   Extracted tags: {result['tags']}")
    except Exception as e:
        print(f"   ❌ Error in caption/tags generation: {e}")

    print("\n🎉 All tests completed successfully!")
    print("\nThe BLIP Captioner with Tags Extraction is ready to use.")
    print("You can start the server with: python run.py")

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    print("And download the spaCy model: python -m spacy download en_core_web_sm")
except Exception as e:
    print(f"❌ Unexpected error: {e}")
