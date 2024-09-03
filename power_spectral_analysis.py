from scipy import signal
import matplotlib.pyplot as plt
from kinetics import CDFDataProcessor, KineticCheckGradient
import numpy as np


class PowerSpectralDensity(CDFDataProcessor):

    """
    Computes the power spectral density
    """

    def __init__(self):
        cdf_file = 'data/mms1_fgm_srvy_l2_20240222_v5.440.0.cdf'

        super().__init__()
        # self.data_frame = data_frame
        self.cdf_file = cdf_file
        self.data_frame = self.load_cdf_to_dataframe()

        cdf_file = 'data/mms1_fgm_srvy_l2_20240222_v5.440.0.cdf'
        data_processor = CDFDataProcessor(cdf_file)
        self.data_frame = data_processor.get_data_frame()

    def load_cdf_to_dataframe(self):
        fs = 10e3

        f, pxx_den = signal.periodogram(self.data_frame['Bt        '], fs)
        plt.semilogy(f, pxx_den)
        plt.xlabel('frequency [Hz]')
        plt.ylabel('PSD')

        return self.data_frame, plt.savefig('power_spectral_density.png')

    def compute_psd(self):
        fs = 10.0e5  # Sampling frequency
        f, Pxx_den = signal.periodogram(self.data_frame['Bt        '], fs)

        # Calculate the slope
        log_f = np.log(f[1:])  # Exclude the first point to avoid log(0)
        log_Pxx_den = np.log(Pxx_den[1:])
        slope, intercept = np.polyfit(log_f, log_Pxx_den, 1)

        # Plot the PSD
        plt.semilogy(f, Pxx_den, label='PSD')

        # Plot the slope line
        fit_line = np.exp(intercept) * f ** slope
        plt.semilogy(f, fit_line, linestyle='--', label=f'Slope = {slope:.2f}')

