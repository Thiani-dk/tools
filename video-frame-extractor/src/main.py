import os
import sys
import logging
import time

# -- Add the 'src' directory to the Python path ---
# This allows us to import our other modules (config, video_utils, etc.)
# It's a bit of a hack, but common for simple projects.
src_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(src_dir)
# --------------------------------------------------

try:
    from config import (
        OUTPUT_DIR, LOG_DIR, LOG_FILE, 
        SSIM_THRESHOLD, PDF_RESOLUTION, SUPPORTED_VIDEO_FORMATS
    )
    import video_utils
    import zip_utils
    import pdf_utils
except ImportError as e:
    print(f"Error: Failed to import a module. Make sure all files are in the 'src' folder.")
    print(f"Details: {e}")
    sys.exit(1)


def setup_logging():
    """Configures the application-wide logger."""
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE),  # Log to a file
            logging.StreamHandler(sys.stdout) # Log to the console
        ]
    )
    # Get the root logger
    logger = logging.getLogger()
    logger.info("Logging initialized.")
    return logger

def get_video_path():
    """Prompts the user for a video file path and validates it."""
    while True:
        video_path = input("Enter the full path to your video file: ").strip()
        
        # Remove quotes if user dragged and dropped (common on Windows/Mac)
        if video_path.startswith('"') and video_path.endswith('"'):
            video_path = video_path[1:-1]
        if video_path.startswith("'") and video_path.endswith("'"):
            video_path = video_path[1:-1]

        if not os.path.exists(video_path):
            print("❌ Error: File not found. Please check the path and try again.")
        elif not os.path.isfile(video_path):
            print("❌ Error: The path provided is a directory, not a file.")
        elif not video_path.lower().endswith(SUPPORTED_VIDEO_FORMATS):
            print(f"❌ Error: Unsupported file type. Supported formats are: {SUPPORTED_VIDEO_FORMATS}")
        else:
            print(f"✅ Video file accepted: {video_path}")
            return video_path

def get_user_choice():
    """Displays the main menu and gets the user's desired action."""
    print("\n--- What would you like to do? ---")
    print("1: Extract frames only (saves to a folder)")
    print("2: Extract frames and create a ZIP file")
    print("3: Extract frames and create a PDF")
    print("0: Exit")
    
    while True:
        choice = input("Enter your choice (1, 2, or 3): ").strip()
        if choice in ['1', '2', '3', '0']:
            return choice
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

def get_ssim_choice():
    """Asks the user if they want to skip similar frames."""
    print("\n--- Frame Skipping ---")
    print(f"This tool can skip similar frames (SSIM threshold > {SSIM_THRESHOLD * 100}%)")
    
    while True:
        choice = input("Skip similar frames? (y/n): ").strip().lower()
        if choice == 'y':
            return SSIM_THRESHOLD
        elif choice == 'n':
            print("OK. Saving ALL frames.")
            return 0.0 # 0.0 means "save everything"
        else:
            print("❌ Invalid choice. Please enter 'y' or 'n'.")

def main():
    """Main application flow."""
    logger = setup_logging()
    logger.info("--- Application Started ---")
    
    print("========================================")
    print("  🎥 Welcome to the Video Frame Extractor ")
    print("========================================")

    try:
        # 1. Get user inputs
        video_path = get_video_path()
        export_choice = get_user_choice()
        
        if export_choice == '0':
            print("Exiting. Goodbye!")
            sys.exit(0)
        
        ssim_level = get_ssim_choice()

        # 2. Set up paths
        video_name = os.path.basename(video_path)
        video_name_no_ext = os.path.splitext(video_name)[0]
        
        # Create a unique folder name for this video's frames
        frame_output_folder = os.path.join(OUTPUT_DIR, f"{video_name_no_ext}_frames")
        
        # Define output file paths
        zip_output_path = os.path.join(OUTPUT_DIR, f"{video_name_no_ext}_frames.zip")
        pdf_output_path = os.path.join(OUTPUT_DIR, f"{video_name_no_ext}_frames.pdf")

        # 3. Start processing
        start_time = time.time()
        logger.info(f"Starting job for video: {video_name}")
        
        # --- Core Logic: Extract Frames ---
        frame_paths = video_utils.extract_frames(
            video_path=video_path,
            output_folder=frame_output_folder,
            ssim_threshold=ssim_level
        )

        if not frame_paths:
            logger.error("No frames were extracted. Exiting.")
            return # Exit main() if extraction failed

        # --- Handle Export Choice ---
        if export_choice == '1':
            # "Extract only"
            logger.info("Job finished: Frames extracted.")
            print(f"\n✅ Success! Frames are saved in:\n{frame_output_folder}")
        
        elif export_choice == '2':
            # "Create ZIP"
            logger.info("Starting ZIP creation...")
            zip_utils.create_zip(frame_paths, zip_output_path)
            logger.info("Job finished: ZIP created.")
            print(f"\n✅ Success! ZIP file created at:\n{zip_output_path}")

        elif export_choice == '3':
            # "Create PDF"
            logger.info("Starting PDF creation...")
            pdf_utils.create_pdf(frame_paths, pdf_output_path, PDF_RESOLUTION)
            logger.info("Job finished: PDF created.")
            print(f"\n✅ Success! PDF file created at:\n{pdf_output_path}")

        end_time = time.time()
        logger.info(f"--- Total execution time: {end_time - start_time:.2f} seconds ---")

    except KeyboardInterrupt:
        logger.warning("--- Process interrupted by user (Ctrl+C) ---")
        print("\nProcess cancelled.")
    except Exception as e:
        logger.critical(f"An unhandled error occurred: {e}", exc_info=True)
        print(f"❌ An unexpected error occurred. Please check the log file: {LOG_FILE}")

if __name__ == "__main__":
    main()