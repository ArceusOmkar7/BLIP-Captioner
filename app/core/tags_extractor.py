"""
Tags Extraction Module
---------------------
This module provides functionality for extracting meaningful tags from image captions
using natural language processing (NLP) techniques with spaCy.
"""

import spacy
from typing import List, Set
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Global variable to hold the spaCy model
_nlp_model = None


def _load_spacy_model():
    """Load the spaCy English model. This is done lazily to avoid loading issues at import time."""
    global _nlp_model
    if _nlp_model is None:
        try:
            _nlp_model = spacy.load("en_core_web_sm")
            logger.info("Successfully loaded spaCy English model")
        except OSError as e:
            logger.error(
                f"Failed to load spaCy model 'en_core_web_sm'. "
                f"Please install it using: python -m spacy download en_core_web_sm. Error: {e}"
            )
            raise RuntimeError(
                "spaCy English model not found. Please install it using: "
                "python -m spacy download en_core_web_sm"
            ) from e
    return _nlp_model


def extract_noun_phrases(caption: str) -> List[str]:
    """
    Extract noun phrases from a caption text to generate meaningful tags.

    This function processes the caption using spaCy's NLP pipeline to identify
    noun phrases and converts them into clean, lemmatized tags. It removes
    determiners (like 'a', 'the') and filters out very short or common words.

    The function includes robust handling for edge cases including None inputs,
    empty captions, and very long captions.

    Args:
        caption (str): The image caption text to extract tags from

    Returns:
        List[str]: A sorted list of unique tags extracted from the caption

    Raises:
        RuntimeError: If spaCy model is not available
    """
    # Handle None input
    if caption is None:
        logger.warning("None caption provided for tag extraction")
        return []

    # Handle empty or whitespace-only captions
    if not caption or not caption.strip():
        logger.warning(
            "Empty or whitespace-only caption provided for tag extraction")
        return []

    # Handle very long captions by truncating them
    if len(caption) > 1000:
        logger.warning(
            f"Caption too long ({len(caption)} chars), truncating to 1000 characters")
        caption = caption[:1000]

    try:
        nlp = _load_spacy_model()
        doc = nlp(caption.strip())
        tags: Set[str] = set()

        # Extract noun phrases
        for chunk in doc.noun_chunks:
            # Remove determiners (e.g., 'a', 'the') and other unwanted parts of speech
            chunk_tokens = [
                token.lemma_.lower() for token in chunk
                if token.pos_ not in ["DET", "PRON"] and
                not token.is_stop and
                not token.is_punct and
                len(token.lemma_.strip()) > 1
            ]

            if chunk_tokens:
                chunk_text = " ".join(chunk_tokens).strip()
                if chunk_text and len(chunk_text) > 1:
                    tags.add(chunk_text)

        # Also extract individual important nouns and adjectives that might not be in noun phrases
        for token in doc:
            if (token.pos_ in ["NOUN", "PROPN"] and
                not token.is_stop and
                not token.is_punct and
                    len(token.lemma_.strip()) > 2):

                lemma = token.lemma_.lower().strip()
                if lemma:
                    tags.add(lemma)

        # Filter out very common/generic words that might not be useful as tags
        filtered_tags = {
            tag for tag in tags
            if tag not in {"image", "picture", "photo", "photograph", "thing", "things", "stuff"}
            and len(tag) > 1
        }

        result = sorted(filtered_tags)
        logger.debug(
            f"Extracted {len(result)} tags from caption: '{caption[:50]}...'")
        return result

    except Exception as e:
        logger.error(
            f"Error extracting tags from caption '{caption[:50]}...': {str(e)}")
        # Return empty list on error rather than crashing
        return []


def is_spacy_model_available() -> bool:
    """
    Check if the required spaCy model is available.

    Returns:
        bool: True if the model is available, False otherwise
    """
    try:
        _load_spacy_model()
        return True
    except Exception:
        return False
