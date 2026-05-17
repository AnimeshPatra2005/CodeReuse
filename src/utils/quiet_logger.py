"""Quiet logger configuration for demo - suppresses verbose ChromaDB warnings."""

import warnings
import logging
import os

def setup_quiet_mode():
    """Configure logging to suppress verbose output during demo."""
    
    # Suppress ChromaDB warnings
    warnings.filterwarnings('ignore', category=UserWarning, module='chromadb')
    
    # Suppress specific loggers
    logging.getLogger('chromadb').setLevel(logging.ERROR)
    logging.getLogger('chromadb.telemetry').setLevel(logging.CRITICAL)
    logging.getLogger('sentence_transformers').setLevel(logging.ERROR)
    logging.getLogger('transformers').setLevel(logging.ERROR)
    
    # Suppress HuggingFace warnings
    os.environ['TRANSFORMERS_VERBOSITY'] = 'error'
    os.environ['TOKENIZERS_PARALLELISM'] = 'false'

# Made with Bob