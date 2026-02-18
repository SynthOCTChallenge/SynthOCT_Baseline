import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==============================================================================
# CONFIGURATION
# ==============================================================================
# Folder containing CSV files
INPUT_CSV_DIR = "Metrics_Stats_CSV" 

# Output folder for plots
OUTPUT_PLOT_DIR = "Final_Publication_Plots"

# Dataset Keywords (as they appear in filenames)
# We compare Intra_Baseline vs Cross_Baseline_vs_Target
SET_BASELINE = "Meso_Both" 
SET_TARGET   = "Macro_Thin"   

# Metrics and Maps to process
METRICS = ['MSE', 'PSNR', 'SSIM', 'MS-SSIM', 'VIF', 'LPIPS']
MAPS = ['Struct', 'OAC', 'SC', 'RSC']

# ==============================================================================
# LOGIC
# ==============================================================================

def find_file(map_type, is_intra):
    """
    Finds the correct CSV file based on the naming convention.
    
    Args:
        map_type (str): e.g., 'Struct', 'OAC'
        is_intra (bool): True for Intra-class, False for Inter-class comparison.
        
    Returns:
        str: Path to the file or None.
    """
    if not os.path.exists(INPUT_CSV_DIR): return None
    
    if is_intra:
        # Pattern: {Map}_Intra_{Baseline}.csv
        # Example: OAC_Intra_Macro_Thick.csv
        name = f"{map_type}_Intra_{SET_BASELINE}.csv"
        path = os.path.join(INPUT_CSV_DIR, name)
        return path if os.path.exists(path) else None
    else:
        # Pattern: {Map}_Cross_{Baseline}_vs_{Target}.csv (or reverse order)
        # Example: OAC_Cross_Macro_Thick_vs_Macro_Thin.csv
        name1 = f"{map_type}_Cross_{SET_BASELINE}_vs_{SET_TARGET}.csv"
        name2 = f"{map_type}_Cross_{SET_TARGET}_vs_{SET_BASELINE}.csv"
        
        p1 = os.path.join(INPUT_CSV_DIR, name1)
        p2 = os.path.join(INPUT_CSV_DIR, name2)
        
        if os.path.exists(p1): return p1
        if os.path.exists(p2): return p2
        return None

def get_stats_and_rating(df_intra, df_inter, metric):
    """
    Calculates statistics (Mean, 95% Interval) and Significance Level (Stars).
    
    Returns:
        dict: {'intra': (mu, low_err, high_err), 'inter': ..., 'stars': str}
    """
    if metric not in df_intra.columns or metric not in df_inter.columns:
        return None
    
    # Extract values, dropping NaNs
    v1 = df_intra[metric].dropna().values
    v2 = df_inter[metric].dropna().values
    
    if len(v1) == 0 or len(v2) == 0: return None
    
    # 1. Statistics for Plotting (Mean + 95% CI/Range)
    # We use empirical percentiles (2.5% and 97.5%)
    mu1, l1, h1 = np.mean(v1), np.percentile(v1, 2.5), np.percentile(v1, 97.5)
    mu2, l2, h2 = np.mean(v2), np.percentile(v2, 2.5), np.percentile(v2, 97.5)
    
    # 2. Statistics for Star Rating (Min/Max/Std)
    min1, max1, std1 = np.min(v1), np.max(v1), np.std(v1)
    min2, max2, std2 = np.min(v2), np.max(v2), np.std(v2)
    
    # Determine Star Rating
    star_label = ""
    
    # Level 1: Do 95% intervals overlap?
    # Intersection check: max(lows) <= min(highs)
    overlap_95 = max(l1, l2) <= min(h1, h2)
    
    if not overlap_95:
        star_label = "(*)" # Significant (p < 0.05 equivalent)
        
        # Level 2: Do 100% ranges (Min-Max) overlap?
        overlap_100 = max(min1, min2) <= min(max1, max2)
        
        if not overlap_100:
            star_label = "(**)" # Highly Significant (Total Separation)
            
            # Level 3: Is there a large safety margin?
            # Margin > Sum of Standard Deviations
            # Gap is the distance between the closest edges of the distributions
            if min1 > max2: gap = min1 - max2
            else: gap = min2 - max1
            
            if gap > (std1 + std2):
                star_label = "(***)" # Robust Separation

    stats = {
        'intra': (mu1, mu1-l1, h1-mu1), # Mean, LowerError, UpperError
        'inter': (mu2, mu2-l2, h2-mu2),
        'stars': star_label
    }
    return stats

