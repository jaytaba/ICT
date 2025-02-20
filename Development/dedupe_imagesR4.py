import os
import cv2
import shutil
from skimage.metrics import structural_similarity as ssim
import numpy as np

# Input and output folders
input_folder = r"D:\AI_train_data\Train_Prod\unique_frames"
output_folder = r"D:\AI_train_data\Train_Prod\unique_framesT3round"

# Ensure output directory exists
os.makedirs(output_folder, exist_ok=True)

def is_duplicate(image1_path, image2_path):
    """Compare two images using SSIM while keeping color information."""
    img1 = cv2.imread(image1_path)  # Read in COLOR
    img2 = cv2.imread(image2_path)  # Read in COLOR

    img1 = cv2.resize(img1, (256, 256))
    img2 = cv2.resize(img2, (256, 256))

    # Convert to grayscale for SSIM comparison
    img1_gray = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    img2_gray = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    similarity = ssim(img1_gray, img2_gray)
    return similarity > 0.95  # Adjust threshold as needed

# Store unique images
unique_images = []

# Get all image files from input folder
image_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith(".jpg")])

for i, filename in enumerate(image_files):
    image_path = os.path.join(input_folder, filename)
    
    is_unique = True
    for unique_file in unique_images:
        unique_image_path = os.path.join(output_folder, unique_file)

        if is_duplicate(image_path, unique_image_path):
            print(f"Duplicate found: {filename} (similar to {unique_file})")
            is_unique = False
            break  # Stop checking once a duplicate is found

    if is_unique:
        unique_images.append(filename)
        shutil.copy(image_path, os.path.join(output_folder, filename))
        print(f"Copied unique image: {filename}")

print(f"\n✅ Unique images saved in: {output_folder}")
