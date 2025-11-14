import cv2
import os
import logging
from tqdm import tqdm
from skimage.metrics import structural_similarity as ssim
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)

def convert_to_grayscale(frame):
    """Helper function to convert a frame to grayscale for SSIM."""
    if frame is None:
        return None
    if len(frame.shape) == 3:  # Check if it's a color image
        return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return frame

def extract_frames(video_path, output_folder, ssim_threshold):
    """
    Extracts frames from a video file.

    Args:
        video_path (str): Path to the video file.
        output_folder (str): Directory to save the extracted frames.
        ssim_threshold (float): Similarity threshold to skip frames.
                                0.0 means save all frames.

    Returns:
        list: A list of paths to the saved frame image files.
    """
    
    # --- 1. Validation and Setup ---
    if not os.path.exists(video_path):
        logger.error(f"Video file not found: {video_path}")
        return []

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        logger.error(f"Error opening video file: {video_path}")
        return []

    # Get video properties
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    logger.info(f"Video loaded: {video_path} ({total_frames} frames @ {fps:.2f} FPS)")

    # Create the output directory if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)
    logger.info(f"Saving frames to: {output_folder}")

    # --- 2. Frame Extraction Loop ---
    saved_frame_paths = []
    prev_frame_gray = None
    saved_count = 0
    skipped_count = 0

    # Use tqdm for a progress bar
    with tqdm(total=total_frames, desc="Extracting frames") as pbar:
        frame_index = 0
        while True:
            # Read one frame from the video
            ret, frame = cap.read()

            # If 'ret' is False, we've reached the end of the video
            if not ret:
                break
            
            # --- 3. SSIM (Similarity) Check ---
            save_this_frame = False
            if ssim_threshold <= 0.0:
                # If threshold is 0, save every frame
                save_this_frame = True
            else:
                # Convert current frame to grayscale for comparison
                current_frame_gray = convert_to_grayscale(frame)

                if prev_frame_gray is None:
                    # Always save the very first frame
                    save_this_frame = True
                else:
                    # Compare current frame to the previous saved frame
                    try:
                        score = ssim(prev_frame_gray, current_frame_gray)
                        if score < ssim_threshold:
                            # If frames are different enough, save it
                            save_this_frame = True
                        else:
                            skipped_count += 1
                    except Exception as e:
                        logger.warning(f"Could not compute SSIM: {e}. Saving frame.")
                        save_this_frame = True # Save if comparison fails

            # --- 4. Save the Frame ---
            if save_this_frame:
                saved_count += 1
                # Format frame number with leading zeros (e.g., 00001)
                frame_filename = f"frame_{saved_count:06d}.jpg"
                frame_path = os.path.join(output_folder, frame_filename)
                
                # Save the frame as a .jpg file
                cv2.imwrite(frame_path, frame)
                saved_frame_paths.append(frame_path)
                
                # Update the 'previous' frame to this new frame
                prev_frame_gray = convert_to_grayscale(frame) # Re-use current gray frame

            frame_index += 1
            pbar.update(1) # Advance the progress bar

    # --- 5. Cleanup ---
    cap.release()  # Release the video file
    logger.info(f"Extraction complete. Saved {saved_count} frames. Skipped {skipped_count} similar frames.")
    
    return saved_frame_paths