def run():
    # Create output directory
    os.makedirs(OUTPUT_PLOT_DIR, exist_ok=True)
    print(f"Generating publication plots in '{OUTPUT_PLOT_DIR}'...")
    
    for metric in METRICS:
        print(f"Processing {metric}...")
        
        labels = []
        means_1, errs_1 = [], [[], []]
        means_2, errs_2 = [], [[], []]
        
        valid_maps = False
        
        for m_type in MAPS:
            # Locate files
            f_intra = find_file(m_type, True)
            f_inter = find_file(m_type, False)
            
            if not f_intra or not f_inter:
                print(f"  [!] Missing files for {m_type}. Skipping.")
                continue
                
            try:
                # Load Data
                d1 = pd.read_csv(f_intra)
                d2 = pd.read_csv(f_inter)
                
                # Compute Stats
                res = get_stats_and_rating(d1, d2, metric)
                if not res: 
                    print(f"  [!] Metric {metric} missing in CSVs.")
                    continue
                
                valid_maps = True
                
                # Format X-Label with Stars (e.g., "OAC\n(***)")
                label = f"{m_type}"
                if res['stars']:
                    label += f"\n{res['stars']}"
                labels.append(label)
                
                # Store Intra Data (Green Bar)
                mu, el, eh = res['intra']
                means_1.append(mu)
                errs_1[0].append(el)
                errs_1[1].append(eh)
                
                # Store Inter Data (Red Bar)
                mu, el, eh = res['inter']
                means_2.append(mu)
                errs_2[0].append(el)
                errs_2[1].append(eh)
                
            except Exception as e:
                print(f"  Error processing {m_type}: {e}")
                
        if not valid_maps:
            print(f"  Skipping plot for {metric} (No valid data).")
            continue
        
        # --- PLOTTING ---
        fig, ax = plt.subplots(figsize=(9, 6))
        
        x = np.arange(len(labels))
        width = 0.35
        
        # Bar 1: Intra-Class Noise (Green)
        rects1 = ax.bar(x - width/2, means_1, width, yerr=errs_1, capsize=5, 
                        label=f'Intra-Class ({SET_BASELINE})', 
                        color='#5cb85c', alpha=0.9, edgecolor='grey', linewidth=0.5)
        
        # Bar 2: Inter-Class Signal (Red)
        rects2 = ax.bar(x + width/2, means_2, width, yerr=errs_2, capsize=5, 
                        label=f'Inter-Class ({SET_BASELINE} vs {SET_TARGET})', 
                        color='#d9534f', alpha=0.9, edgecolor='grey', linewidth=0.5)
        
        # Aesthetics
        ax.set_ylabel(metric, fontsize=12, fontweight='bold')
        ax.set_title(f"Diagnostic Sensitivity: {metric}", fontsize=14)
        ax.set_xticks(x)
        # Using bold font for labels to make stars visible
        ax.set_xticklabels(labels, fontsize=11, fontweight='bold')
        
        ax.legend(fontsize=10, loc='best')
        ax.grid(axis='y', linestyle='--', alpha=0.4)
        
        # Tight layout to handle multi-line labels
        plt.tight_layout()
        
        # Save
        out_path = os.path.join(OUTPUT_PLOT_DIR, f"Diagnostic_{metric}.png")
        plt.savefig(out_path, dpi=300)
        plt.close()
        print(f"  Saved {out_path}")

    print("Done.")

if __name__ == "__main__":
    run()
