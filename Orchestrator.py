import os
import csv
import numpy as np
import warnings
import time
import subprocess
from skimage import io, img_as_float, transform
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error as mse
from skimage.metrics import peak_signal_noise_ratio as psnr

# === FIX FOR WinError 1114 ===
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import Part1_Generator as Generator
import Part3_Processor as Processor

warnings.filterwarnings("ignore")

print("==================================================")
print("   SynthOCT Metrics Pipeline - Final & Formatted  ")
print("==================================================")

SCANNER_EXE = "Part2_Scanner.exe"

if not os.path.exists(SCANNER_EXE):
    print(f"CRITICAL ERROR: {SCANNER_EXE} not found!")
    print("Please compile Part2_Scanner.py using: pyinstaller --onefile --clean Part2_Scanner.py")
    exit(1)

# ==========================================
# METRICS SETUP
# ==========================================
SEWAR_AVAILABLE = False
try:
    from sewar.full_ref import vifp, msssim
    SEWAR_AVAILABLE = True
    print("[Metrics] Sewar library loaded.")
except ImportError:
    print("[Metrics] WARNING: 'sewar' library not found.")

LPIPS_AVAILABLE = False
loss_fn_alex = None
try:
    import torch
    import lpips
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    loss_fn_alex = lpips.LPIPS(net='alex', verbose=False).to(device)
    LPIPS_AVAILABLE = True
    print(f"[Metrics] LPIPS model loaded on {device}.")
except Exception:
    print(f"[Metrics] LPIPS skipped.")

def prepare_image_for_lpips(img_np):
    if not LPIPS_AVAILABLE: return None
    t = torch.from_numpy(img_np).float()
    t = t.unsqueeze(0).unsqueeze(0)
    t = t * 2 - 1
    t = t.repeat(1, 3, 1, 1)
    if torch.cuda.is_available(): t = t.cuda()
    return t

def calculate_all_metrics(path_ref, path_target):
    results = {}
    if not os.path.exists(path_ref) or not os.path.exists(path_target):
        return None

    try:
        img_ref = io.imread(path_ref, as_gray=True)
        img_tar = io.imread(path_target, as_gray=True)
        img_ref = img_as_float(img_ref)
        img_tar = img_as_float(img_tar)
        
        if img_ref.shape != img_tar.shape:
            img_tar = transform.resize(img_tar, img_ref.shape, anti_aliasing=True)

        # 1. Standard Metrics
        results['MSE'] = mse(img_ref, img_tar)
        results['PSNR'] = psnr(img_ref, img_tar, data_range=1.0)
        results['SSIM'] = ssim(img_ref, img_tar, data_range=1.0)

        # 2. Sewar Metrics
        if SEWAR_AVAILABLE:
            ref_u8 = (img_ref * 255).astype(np.uint8)
            tar_u8 = (img_tar * 255).astype(np.uint8)
            try: results['VIF'] = vifp(ref_u8, tar_u8)
            except: results['VIF'] = np.nan
            try:
                val_ms = msssim(ref_u8, tar_u8)
                results['MS-SSIM'] = float(np.real(val_ms))
            except: results['MS-SSIM'] = np.nan
        else:
            results['VIF'] = np.nan
            results['MS-SSIM'] = np.nan

        # 3. LPIPS Metric
        if LPIPS_AVAILABLE:
            try:
                t_ref = prepare_image_for_lpips(img_ref)
                t_tar = prepare_image_for_lpips(img_tar)
                with torch.no_grad():
                    d = loss_fn_alex(t_ref, t_tar)
                    results['LPIPS'] = d.item()
            except: results['LPIPS'] = np.nan
        else:
            results['LPIPS'] = np.nan
            
    except Exception as e:
        print(f"Error calc metrics: {e}")
        return None
            
    return results

