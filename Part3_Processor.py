import numpy as np
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter
import os

# ==========================================
# CONFIGURATION (Dataset Specific)
# ==========================================
HPX = 6.0        # Pixel size (microns) - Updated to Zenodo spec
WINDOW_SIZE = 20 # Window for Speckle Contrast

def load_and_linearize_image(filename):
    """
    Loads PNG and restores Linear Intensity.
    Assumes PNG is 0..1 mapping to 0..40dB.
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found.")
        
    img = plt.imread(filename)
    if img.ndim == 3:
        if img.shape[2] == 4: img = img[:, :, :3]
        img = np.mean(img, axis=2)
    
    if img.max() > 1.0:
        img = img / 255.0
        
    # Linearization: I = 10^(4 * P) -> 4 comes from 40dB / 10
    intensity = 10.0 ** (img * 4.0)
    return intensity

def calculate_oac(intensity, h_px):
    epsilon = 1e-10
    I_rev = intensity[::-1, :]
    cumsum_rev = np.cumsum(I_rev, axis=0)
    cumsum_from_bottom = cumsum_rev[::-1, :]
    denom_term = cumsum_from_bottom - 0.5 * intensity
    mu = intensity / (2 * h_px * (denom_term + epsilon))
    return mu

def calculate_speckle_contrast_map(data, window_size=20):
    mean_val = uniform_filter(data, size=window_size, mode='reflect')
    mean_sq_val = uniform_filter(data**2, size=window_size, mode='reflect')
    var_val = mean_sq_val - mean_val**2
    var_val[var_val < 0] = 0 
    std_val = np.sqrt(var_val)
    sc_map = std_val / (mean_val + 1e-10)
    
    # Crop borders to avoid artifacts
    border = window_size // 2
    sc_map_cropped = sc_map[border:-border, border:-border]
    
    # Pad back to original size to keep image dimensions consistent for SSIM
    sc_map_padded = np.pad(sc_map_cropped, border, mode='edge')
    return sc_map_padded

def save_map(data, filename, vmin=None, vmax=None):
    """Saves a normalized grayscale map for metric comparison."""
    if vmin is None: vmin = np.min(data)
    if vmax is None: vmax = np.max(data)
    
    norm_data = np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)
    plt.imsave(filename, norm_data, cmap='gray')

def generate_maps(input_image_path):
    """
    Generates OAC, SC, and RSC maps from a structural OCT image.
    Saves them with suffixes _OAC.png, _SC.png, _RSC.png.
    Returns a dictionary of generated file paths.
    """
    base_name = os.path.splitext(input_image_path)[0]
    
    # 1. Load
    intensity = load_and_linearize_image(input_image_path)
    
    # 2. OAC
    mu_map = calculate_oac(intensity, HPX)
    oac_path = base_name + "_OAC.png"
    # OAC limits: usually 0 to 99th percentile
    save_map(mu_map, oac_path, vmin=np.min(mu_map), vmax=np.percentile(mu_map, 99))
    
    # 3. SC (on Intensity)
    sc_map = calculate_speckle_contrast_map(intensity, WINDOW_SIZE)
    sc_path = base_name + "_SC.png"
    save_map(sc_map, sc_path, vmin=0.5, vmax=5.0) # Standard limits
    
    # 4. RSC (on OAC)
    rsc_map = calculate_speckle_contrast_map(mu_map, WINDOW_SIZE)
    rsc_path = base_name + "_RSC.png"
    save_map(rsc_map, rsc_path, vmin=0.5, vmax=5.0)
    
    print(f"[Processor] Generated maps for {input_image_path}")
    
    return {
        'Struct': input_image_path,
        'OAC': oac_path,
        'SC': sc_path,
        'RSC': rsc_path
    }

if __name__ == "__main__":
    # Test run (requires Test_Scan.png from Part 2)
    if os.path.exists("Test_Scan.png"):
        generate_maps("Test_Scan.png")
    else:
        print("Run Part 2 first to generate Test_Scan.png")
