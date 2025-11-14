import os
import zipfile
import logging
from tqdm import tqdm

logger = logging.getLogger(__name__)

def create_zip(frame_paths, zip_path):
    """
    Creates a ZIP archive from a list of frame images.

    Args:
        frame_paths (list): List of paths to the frame image files.
        zip_path (str): The desired output path for the .zip file.
    """
    if not frame_paths:
        logger.warning("No frame paths provided to create zip. Aborting.")
        return

    logger.info(f"Creating ZIP file at: {zip_path}")
    
    try:
        # Open the zip file in 'write' mode
        with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
            # Use tqdm to show progress for zipping
            for frame_path in tqdm(frame_paths, desc="Zipping frames"):
                if os.path.exists(frame_path):
                    # Add the file to the zip.
                    # 'arcname' is the name it will have *inside* the zip.
                    # We use os.path.basename to just get the filename (e.g., "frame_00001.jpg")
                    zf.write(frame_path, arcname=os.path.basename(frame_path))
                else:
                    logger.warning(f"Frame file not found during zipping: {frame_path}")
        
        logger.info(f"Successfully created ZIP file with {len(frame_paths)} frames.")
    
    except Exception as e:
        logger.error(f"Failed to create ZIP file: {e}")
        # Clean up a potentially broken zip file
        if os.path.exists(zip_path):
            os.remove(zip_path)