import os
import glob
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re
import warnings

warnings.filterwarnings("ignore")

# ==============================================================================
# CONFIGURATION
# ==============================================================================
RESULTS_ROOT = "Results_MICCAI_Experiment"
RAW_DATA_DIR = os.path.join(RESULTS_ROOT, "Raw_Data")
PLOTS_DIR = os.path.join(RESULTS_ROOT, "Plots_Sensitivity_Final")

# Metrics to look for
POTENTIAL_METRICS = ['MS-SSIM', 'LPIPS', 'SSIM', 'MSE', 'PSNR', 'VIF']
MAP_TYPES = ['Struct', 'OAC', 'SC', 'RSC']

# Series Display Config (ONLY Macro and Meso)
SERIES_INFO = {
    'Macro_Thickness': {'label': 'Macro (Thickness)', 'color': '#1f77b4', 'marker': 'o'}, # Blue
    'Meso_Count':      {'label': 'Meso (Void Count)', 'color': '#ff7f0e', 'marker': 's'}, # Orange
}

# ==============================================================================
# 1. PARSING LOGIC
# ==============================================================================
def get_normalized_step(series_name, step_name):
    """
    Parses folder name to extract physics-based value and maps it to 
    Distortion Level 1..10.
    """
    s_str = str(step_name)
    try:
        val = int(re.search(r'\d+', s_str).group())
    except:
        return None

    # --- MACRO (Thickness) ---
    # Baseline: 400. Range in folders: 380 -> 200.
    # Distortion: Thickness DECREASING from 400.
    # Step 1: 380 (Diff 20). Step 10: 200 (Diff 200).
    if series_name == 'Macro_Thickness':
        diff = 400 - val
        step = diff // 20
        return step

    # --- MESO (Void Count) ---
    # Baseline: 20. Range in folders: 39 -> 20.
    # Distortion: Count INCREASING from 20 to 40.
    # Step 1: 22 (Diff 2). Step 9: 38 (Diff 18).
    # We map (Count - 20) / 2.
    elif series_name == 'Meso_Count':
        diff = val - 20
        # Check if even step (to align with 1-10 integer grid)
        # Note: 'Count_20' is Baseline (Diff 0).
        if diff <= 0: return None # Should be treated as baseline or skipped here
        
        if diff % 2 != 0:
            return None # Skip odd counts (21, 23...)
            
        step = diff // 2
        return step

    return None

# ==============================================================================
# 2. DATA LOADING (MIN/MAX Logic)
# ==============================================================================
def get_stats_minmax(series_data):
    """Returns Median, Min (Low), Max (High) for 100% interval"""
    if series_data.empty: return np.nan, np.nan, np.nan
    v = series_data.dropna().values
    if len(v) == 0: return np.nan, np.nan, np.nan
    
    med = np.median(v)
    low = np.min(v)
    high = np.max(v)
    return med, low, high

def load_all_data():
    if not os.path.exists(RAW_DATA_DIR):
        print(f"Error: {RAW_DATA_DIR} not found.")
        return None, None
        
    all_files = glob.glob(os.path.join(RAW_DATA_DIR, "*.csv"))
    if not all_files:
        print("No CSV files found.")
        return None, None
        
    print(f"Found {len(all_files)} files. Parsing...")
    
    baseline_stats = {} 
    series_data_points = []
    detected_metrics = set()
    
    for f in all_files:
        try:
            df = pd.read_csv(f)
            if df.empty: continue
            
            # Identify columns
            cols = [c for c in df.columns if c in POTENTIAL_METRICS]
            for c in cols: detected_metrics.add(c)
            
            # Read metadata
            series_name = df.iloc[0]['Series']
            map_type = df.iloc[0]['Map_Type']
            step_name = df.iloc[0]['Step_Name'] 
            
            # --- BASELINE ---
            if series_name == 'Baseline':
                for met in cols:
                    med, low, high = get_stats_minmax(df[met])
                    baseline_stats[(met, map_type)] = (med, low, high)
                continue

            # --- SERIES ---
            # Filter only requested series
            if series_name not in SERIES_INFO:
                continue

            norm_step = get_normalized_step(series_name, step_name)
            
            if norm_step is None:
                continue
                
            for met in cols:
                med, low, high = get_stats_minmax(df[met])
                series_data_points.append({
                    'Series': series_name,
                    'Norm_Step': norm_step,
                    'Map_Type': map_type,
                    'Metric': met,
                    'Median': med,
                    'Low': low,
                    'High': high
                })
                    
        except Exception as e:
            print(f"Error parsing {f}: {e}")
            
    return baseline_stats, pd.DataFrame(series_data_points), list(detected_metrics)

