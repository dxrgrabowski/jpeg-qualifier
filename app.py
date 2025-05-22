import streamlit as st
from skimage import io
import numpy as np
from brisque import BRISQUE

# Initialize BRISQUE
brisque_model = BRISQUE(url=False)

def estimate_jpeg_quality(image_array):
    """Estimate JPEG quality using BRISQUE.
    BRISQUE scores range from 0 (best) to 100 (worst).
    We convert this to a 0-100% quality score (higher is better).
    """
    try:
        if image_array.shape[-1] == 4:
            image_array = image_array[..., :3] # Convert RGBA to RGB
        
        brisque_score = brisque_model.score(image_array)
        estimated_quality = 100 - brisque_score
        estimated_quality = max(0, min(100, estimated_quality))
        return estimated_quality
    except Exception as e:
        st.error(f"Error in BRISQUE calculation: {e}")
        return 50

def classify_quality(score):
    if score >= 90:
        return "High Quality"
    elif score >= 80:
        return "Medium Quality"
    elif score >= 70:
        return "Low Quality"
    else:
        return "Very Low Quality"

st.title("JPEG Quality Estimator")

uploaded_file = st.file_uploader("Choose a JPEG image", type=["jpg", "jpeg"])

if uploaded_file is not None:
    try:
        image_bytes = uploaded_file.read()
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