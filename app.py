import streamlit as st
from skimage import io
import numpy as np
from brisque import BRISQUE
import argparse
from PIL import Image # For saving compressed JPEGs
import os

# Initialize BRISQUE
brisque_model = BRISQUE(url=False)

def estimate_jpeg_quality(image_array):
    """Estimate JPEG quality using BRISQUE.
    BRISQUE scores range from 0 (best) to 100 (worst).
    We convert this to a 0-100% quality score (higher is better).
    """
    try:
        if image_array.ndim == 2: # Grayscale image
            # BRISQUE might work better with 3-channel images, even if grayscale
            # For now, we pass it as is, but conversion to 3-channel might be needed if results are poor
            pass
        elif image_array.shape[-1] == 4:
            image_array = image_array[..., :3] # Convert RGBA to RGB
        
        brisque_score = brisque_model.score(image_array)
        estimated_quality = 100 - brisque_score
        estimated_quality = max(0, min(100, estimated_quality))
        return estimated_quality
    except Exception as e:
        # st.error(f"Error in BRISQUE calculation: {e}") # Avoid streamlit call in CLI mode
        print(f"Error in BRISQUE calculation: {e}")
        return 50 # Neutral score on error

def classify_quality(score):
    if score >= 90:
        return "High Quality"
    elif score >= 80:
        return "Medium Quality"
    elif score >= 70:
        return "Low Quality"
    else:
        return "Very Low Quality"

def compress_image(input_path, output_path, quality):
    """Compresses an image and saves it as JPEG with the specified quality."""
    try:
        img = Image.open(input_path)
        # Ensure the image is in RGB mode for JPEG saving, especially if it was PNG with alpha
        if img.mode == 'RGBA' or img.mode == 'P': # P is for paletted images
            img = img.convert('RGB')
        img.save(output_path, 'JPEG', quality=quality)
        print(f"Successfully compressed image saved to {output_path} with quality {quality}%")
    except Exception as e:
        print(f"Error compressing image: {e}")

def main_cli(image_path):
    try:
        image = io.imread(image_path) # skimage.io can handle various formats
        
        estimated_quality_score = estimate_jpeg_quality(image)
        quality_category = classify_quality(estimated_quality_score)

        print(f"--- Image: {image_path} ---")
        print(f"Estimated Quality: {estimated_quality_score:.2f}%")
        print(f"Quality Category: {quality_category}")

    except FileNotFoundError:
        print(f"Error: Image file not found at {image_path}")
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")

def main_streamlit():
    st.title("JPEG Quality Estimator")
    uploaded_file = st.file_uploader("Choose a JPEG image", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        try:
            image_bytes = uploaded_file.read()
            # Use skimage.io.imread as it's already imported and handles bytes well
            image = io.imread(image_bytes, plugin='imageio')

            st.image(image, caption="Uploaded Image.", use_column_width=True)
            st.write("")
            st.write("Estimating quality...")

            estimated_quality_score = estimate_jpeg_quality(image)
            quality_category = classify_quality(estimated_quality_score)

            st.write(f"Estimated Quality: {estimated_quality_score:.2f}%")
            st.write(f"Quality Category: {quality_category}")

        except Exception as e:
            st.error(f"Error processing image: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='JPEG Quality Estimator and Compressor')
    parser.add_argument('--file', type=str, help='Path to an image file to estimate quality.')
    parser.add_argument('--compress', type=str, help='Path to an image file to compress.')
    parser.add_argument('--quality', type=int, default=75, help='JPEG quality for compression (1-100).')
    parser.add_argument('--output', type=str, help='Output path for the compressed image.')

    args = parser.parse_args()

    if args.file:
        main_cli(args.file)
    elif args.compress:
        if not args.output:
            # Default output name if not provided
            base, ext = os.path.splitext(args.compress)
            args.output = f"{base}_compressed_q{args.quality}.jpg"
        compress_image(args.compress, args.output, args.quality)
    else:
        main_streamlit() 