# ==============================================================================
# 3. PLOTTING
# ==============================================================================
def run_plotter():
    base_stats, df_series, valid_metrics = load_all_data()
    
    if not valid_metrics:
        print("No valid metrics found.")
        return
        
    os.makedirs(PLOTS_DIR, exist_ok=True)
    print(f"Generating plots in: {PLOTS_DIR}")
    
    for metric in valid_metrics:
        # Figure Setup
        fig, axes = plt.subplots(1, 4, figsize=(26, 6), constrained_layout=True)
        fig.suptitle(f"Metric Sensitivity Analysis: {metric}", fontsize=24, fontweight='bold', y=1.05)
        
        for idx, map_type in enumerate(MAP_TYPES):
            ax = axes[idx]
            ax.set_title(f"Map: {map_type}", fontsize=18)
            
            # --- 1. Draw Baseline (Noise Floor 100% Interval) ---
            if (metric, map_type) in base_stats:
                b_med, b_low, b_high = base_stats[(metric, map_type)]
                # Full band
                ax.axhspan(b_low, b_high, color='gray', alpha=0.25, label='Baseline (100% Interval)')
                ax.axhline(b_med, color='gray', linestyle='--', alpha=0.6)
            else:
                b_med, b_low, b_high = np.nan, np.nan, np.nan
            
            # --- 2. Draw Series Curves ---
            if not df_series.empty:
                sub = df_series[(df_series['Metric'] == metric) & 
                                (df_series['Map_Type'] == map_type)]
                
                for s_name in SERIES_INFO.keys():
                    s_sub = sub[sub['Series'] == s_name].sort_values('Norm_Step')
                    if s_sub.empty: continue
                    
                    x = s_sub['Norm_Step'].values
                    y = s_sub['Median'].values
                    lows = s_sub['Low'].values
                    highs = s_sub['High'].values
                    
                    # Prepend Baseline at X=0
                    if not np.isnan(b_med):
                        x_plot = np.insert(x, 0, 0)
                        y_plot = np.insert(y, 0, b_med)
                    else:
                        x_plot, y_plot = x, y
                        
                    props = SERIES_INFO.get(s_name)
                    
                    # Error Bars (Whiskers)
                    # For X=0 (Baseline), we don't plot error bars on the line itself to keep it clean,
                    # as the gray band shows the baseline spread.
                    # We plot error bars for steps 1..10
                    
                    # Calculate asymmetric error for errorbar function
                    y_err_low = y - lows
                    y_err_high = highs - y
                    y_err = [y_err_low, y_err_high]
                    
                    ax.errorbar(x, y, yerr=y_err, fmt='none', ecolor=props['color'], 
                                capsize=4, elinewidth=1.5, alpha=0.8)

                    # Plot Line
                    ax.plot(x_plot, y_plot, marker=props['marker'], label=props['label'], 
                            color=props['color'], linewidth=2.5, markersize=7)
                    
                    # --- 3. Check Separation (Stars) ---
                    # Separation: Full Disjoint Intervals [Low, High] vs [B_Low, B_High]
                    if not np.isnan(b_low):
                        sep_x = []
                        sep_y = []
                        
                        for i in range(len(lows)):
                            s_low = lows[i]
                            s_high = highs[i]
                            
                            # Overlap Logic: max(L1, L2) <= min(H1, H2)
                            overlap = max(b_low, s_low) <= min(b_high, s_high)
                            
                            if not overlap:
                                sep_x.append(x[i])
                                # Put star slightly offset or exactly on point
                                sep_y.append(y[i])
                        
                        if sep_x:
                            ax.plot(sep_x, sep_y, '*', color=props['color'], 
                                    markersize=20, markeredgecolor='black', zorder=10)

            # --- 4. Styling ---
            ax.set_xlabel("Distortion Level", fontsize=14, fontweight='bold')
            ax.set_xticks(np.arange(0, 11, 1))
            
            if idx == 0:
                ax.set_ylabel(metric, fontsize=14, fontweight='bold')
                # Move legend inside or below
                ax.legend(loc='upper left', fontsize=11, framealpha=0.95)
                
                # Descriptive Text
                desc = "Distortion 0: Baseline\nDistortion 10: 2x Change\n(Half Thickness / Double Voids)"
                ax.text(0.05, 0.05, desc, transform=ax.transAxes, 
                        fontsize=10, bbox=dict(facecolor='white', alpha=0.8))
            
            ax.grid(True, linestyle=':', alpha=0.6)
            ax.tick_params(labelsize=12)
            
        plt.savefig(os.path.join(PLOTS_DIR, f"Sensitivity_{metric}.png"), dpi=300, bbox_inches='tight')
        plt.close()
        print(f"   -> Saved Plot_{metric}")

    print(f"\nDone. Plots in {PLOTS_DIR}")

if __name__ == "__main__":
    run_plotter()
