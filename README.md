# JPEG Quality Estimator

A Python application to estimate the JPEG compression quality of an image and to compress images to a specified JPEG quality. The estimation is based on an analysis of the image's quantization tables.

## Features

*   **Web Interface (Streamlit)**:
    *   Upload JPEG or PNG images.
    *   Displays the uploaded image.
    *   Estimates and shows the JPEG quality percentage (1-100%).
    *   Classifies the quality into categories: High, Medium, Low, Very Low.
*   **Command-Line Interface (CLI)**:
    *   Estimate quality of a single image file.
    *   Compress an image (e.g., PNG, JPEG) to a new JPEG file with a specified quality level.

## Quality Estimation Method

The JPEG quality is estimated by analyzing the luminance quantization table embedded within the JPEG file. 
The values in this table are compared against a standard luminance quantization table (commonly associated with a quality level of 50). A heuristic mapping based on the average of the image's quantization table values is used to derive an estimated quality percentage. For non-JPEG files like PNGs, a high quality is assumed.

## Setup

1.  **Clone the repository or download the files.**
2.  **Install Python 3.x** if you don't have it.
3.  **Install required Python libraries:**
    Navigate to the project directory in your terminal and run:
    ```bash
    pip install -r requirements.txt
    ```
    The `requirements.txt` file includes:
    *   `streamlit`: For the web interface.
    *   `opencv-python`: (Currently a general dependency, was for BRISQUE, less critical for Q-table method but good for broader image ops if needed in future)
    *   `scikit-image`: For image I/O (can be replaced by Pillow or imageio directly for Q-table method).
    *   `imageio`: Used by scikit-image for wider format support.
    *   `Pillow`: For opening images, accessing JPEG quantization tables, and saving compressed JPEGs.
    *   `numpy`: For numerical operations, especially on quantization tables.

## Usage

### 1. Web Interface

To run the Streamlit web application:

```bash
python3 app.py
```

Then open the URL shown in your terminal (usually `http://localhost:8501`) in your web browser.

### 2. Command-Line Interface

#### Estimate Quality of an Image

```bash
python3 app.py --file path/to/your/image.jpg
```
Replace `path/to/your/image.jpg` with the actual path to your image. The script will print the estimated quality and category to the console.

#### Compress an Image

```bash
python3 app.py --compress path/to/input_image.png --quality 80 --output path/to/save/compressed.jpg
```
*   `--compress path/to/input_image.png`: Path to the image you want to compress.
*   `--quality 80`: Desired JPEG quality (1-100). Defaults to 75 if not specified.
*   `--output path/to/save/compressed.jpg`: Path where the compressed JPEG will be saved. If omitted, it defaults to `[input_filename]_compressed_q[QUALITY].jpg` in the same directory as the input image.

Example:
```bash
python3 app.py --compress my_photo.png --quality 90
# This will save as my_photo_compressed_q90.jpg
```

## Notes

*   The quantization table-based estimation is a heuristic. While it gives a good indication of the *encoder's* quality setting, the visual quality can still vary depending on the image content and the specific JPEG encoder used.
*   The application provides fallback values if quantization tables are not found or if the image is not a recognized JPEG or PNG. 