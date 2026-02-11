# SynthOCT 2026: Baseline & Evaluation Framework

**Digital Phantoms Simulation for Physics-Based Scans Synthesis in Optical Coherence Tomography**

[![Challenge](https://img.shields.io/badge/Challenge-MICCAI%202026-blue)](http://synthoct.com/)
[![Dataset](https://img.shields.io/badge/Data-Zenodo-green)](https://zenodo.org/records/18095266)
[![License](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey)](https://creativecommons.org/licenses/by/4.0/)

## 📌 Overview

This repository contains the official **Baseline Pipeline** and **Physics-Based Evaluation Framework** for the **SynthOCT 2026 Challenge** (MICCAI Satellite Event).

### The Challenge Mission
Unlike traditional medical image synthesis tasks that focus on visual plausibility (using GANs or Diffusion models), **SynthOCT** requires participants to solve an inverse physics problem: reconstructing the underlying **tissue microstructure**.

Participants must generate **"Digital Phantoms"**—spatial distributions of optical scatterers. These phantoms are processed by our fixed, physics-based **Virtual Scanner** to generate synthetic OCT B-scans. The quality of synthesis is evaluated not just on visual similarity, but on physical consistency using Optical Attenuation Coefficients (OAC) and Speckle Statistics.

## 📂 Repository Structure

The pipeline is modular. Participants are expected to modify **`Part1`** (Generation). **`Part2`** (Scanning) acts as the fixed imaging device.

| File | Type | Description |
| :--- | :--- | :--- |
| **`Part1_Generator.py`** | **Editable** | **The Baseline Model.** Generates 3D coordinates `(x, y, z)` and Backscattering Energy `(%)` for scatterers. Saves them to a `.txt` file. **This is the component you aim to improve.** |
| **`Part2_Scanner.exe`** | **Fixed** | **The Virtual Scanner.** [Download link](https://drive.google.com/file/d/10xO8WTGbaBDIixBwpY9btxwHZAhHF3L2/view?usp=drive_link) A compiled, physics-based simulation engine. It takes the Digital Phantom `.txt` and renders a raw OCT B-scan (`.png`, 51dB dynamic range). |
| **`Part3_Processor.py`** | **Fixed** | **Parametric Mapping.** Converts raw OCT scans into physics-based maps: **OAC** (Optical Attenuation Coefficient), **SC** (Speckle Contrast), and **RSC** (Refined Speckle Contrast). |
| **`Orchestrator.py`** | **Manager** | **Validation Pipeline.** Configured for a **self-consistency check**. It generates four digital phantoms (Unstructured vs. Layered, each with two different speckle realizations) to test metric performance and establish a baseline for structural similarity under stochastic variations speckle patterns (driven by the same scatterers governing distribution function). |

---

## 🚀 Getting Started

### 1. Prerequisites
You need **Python 3.8+** and the following libraries.
*(Note: The Scanner is a standalone `.exe` and does not require Python dependencies to run).*

```bash
pip install numpy scipy matplotlib scikit-image joblib numba sewar lpips torch torchvision
```

### 2. Installation
1.  Clone this repository.
2.  Download Part2_Scanner.exe from: [https://drive.google.com/file/d/10xO8WTGbaBDIixBwpY9btxwHZAhHF3L2/view?usp=drive_link](https://drive.google.com/file/d/10xO8WTGbaBDIixBwpY9btxwHZAhHF3L2/view?usp=drive_link)
3.  **Crucial:** Ensure `Part2_Scanner.exe` is placed in the root directory alongside the python scripts.
4.  For SynthOCT Challenge: Download the reference dataset from [Zenodo](https://zenodo.org/records/18095266).

### 3. Running the Baseline
Run the `Orchestrator.py` script. It executes a **Self-Consistency Check** to demonstrate how metrics behave on physically accurate data versus structural changes.

```bash
python Orchestrator.py
```

The Orchestrator performs the following logic:
  -Generation: Creates Scatterers_*.txt files using Part 1.
  -Scanning: Calls Part2_Scanner.exe with the generated configuration.
  -Mapping: Generates *_OAC.png, *_SC.png, *_RSC.png using Part 3.
  -Reporting: Compares Uniform vs. Layered phantoms and outputs Final_Metrics_Report.csv.

## 🔬 The Virtual Scanner (`Part2_Scanner.exe`)

The scanner is provided as a compiled executable. While the `Orchestrator.py` handles it automatically, you can run it manually for debugging or integration into your own pipelines.
Download link: [Part2_Scanner Download](https://drive.google.com/file/d/10xO8WTGbaBDIixBwpY9btxwHZAhHF3L2/view?usp=drive_link)

### Command Line Usage
```bash
Part2_Scanner.exe <Configuration.ini> <Scatterers.txt> <Output.png>
```

Configuration File Structure (.ini)
The scanner requires a Configuration.ini file to define the optical parameters of the device. The baseline generator creates this automatically, but you can create your own.
Example Configuration.ini:
```
[Parameters]
scan filename = Scan_Raw.bin
scatterers coordinates file = Scatterers_Exp.txt
a-scan pixel numbers = 256
vertical pixel size mcm = 6.0
central wavelength mcm = 1.3
number of a-scans in b-scan = 512
xmax mcm = 3072.0
number of b-scans = 1
ymax mcm = 0.0
beam radius mcm = 10.0
number of scatterers in b-scan = 300000
```
## 🔬 Physics & Data Format

### 1. Digital Phantom Format (`Part1`)
Your algorithm must output a text file with 4 columns:
`X (μm) | Y (μm) | Z (μm) | Energy (%)`

*   **X, Y, Z**: Spatial coordinates of scatterers.
    *   *X range:* -1536 to +1536 μm
    *   *Z range:* 0 to 1536 μm
*   **Energy**: Backscattering Energy in percent (**0..100%**).
    *   `1.0`: Typical biological tissue (~1% energy reflection).
    *   `100.0`: Perfect mirror (100% reflection).
    *   *Physics Note:* The scanner calculates reflection amplitude as $\sqrt{Energy/100}$.

### 2. Scan Output
*   **Format:** `.png` (Grayscale)
*   **Dynamic Range:** 51 dB
*   **Mapping:** Logarithmic scale, mapped to 0-255.

---

## 📊 Full set of Metrics

We use a multi-view evaluation strategy. Synthetic scans are compared against reference scans across four domains: **Structural** (Intensity), **OAC** (Physical), **SC** & **RSC** (Statistical).

| Metric | Type | Direction | Ideal | Interpretation |
| :--- | :--- | :--- | :---: | :--- |
| **SSIM** | Similarity | **$\uparrow$ Higher** | 1.0 | **Primary Metric.** Evaluates structural preservation. |
| **MS-SSIM** | Similarity | **$\uparrow$ Higher** | 1.0 | **Robustness.** Evaluates structure at multiple scales. |
| **PSNR** | Fidelity | **$\uparrow$ Higher** | High | **Signal Quality.** Ratio of signal power to noise. |
| **VIF** | Info Theory | **$\uparrow$ Higher** | 1.0 | **Information.** Quantifies diagnostic information preservation. |
| **MSE** | Error | **$\downarrow$ Lower** | 0.0 | **Accuracy.** Measures physical accuracy of pixel intensities. |
| **LPIPS** | Perceptual | **$\downarrow$ Lower** | 0.0 | **Realism.** Low LPIPS confirms the scan "looks" real. |

---

**NOTE: For the Liderboard only SSIM, MS-SSIM and LPIPS will be taken into account. Other metrics can be reported only for information due to its failure because of speckles**


## 🤝 Citation & Contact

This dataset is made freely available for research, benchmarking, and challenges. Use of this dataset requires appropriate citation of both this dataset:

> L. A. Matveev, A. A. Sovetsky, K. S. Petrova, M. G. Ryabkov, M. A. Brueva, A. L. Matveyev, V. Y. Zaitsev. "In vivo Human Skin Optical Coherence Tomography (OCT) Dataset for Classification Benchmarking and Digital Phantom Generation" Zenodo (https://doi.org/10.5281/zenodo.18095266)

and the associated paper:

> A. A. Sovetsky, K. S. Petrova, M. A. Brueva, M. G. Ryabkov, A. L. Matveyev, L. A. Matveev, V. Y. Zaitsev. "Automated segmentation and skin-layer thickness estimation by extracting the optical scattering coefficient and speckle contrast parameter from optical coherence tomography scans". Skin Pharmacology and Physiology, 2026 (DOI: 10.1159/000550613).
