import numpy as np
import configparser
import os

class ExperimentConfig:
    def __init__(self):
        # Zenodo dataset parameters
        self.N_depth = 256
        self.N_lateral = 512
        self.pixel_size_z = 6.0
        self.pixel_size_x = 6.0
        self.wavelength = 1.3
        self.beam_diameter = 20.0
        self.beam_radius = self.beam_diameter / 2.0 
        
        self.z_max = self.N_depth * self.pixel_size_z
        self.x_max = self.N_lateral * self.pixel_size_x
        
        self.b_scans_count = 1
        self.scatterers_count = 300000 
        
        self.config_filename = 'Configuration.ini'
        self.scatterers_filename = 'Scatterers_Exp.txt'
        self.output_filename = 'Scan_Raw.bin'

    def write_ini(self):
        config = configparser.ConfigParser()
        config['Parameters'] = {
            'Scan Filename': self.output_filename,
            'Scatterers coordinates File': self.scatterers_filename,
            'A-scan pixel numbers': str(self.N_depth),
            'Vertical pixel size mcm': str(self.pixel_size_z),
            'Central wavelength mcm': str(self.wavelength),
            'Number of A-scans in B-scan': str(self.N_lateral),
            'Xmax mcm': str(self.x_max),
            'Number of B-scans': str(self.b_scans_count),
            'Ymax mcm': '0.0', 
            'Beam Radius mcm': str(self.beam_radius),
            'Number of scatterers in B-scan': str(self.scatterers_count)
            # TransparencyCoeff removed
        }
        
        with open(self.config_filename, 'w') as f:
            config.write(f)
        print(f"[Config] {self.config_filename} generated.")

class ScattererGenerator:
    def __init__(self, config):
        self.cfg = config
        
    def generate_uniform(self, seed=None, amp=1.0):
        """
        amp: Backscattering Energy in Percent (0..100).
             1.0 means 1% of energy is reflected back.
        """
        if seed is not None:
            np.random.seed(seed)
            
        count = self.cfg.scatterers_count
        xs = (np.random.rand(count) - 0.5) * self.cfg.x_max
        ys = (np.random.rand(count) - 0.5) * (2 * self.cfg.beam_radius)
        zs = np.random.rand(count) * self.cfg.z_max
        amps = np.ones(count) * amp
        
        return np.column_stack((xs, ys, zs, amps))

    def generate_two_layers(self, seed=None, boundary_z_mcm=500.0, amp_top=1.0, amp_bottom=5.0):
        """
        amp_top, amp_bottom: Backscattering Energy in Percent (0..100).
        """
        if seed is not None:
            np.random.seed(seed)
            
        data = self.generate_uniform(seed, amp=amp_top)
        zs = data[:, 2]
        
        mask_bottom = zs > boundary_z_mcm
        data[mask_bottom, 3] = amp_bottom
        
        return data

    def save_to_file(self, data, filename):
        np.savetxt(filename, data, fmt='%.4e')
