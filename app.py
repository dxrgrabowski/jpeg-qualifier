import streamlit as st
from skimage import io
import numpy as np
# from brisque import BRISQUE # No longer needed
import argparse
from PIL import Image, UnidentifiedImageError # For saving and reading JPEGs, and accessing Q tables
import os
import io as BytesIOModule # To handle byte streams for Pillow

# Standard luminance quantization table (often used for quality 50 in libjpeg)
# This is a reference point; actual tables vary by encoder and quality setting.
# We will use it to derive the scaling factor.
STANDARD_LUMINANCE_TABLE = np.array([
    16,  11,  10,  16,  24,  40,  51,  61,
    12,  12,  14,  19,  26,  58,  60,  55,
    14,  13,  16,  24,  40,  57,  69,  56,
    14,  17,  22,  29,  51,  87,  80,  62,
    18,  22,  37,  56,  68, 109, 103,  77,
    24,  35,  55,  64,  81, 104, 113,  92,
    49,  64,  78,  87, 103, 121, 120, 101,
    72,  92,  95,  98, 112, 100, 103,  99
])

def get_jpeg_quality_from_qtable(image_path_or_bytes):
    """Estimates JPEG quality based on quantization tables."""
    try:
        if isinstance(image_path_or_bytes, str):
            img = Image.open(image_path_or_bytes)
        elif isinstance(image_path_or_bytes, bytes):
            img = Image.open(BytesIOModule.BytesIO(image_path_or_bytes))
        else:
            raise ValueError("Input must be a file path (str) or bytes.")

        if img.format != 'JPEG':
            # If not a JPEG, we can't get qtables. 
            # We could try to save it as JPEG with high quality and then analyze,
            # but for now, let's indicate it's not a JPEG or return a default.
            # For this application, we primarily expect JPEGs for quality estimation.
            # Or, we can return a high quality if it's a lossless format like PNG.
            if img.format == 'PNG': # Assuming PNG is high quality
                 return 98 # High quality for lossless like PNG
            return 50 # Default for non-JPEG unidentified types

        q_tables = img.quantization
        if not q_tables:
            # This can happen if the JPEG is malformed or uses a very unusual structure
            print("Warning: Quantization tables not found in the image.")
            return 50 # Default fallback

        # Typically, table 0 is for luminance, table 1 for chrominance
        # We'll focus on the luminance table for quality estimation
        luminance_q_table = np.array(q_tables.get(0))
        if luminance_q_table is None:
            print("Warning: Luminance quantization table (0) not found.")
            # Try to get any available table if 0 is not there
            available_tables = list(q_tables.keys())
            if not available_tables:
                return 40 # Low fallback if no tables at all
            luminance_q_table = np.array(q_tables.get(available_tables[0]))
            print(f"Using quantization table {available_tables[0]} as fallback.")

        # The core idea: JPEG quality scales the standard table.
        # If Q_image[i,j] = S * Q_standard[i,j], then S is the scaling factor.
        # For quality < 50, S = 5000 / (quality * Q_standard)
        # For quality >= 50, S = (200 - 2 * quality) * Q_standard / 100
        # We need to estimate S, then estimate quality.
        # A simpler approach: find an average scaling factor.
        # We must be careful with division by zero if standard table has zeros (it shouldn't for default JPEG tables).
        
        # Calculate mean ratio. Filter out any zeros in standard table if they exist.
        non_zero_std_indices = STANDARD_LUMINANCE_TABLE != 0
        if not np.any(non_zero_std_indices):
            print("Error: Standard luminance table contains all zeros.")
            return 30 # Error case

        # Ensure luminance_q_table is also 1D for consistent comparison if it comes in a different shape
        luminance_q_table_flat = luminance_q_table.flatten()
        standard_luminance_table_flat_filtered = STANDARD_LUMINANCE_TABLE[non_zero_std_indices]
        
        # Ensure the image's qtable has the same number of elements for comparison
        if len(luminance_q_table_flat) != len(STANDARD_LUMINANCE_TABLE):
            # This can happen with non-standard JPEGs or an issue with table extraction
            print(f"Warning: Image Q-table size ({len(luminance_q_table_flat)}) mismatches standard ({len(STANDARD_LUMINANCE_TABLE)}).")
            # Fallback: Average value of the table. Higher average means lower quality.
            avg_q_value = np.mean(luminance_q_table_flat)
            # Simple heuristic: map avg_q_value (e.g. 2-200) to quality (100-1)
            # This is a very rough estimate.
            quality = max(1, min(100, int(110 - avg_q_value / 1.5)))
            return quality

        luminance_q_table_flat_filtered = luminance_q_table_flat[non_zero_std_indices]

        # Calculate the scaling factor S. S = Q_image / Q_standard
        # Averaging ratios can be problematic if some values are very small or very large.
        # Instead, let's try to find a quality value that would produce a table similar to the image's q_table.
        # This is an inverse problem. The original IJG scaling formulas are:
        # if (quality < 50) scale = 5000 / quality; else scale = 200 - quality * 2;
        # q_val = floor((std_q_val * scale + 50) / 100) for q<50
        # q_val = floor((std_q_val * scale + 50) / 100) for q>=50, but scale is different.
        # q_val = clamp(q_val, 1, 255)
        
        # Simpler: Estimate based on the average value of the Q table.
        # Lower average Q value usually means higher quality.
        avg_q_val = np.mean(luminance_q_table_flat_filtered)

        # Heuristic mapping: Q values typically range. E.g., for quality 100, avg Q might be low (e.g., <5).
        # For quality 10, avg Q might be high (e.g., >50).
        # This is a simplification of the libjpeg quality scaling.
        # Let's try a curve fit or a lookup if possible, for now, a linear-ish map.
        if avg_q_val <= 10: quality = 95 - (avg_q_val - 1) # e.g. avg_val 1->95, 10->86
        elif avg_q_val <= 20: quality = 90 - (avg_q_val - 10) * 1.5 # e.g. 20 -> 75
        elif avg_q_val <= 50: quality = 75 - (avg_q_val - 20) * 1.0 # e.g. 50 -> 45
        elif avg_q_val <= 100: quality = 45 - (avg_q_val - 50) * 0.6 # e.g. 100 -> 15
        else: quality = 15 - (avg_q_val - 100) * 0.1 # very low
        
        quality = int(max(1, min(100, quality)))
        return quality

    except UnidentifiedImageError:
        print("Error: Cannot identify image file. It might be corrupted or not a supported format.")
        return 20 # Low quality for unidentified files
    except ValueError as ve:
        print(f"ValueError: {ve}")
        return 25
    except Exception as e:
        print(f"Error processing image for Q-table quality: {e}")
        return 30 # Fallback quality

# def estimate_jpeg_quality(image_array): # Old BRISQUE function - REMOVE
#    ...

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
        # image = io.imread(image_path) # skimage.io not needed for qtable method with path
        estimated_quality_score = get_jpeg_quality_from_qtable(image_path)
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
            # image = io.imread(image_bytes, plugin='imageio') # No longer need to load full image array for qtable method

            st.image(image_bytes, caption="Uploaded Image.", use_container_width=True) # Display the uploaded bytes
            st.write("")
            st.write("Estimating quality...")

            estimated_quality_score = get_jpeg_quality_from_qtable(image_bytes)
            quality_category = classify_quality(estimated_quality_score)

            st.write(f"Estimated Quality: {estimated_quality_score:.0f}%") # Q table usually gives integer quality
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