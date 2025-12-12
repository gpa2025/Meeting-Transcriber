"""
Image Resizer

This script resizes JPG images from an input folder and saves them to an output folder.
"""

import os
import sys
from PIL import Image
from pathlib import Path


def create_directory(directory_path):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Created directory: {directory_path}")


def resize_image(input_path, output_path, size):
    """
    Resize an image and save it to the output path.
    
    Args:
        input_path: Path to the input image
        output_path: Path where the resized image will be saved
        size: Tuple of (width, height) for the new size
    """
    try:
        with Image.open(input_path) as img:
            # Resize the image
            resized_img = img.resize(size, Image.Resampling.LANCZOS)
            # Save the resized image
            resized_img.save(output_path)
            print(f"Resized: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
    except Exception as e:
        print(f"Error processing {input_path}: {e}")


def process_images(input_folder, output_folder, width, height):
    """
    Process all JPG images in the input folder and save resized versions to the output folder.
    
    Args:
        input_folder: Path to the folder containing images to resize
        output_folder: Path to the folder where resized images will be saved
        width: Width of the resized images
        height: Height of the resized images
    """
    # Create output directory if it doesn't exist
    create_directory(output_folder)
    
    # Get all jpg files in the input directory
    input_path = Path(input_folder)
    jpg_files = list(input_path.glob("*.jpg")) + list(input_path.glob("*.jpeg"))
    
    if not jpg_files:
        print(f"No JPG images found in {input_folder}")
        return
    
    print(f"Found {len(jpg_files)} JPG images to process")
    
    # Process each image
    for jpg_file in jpg_files:
        output_path = os.path.join(output_folder, jpg_file.name)
        resize_image(str(jpg_file), output_path, (width, height))
    
    print(f"Finished processing {len(jpg_files)} images")


def main():
    """Main function to handle command line arguments and start processing."""
    if len(sys.argv) < 5:
        print("Usage: python image_resizer.py <input_folder> <output_folder> <width> <height>")
        print("Example: python image_resizer.py ./images ./resized_images 800 600")
        return
    
    input_folder = sys.argv[1]
    output_folder = sys.argv[2]
    
    try:
        width = int(sys.argv[3])
        height = int(sys.argv[4])
    except ValueError:
        print("Error: Width and height must be integers")
        return
    
    if not os.path.isdir(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist")
        return
    
    process_images(input_folder, output_folder, width, height)


if __name__ == "__main__":
    main()