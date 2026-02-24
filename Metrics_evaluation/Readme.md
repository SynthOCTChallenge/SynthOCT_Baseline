# Benchmarking OCT Scans Similarity Metrics

**Physics-Based Simulatory Analysis with Controlled Micro-, Meso-, and Macro-Structural Shifts**

This repository contains the evaluation scripts and results for the paper submitted to **MICCAI 2026**. It provides tools to benchmark similarity metrics (MSE, PSNR, SSIM, MS-SSIM, VIF, LPIPS) on synthetic OCT B-scans with strictly controlled structural parameters.

## 📂 Dataset

The synthetic dataset used for this benchmark is hosted on Zenodo. It includes Ground Truth scatterer maps, structural OCT scans, and physics-based parametric maps (OAC, SC, RSC) via [Processor](https://github.com/SynthOCTChallenge/SynthOCT_Baseline/blob/main/Part3_Processor.py).

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.18670884.svg)](https://doi.org/10.5281/zenodo.18670884)

**[Download Dataset from Zenodo](https://zenodo.org/records/18670884)**

### Structural Levels
The benchmark covers three scales of structural changes:
1.  **Micro-structure:** Sensitivity to sub-resolution scatterer density and amplitude statistics.
2.  **Meso-structure:** Sensitivity to discrete inclusions (cysts, vessels) on a speckle background.
3.  **Macro-structure:** Sensitivity to morphological layer thickness changes on a heterogeneous background.

### Additional dataset for sensitivity evaluation
**Metrics_Sensitivity_Benchmark_Grading_structural_changes.zip**

This dataset contains physics-based synthetic OCT B-scans designed to evaluate the sensitivity of metrics to structural changes against a background of speckle noise. The archive is organized into three main sections:
1.  **Baseline:** Containing 20 independent speckle realizations of a fixed structure (400 micron layer thickness, 20 inclusions) to establish the noise floor.
2.  **Series1_Macro_Thickness:** Containing 10 steps of graded macro-structural changes where the epithelial layer thickness decreases from 380 microns to 200 microns (approaching a 2x reduction).
3.  **Series2_Meso_Count:** Containing graded steps of meso-structural changes where the number of void inclusions increases from 20 to 39 (approaching a 2x increase).

Each step in these series contains 20 independent scans to allow for statistical analysis of metric distributions.

---

##  🚀 Repository Structure

```text
├── Metrics_evaluation/
│   ├── Metrics_Stats_CSV.zip           # Pre-calculated metric statistics (Raw Data)
│   ├── Results_MICCAI_Experiment.zip                              # Pre-calculated CSVs for Sensitivity Analysis
│   ├── Metric_Performance_Test_v5_MicroMesoMacro_Empirical.py   # Main script for calculating metrics
│   ├── Metrics_Plots_with_Intervals_and_SignificanceLevel.py      # Script for generating publication-ready plots
│   ├── Metric_Plotter_MICCAI_Experiment_sensitivity_final.py      # Script for generating sensitivity curves
│   └── Illustrations.png   # Synth OCT scan examples
│   └── Physics_maps.png   # physics-based maps
│   └── Sensitivity_Experiments_Setup.png
│   └── Resutls.png   # Metrics evaluation results
│   └── Sensitivity_Evaluation_Results.png
│   └──  README.md
```

## 📊 Evaluation Methodology
We evaluate metrics based on their Diagnostic Sensitivity, defined as the statistical separation between:

Intra-class Baseline: The metric distribution when comparing different realizations of the same tissue structure (speckle noise only); representing the ultimate reachable similarity level in speckled conditions for the same structural patterns.

Inter-class Target (Signal): The metric distribution when comparing the baseline tissue to a structurally altered tissue.

Significance Levels (Stars)

(*): 95% empirical intervals are separated (<5% overlap).

(** ): 100% ranges (min-max) are fully separated.

(*** ): Robust separation (Gap > Sum of Standard Deviations).

## Simulation of Structural Shifts
<p align="center"><img src="Illustrations_compressed.png" width="800" alt="Illustrations">

 Visualization of the synthetic datasets representing three scales of structural changes: (a) Micro-structure (scatterer density), (b) Meso-structure (inclusions), and (c) Macro-structure (layered morphology).



## Physics-Based Parametric Maps
<p align="center"><img src="Physics_maps_compressed.png" width="800" alt="Physics_maps">
 
Physics-based parametric maps derived from synthetic OCT B-scans. (a) Speckle Contrast (SC) map: Characterizes microstructural inhomogeneities but remains confounded by depth-dependent signal attenuation; (b) Optical Attenuation Coefficient (OAC) map: Provides a pixel-level representation of the backscattering energy distribution within each spatially resolved volume; (c) Refined Speckle Contrast (RSC) map: Calculated directly from the OAC map to reveal the pure inhomogeneity of the scatterer distribution, independent of in-depth attenuation artifacts. Together, OAC and RSC provide a physics-consistent and spatially resolved characterization of tissue structure.

## Experimental Setup (Sensitivity Analysis)
<p align="center"><img src="Sensitivity_Experiments_Setup.png" alt="Experiment Setup">
Visual overview of the synthetic OCT dataset generation and structural perturbation experiments. (a) The Baseline (BL) configuration representing the system's noise floor, consisting of: (a-1) the structural B-scan (generated with 400 µm epithelial thickness and 20 dermal void inclusions), and its derived physics-based maps: (a-2) Optical Attenuation Coefficient (OAC), (a-3) Refined Speckle Contrast (RSC), and (a-4) Speckle Contrast (SC). Two distinct numerical experiments were conducted to grade structural deviations from this baseline: (b) Experiment 1 (Macro-changes): Simulation of epithelial thinning, where the top layer thickness decreases from 400 to 200 µm over 10 steps. Panels (b-1) through (b-4) show the resulting structural scan and derived maps at a high distortion level. (c) Experiment 2 (Meso-changes): Simulation of increased tissue heterogeneity, where the number of meso-structural void inclusions in the dermis increases from 20 to 39 over 10 steps. Panels (c-1) through (c-4) display the corresponding scan and maps for the modified structure.

## Metric Performance Results
<p align="center"><img src="Results_compressed.png" width="800" alt="Results">
 
Metric performance results grouped by the type of structural changes (Micro-, Meso-, and Macro-structure). The diagnostic sensitivity is estimated as the separation between the intra-class baseline distribution (green bars), representing the ultimate reachable similarity level in speckled conditions for the same structural patterns, and the inter-class target distribution (red bars) representing structural shifts. Significance levels denote the separation of empirical value ranges: no star indicates overlapping ranges; (* ) indicates separation of the 95% empirical intervals (<5% overlap); (** ) indicates fully separated ranges (100% min-max separation); and (*** ) indicates robust separation where the gap between distributions exceeds the sum of their standard deviations. MS-SSIM and LPIPS achieved the highest overall sensitivity scores (31). These metrics demonstrated superior consistency across all scales, particularly excelling in detecting meso- and macro-structural anomalies, and proved highly effective on physics-consistent maps (OAC and RSC) even for micro-structural shifts (e.g., LPIPS achieved *** on OAC and MS-SSIM achieved ** on RSC, matching the high sensitivity of MSE/PSNR while offering better structural specificity).

## Metric Sensitivity Results
<p align="center"><img src="Sensitivity_Experiments_Setup.png" alt="Sensitivity Results">
Comprehensive diagnostic sensitivity benchmark of six IQA metrics across four physics-based map types. The figure evaluates the performance of (a) MSE, (b) PSNR, (c) SSIM, (d) MS-SSIM, (e) VIF, and (f) LPIPS. Columns (1–4) correspond to the input modality: (-1) Structural B-scans, (-2) Optical Attenuation Coefficient (OAC), (-3) Speckle Contrast (SC), and (-4) Refined Speckle Contrast (RSC) maps. Graph Details: The X-axis indicates the Distortion Level (0–10), representing a linear progression from the baseline to a ~2x physical change. Blue circles track Macro-structural changes (epithelial thinning: 400 to 200 µm). Orange squares track Meso-structural changes (void inclusion count: 20 to 39). Error bars represent the full range (min-max) of values for n=20 independent speckle realizations. Significance: The gray shaded band defines the "noise floor" (100% interval of intra-class baseline variability). Star markers (⋆) indicate the sensitivity threshold: the point where the metric’s distribution for the perturbed state becomes fully separated from the baseline noise floor (no overlap). Note that while pixel-wise metrics (MSE, PSNR) struggle to differentiate meso-scale changes (orange) from speckle noise, MS-SSIM and LPIPS demonstrate robust sensitivity, particularly when applied to physics-based OAC and RSC maps.



## 🛠️ Usage

1. Calculate Metrics
 
To re-run the metric calculations on the dataset:

Download the dataset from Zenodo and extract it to Dataset/.

Run the analysis script:

Metric_Performance_Test_v5_MicroMesoMacro_Empirical.py

Note: You may need to edit the INPUT_DIR variable in the script to point to specific subfolder

2. Generate Plots
   
To generate the bar charts with significance stars from the provided CSVs:

Metrics_Plots_with_Intervals_and_SignificanceLevel.py

Note: The metric statistics are already calculated and provided in this repository. You do not need to re-run the heavy computation to reproduce the figures.
Unzip Metrics_Stats_CSV.zip. Ensure the extracted folder is named Metrics_Stats_CSV and is located in the same directory as the scripts.

Run the plotting script

3. Generate Sensitivity Analysis Plots

To reproduce the sensitivity curves for Macro/Meso grading:

Unzip Results_MICCAI_Experiment.zip. Ensure it contains the Results_MICCAI_Experiment/Raw_Data/ folder with CSV files.

Run the sensitivity plotter: python Metric_Plotter_MICCAI_Experiment_sensitivity_final.py

This will generate the sensitivity panels showing metric responses to graded structural changes.


## 📚 Citation

If you use this code or dataset, please cite the following works:

Dataset:

[Link to Zenodo Record](https://zenodo.org/records/18670884)

Methodology:
```text
 [1] Sovetsky, A., Matveyev, A., Chizhov, P., Zaitsev, V., Matveev, L. (2025). OCT Scans Simulation Framework for Data Augmentation and Controlled Evaluation of Signal Processing Approaches. In: Fernandez, V., et al. (eds) Simulation and Synthesis in Medical Imaging. SASHIMI 2024. LNCS, vol 15187. Springer, Cham. https://doi.org/10.1007/978-3-031-73281-2_12
```
```text
 [2] Nikoshin, D., Mikhailenko, D., Sovetsky, A., Matveyev, A., Zaitsev, V., Matveev, L. (2026). From Tissue-Mimicking Phantoms to Physics-Based Scans: Synthetic OCT for Few-Shot Foundation Model Training. In: Fernandez, V., et al. (eds) Simulation and Synthesis in Medical Imaging. SASHIMI 2025. LNCS, vol 16085. Springer, Cham. https://doi.org/10.1007/978-3-032-05573-6_5
```
```text
 [3] MICCAI 2026 submission (will be available soon)
```
