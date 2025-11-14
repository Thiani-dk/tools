import os
import logging
from PIL import Image
from tqdm import tqdm

logger = logging.getLogger(__name__)

def create_pdf(frame_paths, pdf_path, resolution):
    """
    Creates a multi-page PDF from a list of frame images in a memory-safe way.

    Args:
        frame_paths (list): List of paths to the frame image files.
        pdf_path (str): The desired output path for the .pdf file.
        resolution (float): The DPI resolution for the PDF.
    """
    if not frame_paths:
        logger.warning("No frame paths provided to create PDF. Aborting.")
        return

    logger.info(f"Creating PDF file at: {pdf_path}")

    try:
        # --- Memory-Safe PDF Creation ---
        
        # 1. Open the *first* image
        img1 = Image.open(frame_paths[0])
        # Convert to RGB (PDFs don't like all image modes)
        img1 = img1.convert("RGB") 

        # 2. Create a generator for the *rest* of the images
        # A generator doesn't load all images into memory at once.
        # It loads one, yields it, and then it's discarded (garbage collected).
        def image_generator(paths):
            for path in tqdm(paths, desc="Stitching PDF"):
                if os.path.exists(path):
                    try:
                        img = Image.open(path)
                        yield img.convert("RGB")
                    except Exception as e:
                        logger.warning(f"Could not open image {path} for PDF: {e}")
                else:
                    logger.warning(f"Frame file not found during PDF creation: {path}")

        # 3. Save the first image, and "append" the generator
        img1.save(
            pdf_path,
            "PDF",
            resolution=resolution,
            save_all=True,  # This tells Pillow to save multiple pages
            append_images=image_generator(frame_paths[1:]) # Pass our generator
        )
        
        logger.info(f"Successfully created PDF file with {len(frame_paths)} pages.")

    except Exception as e:
        logger.error(f"Failed to create PDF file: {e}")
        # Clean up a potentially broken pdf file
        if os.path.exists(pdf_path):
            os.remove(pdf_path)