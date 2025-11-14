import os

# --- Directory Setup ---
# Get the absolute path of the directory where this file is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
# Get the parent directory (our project root 'video-frame-extractor')
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Define key directories
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
LOG_FILE = os.path.join(LOG_DIR, "app.log")

# --- Video Processing ---
# SSIM (Structural Similarity Index) Threshold
# 1.0 = identical. 0.98 = very similar.
# Frames with similarity ABOVE this threshold will be skipped.
# Set to 0.0 to save every single frame.
SSIM_THRESHOLD = 0.98

# --- PDF Output ---
PDF_RESOLUTION = 100.0  # DPI for the output PDF

# --- Supported Formats ---
# Add more video extensions as needed
SUPPORTED_VIDEO_FORMATS = ('.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv')