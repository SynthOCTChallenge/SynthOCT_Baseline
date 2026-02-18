import os
import glob
import itertools
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from skimage import io, img_as_float
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import mean_squared_error as mse
from skimage.metrics import peak_signal_noise_ratio as psnr

import warnings
warnings.filterwarnings("ignore")
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

# ==============================================================================
# CONFIGURATION (CHANGE THIS PER EXPERIMENT)
# ==============================================================================

# 1. MICRO
# INPUT_DIR = "Dataset_Micro"
# REFERENCE_SET = "Dens_200000"

# 2. MESO
INPUT_DIR = "Dataset"
REFERENCE_SET = "Meso_Amp"

# 3. MACRO
# INPUT_DIR = "Dataset_Macro"
# REFERENCE_SET = "Macro_Thin"

OUTPUT_DIR = f"Results_{INPUT_DIR}" # Results will go here
NEIGHBOR_DEPTH = 5 

# ==============================================================================
# INIT
# ==============================================================================
ML_AVAILABLE = False
try:
    import torch
    import lpips
    DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
    loss_fn_alex = lpips.LPIPS(net='alex', verbose=False).to(DEVICE)
    ML_AVAILABLE = True
    print(f"[Init] LPIPS enabled on {DEVICE}")
except:
    print("[Init] LPIPS disabled")

SEWAR_AVAILABLE = False
try:
    from sewar.full_ref import vifp, msssim
    SEWAR_AVAILABLE = True
    print("[Init] MS-SSIM/VIF enabled")
except:
    print("[Init] MS-SSIM/VIF disabled")

def calc_pair_metrics(p1, p2):
    res = {}
    try:
        i1 = io.imread(p1, as_gray=True); i1 = img_as_float(i1)
        i2 = io.imread(p2, as_gray=True); i2 = img_as_float(i2)
        if i1.shape != i2.shape: return {}
        
        res['MSE'] = mse(i1, i2)
        res['PSNR'] = psnr(i1, i2, data_range=1.0)
        res['SSIM'] = ssim(i1, i2, data_range=1.0)
        
        if SEWAR_AVAILABLE:
            u1 = (i1*255).astype(np.uint8); u2 = (i2*255).astype(np.uint8)
            try: res['VIF'] = vifp(u1, u2)
            except: res['VIF'] = np.nan
            try: res['MS-SSIM'] = float(np.real(msssim(u1, u2)))
            except: res['MS-SSIM'] = np.nan
            
        if ML_AVAILABLE:
            t1 = torch.from_numpy(i1).float().view(1,1,i1.shape[0],i1.shape[1]).to(DEVICE)
            t2 = torch.from_numpy(i2).float().view(1,1,i2.shape[0],i2.shape[1]).to(DEVICE)
            res['LPIPS'] = loss_fn_alex(t1.repeat(1,3,1,1)*2-1, t2.repeat(1,3,1,1)*2-1).item()
    except: pass
    return res

def get_files(folder_name, map_type):
    path = os.path.join(INPUT_DIR, folder_name)
    if not os.path.exists(path): return []
    base = sorted(glob.glob(os.path.join(path, "Scan_*.png")))
    structs = [f for f in base if "_OAC" not in f and "_SC" not in f and "_RSC" not in f]
    if map_type == 'Struct': return structs
    return [f.replace(".png", f"_{map_type}.png") for f in structs]

def check_interval_overlap(low1, high1, low2, high2):
    return max(low1, low2) <= min(high1, high2)

def run_analysis():
    if not os.path.exists(INPUT_DIR):
        print(f"Error: {INPUT_DIR} not found.")
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    dirs = {
        'csv': os.path.join(OUTPUT_DIR, "Raw_CSVs"),
        'corr': os.path.join(OUTPUT_DIR, "Correlations"),
        'plots': os.path.join(OUTPUT_DIR, "Plots")
    }
    for d in dirs.values(): os.makedirs(d, exist_ok=True)
    
    map_types = ['Struct', 'OAC', 'SC', 'RSC']
    metric_names = ['MSE', 'PSNR', 'SSIM', 'MS-SSIM', 'VIF', 'LPIPS']
    
    # 1. Discover Folders
    all_folders = sorted([d for d in os.listdir(INPUT_DIR) if os.path.isdir(os.path.join(INPUT_DIR, d))])
    if REFERENCE_SET in all_folders:
        all_folders.remove(REFERENCE_SET)
        all_folders.insert(0, REFERENCE_SET)
    else:
        print(f"Warning: Reference set '{REFERENCE_SET}' not found.")
    
    print(f"Analyzing sets: {all_folders}")
    
    stats_rows = []
    all_raw_corr = []

    for mt in map_types:
        print(f"  > Map: {mt}")
        
        # 1. Collect Distributions
        distributions = {} 
        comp_types = {}
        
        pairs = list(itertools.combinations_with_replacement(all_folders, 2))
        
        for (name_a, name_b) in pairs:
            if name_a == name_b:
                c_type = "Intra"
                tag = f"Intra_{name_a}"
            elif name_a == REFERENCE_SET:
                c_type = "Inter"
                tag = f"Inter_{name_b}"
            elif name_b == REFERENCE_SET:
                c_type = "Inter"
                tag = f"Inter_{name_a}"
            else:
                c_type = "Cross"
                tag = f"Cross_{name_a}_vs_{name_b}"
            
            distributions[tag] = {m: [] for m in metric_names}
            comp_types[tag] = c_type
            
            files_a = get_files(name_a, mt)
            files_b = get_files(name_b, mt)
            
            raw_rows = []
            
            for i in range(len(files_a)):
                if c_type == "Intra":
                    j_range = range(i + 1, min(i + 1 + NEIGHBOR_DEPTH, len(files_a)))
                else:
                    j_start = max(0, i - NEIGHBOR_DEPTH)
                    j_end = min(len(files_b), i + NEIGHBOR_DEPTH + 1)
                    j_range = range(j_start, j_end)
                
                for j in j_range:
                    if c_type != "Intra" and i == j: continue
                    
                    res = calc_pair_metrics(files_a[i], files_b[j])
                    if res:
                        for m, v in res.items(): distributions[tag][m].append(v)
                        
                        row = {'File1': os.path.basename(files_a[i]), 'File2': os.path.basename(files_b[j])}
                        row.update(res)
                        raw_rows.append(row)
                        
                        rec = {'Map': mt, 'Type': c_type, 'Comparison': tag}
                        rec.update(res)
                        all_raw_corr.append(rec)
            
            # Save Raw CSV
            if raw_rows:
                pd.DataFrame(raw_rows).to_csv(os.path.join(dirs['csv'], f"{mt}_{tag}.csv"), index=False)

        # 2. Compute Stats & Significance
        # Baseline intervals
        baseline_intervals = {}
        base_tag = f"Intra_{REFERENCE_SET}"
        
        if base_tag in distributions:
            for m in metric_names:
                vals = distributions[base_tag][m]
                if vals:
                    baseline_intervals[m] = (np.percentile(vals, 2.5), np.percentile(vals, 97.5))
                else:
                    baseline_intervals[m] = (np.nan, np.nan)
        
        for tag, metrics in distributions.items():
            for m, vals in metrics.items():
                if not vals: continue
                
                mu = np.mean(vals)
                low = np.percentile(vals, 2.5)
                high = np.percentile(vals, 97.5)
                
                is_overlap = True
                base_low, base_high = baseline_intervals.get(m, (np.nan, np.nan))
                
                if tag != base_tag and not np.isnan(base_low):
                    is_overlap = check_interval_overlap(base_low, base_high, low, high)
                
                stats_rows.append({
                    'Map': mt, 'Comparison': tag, 'Type': comp_types[tag], 'Metric': m,
                    'Mean': mu, 'P_2_5': low, 'P_97_5': high,
                    'Diagnostic_Power': not is_overlap
                })

    # Save Results
    pd.DataFrame(stats_rows).to_csv(os.path.join(OUTPUT_DIR, "Summary_Stats.csv"), index=False)
    
    # Generate Plots
    def get_color(c):
        if 'Intra' in c: return '#2ca02c'
        if 'Inter' in c: return '#d62728'
        return '#1f77b4'

    print("  > Plotting...")
    for m in metric_names:
        fig, axes = plt.subplots(1, 4, figsize=(24, 8), constrained_layout=True)
        fig.suptitle(f"Metric Performance: {m} (Empirical 95% Interval)", fontsize=20)
        
        for idx, mt in enumerate(map_types):
            ax = axes[idx]
            data = pd.DataFrame(stats_rows)
            data = data[(data['Map']==mt) & (data['Metric']==m)]
            if data.empty: continue
            
            # Sort: Intra, Inter, Cross
            data['sort'] = data['Comparison'].apply(lambda x: 0 if 'Intra' in x else (1 if 'Inter' in x else 2))
            data = data.sort_values(['sort', 'Comparison'])
            
            cols = [get_color(c) for c in data['Comparison']]
            yerr = [data['Mean'] - data['P_2_5'], data['P_97_5'] - data['Mean']]
            
            ax.bar(data['Comparison'], data['Mean'], yerr=yerr, capsize=5, color=cols, alpha=0.7)
            ax.set_title(mt, fontsize=16)
            ax.set_xticklabels(data['Comparison'], rotation=90)
            ax.grid(axis='y', linestyle='--')
            
            for i, row in enumerate(data.itertuples()):
                if row.Comparison != f"Intra_{REFERENCE_SET}" and row.Diagnostic_Power:
                    y_pos = row.P_97_5 + (row.P_97_5 - row.P_2_5)*0.1
                    ax.text(i, y_pos, '*', ha='center', fontsize=20)

        plt.savefig(os.path.join(dirs['plots'], f"Plot_{m}.png"))
        plt.close()

    print(f"[Done] Check {OUTPUT_DIR}")

if __name__ == "__main__":
    run_analysis()