# ==========================================
# MAIN PIPELINE
# ==========================================
def run_experiment_pipeline():
    print("\n=== STARTING PIPELINE ===\n")
    
    config = Generator.ExperimentConfig()
    config.write_ini() 
    
    gen = Generator.ScattererGenerator(config)
    
    # Experiments (Physics: 0-100%)
    experiments = [
        ("Exp1_Uniform", lambda seed: gen.generate_uniform(seed=seed, amp=1.0), 42, 101),
        ("Exp2_Layers", lambda seed: gen.generate_two_layers(seed=seed, boundary_z_mcm=400.0, amp_top=0.01, amp_bottom=2.5), 42, 101)
    ]
    
    all_results = []
    
    for exp_name, gen_func, seed_a, seed_b in experiments:
        print(f"\n--- Running Experiment: {exp_name} ---")
        
        file_a = f"Scatterers_{exp_name}_A.txt"
        file_b = f"Scatterers_{exp_name}_B.txt"
        
        gen.save_to_file(gen_func(seed=seed_a), file_a)
        gen.save_to_file(gen_func(seed=seed_b), file_b)
        
        scan_a = f"Scan_{exp_name}_A.png"
        scan_b = f"Scan_{exp_name}_B.png"
        
        # === ВЫЗОВ EXE ===
        print(f"Scanning Phantom A (via EXE)...")
        try:
            subprocess.run(
                [SCANNER_EXE, config.config_filename, file_a, scan_a],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"\n!!! SCANNER EXE CRASHED !!!")
            print(f"Exit Code: {e.returncode}")
            print(f"STDERR:\n{e.stderr}") 
            return 

        print(f"Scanning Phantom B (via EXE)...")
        try:
            subprocess.run(
                [SCANNER_EXE, config.config_filename, file_b, scan_b],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            print(f"\n!!! SCANNER EXE CRASHED !!!")
            print(f"STDERR:\n{e.stderr}")
            return
        
        print(f"Generating Maps...")
        maps_a = Processor.generate_maps(scan_a)
        maps_b = Processor.generate_maps(scan_b)
        
        print(f"Calculating Metrics (A vs B)...")
        map_types = ['Struct', 'OAC', 'SC', 'RSC']
        
        for m_type in map_types:
            path_a = maps_a[m_type]
            path_b = maps_b[m_type]
            
            metrics = calculate_all_metrics(path_a, path_b)
            
            if metrics:
                row = {
                    'Experiment': exp_name,
                    'Map_Type': m_type,
                    **metrics
                }
                all_results.append(row)
                
                # === FORMATTED PRINTING ===
                # Helper to format floats or print N/A
                def fmt(val): return f"{val:.4f}" if isinstance(val, (int, float)) and not np.isnan(val) else "N/A"
                
                print(f"   [{m_type:6}] SSIM: {fmt(row.get('SSIM'))} | MS-SSIM: {fmt(row.get('MS-SSIM'))} | "
                      f"PSNR: {fmt(row.get('PSNR'))} | MSE: {fmt(row.get('MSE'))} | "
                      f"VIF: {fmt(row.get('VIF'))} | LPIPS: {fmt(row.get('LPIPS'))}")

    # === STAGE 3: Cross-Comparison ===
    print("\n--- Running Cross-Comparison: Uniform vs Layers ---")
    scan_uniform = "Scan_Exp1_Uniform_A.png"
    scan_layers = "Scan_Exp2_Layers_A.png"
    
    if os.path.exists(scan_uniform) and os.path.exists(scan_layers):
        print(f"Comparing: {scan_uniform} vs {scan_layers}")
        maps_uniform = Processor.generate_maps(scan_uniform)
        maps_layers = Processor.generate_maps(scan_layers)
        
        map_types = ['Struct', 'OAC', 'SC', 'RSC']
        for m_type in map_types:
            path_u = maps_uniform[m_type]
            path_l = maps_layers[m_type]
            metrics = calculate_all_metrics(path_u, path_l)
            if metrics:
                row = {
                    'Experiment': "Cross_Uniform_vs_Layers",
                    'Map_Type': m_type,
                    **metrics
                }
                all_results.append(row)
                
                def fmt(val): return f"{val:.4f}" if isinstance(val, (int, float)) and not np.isnan(val) else "N/A"
                
                print(f"   [{m_type:6}] SSIM: {fmt(row.get('SSIM'))} | MS-SSIM: {fmt(row.get('MS-SSIM'))} | "
                      f"PSNR: {fmt(row.get('PSNR'))} | MSE: {fmt(row.get('MSE'))} | "
                      f"VIF: {fmt(row.get('VIF'))} | LPIPS: {fmt(row.get('LPIPS'))}")

    csv_file = "Final_Metrics_Report.csv"
    if all_results:
        keys = all_results[0].keys()
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_results)
        print(f"\n=== DONE. Results saved to {csv_file} ===")
    else:
        print("\nNo results generated.")

if __name__ == "__main__":
    run_experiment_pipeline()
