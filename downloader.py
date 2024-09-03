import logging
from PyQt6.QtCore import QThread, pyqtSignal, QObject
import pyspedas
import pytplot
from pytplot import tplot
import os

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class DownloadWorker(QObject):
    finished = pyqtSignal(list)

    def __init__(self, date_init, date_end, parent=None):
        super().__init__(parent)
        self.date_init = date_init
        self.date_end = date_end

    def run(self):
        try:
            logging.info(f"Starting download from {self.date_init} to {self.date_end}")
            trange = [self.date_init, self.date_end]

            # Example download calls
            fgm_vars = pyspedas.themis.fgm(probe='a', trange=trange)
            logging.debug(f"FGM Vars: {fgm_vars}")
            esa_vars = pyspedas.themis.esa(probe='a', trange=trange)
            logging.debug(f"ESA Vars: {esa_vars}")
            erg_orb_vars = pyspedas.erg.orb(trange=trange)
            pyspedas.omni.data(trange=trange)
            gmag_vars = pyspedas.themis.gmag(sites=['fsmi', 'fykn', 'atha'], trange=trange)

            variables_to_plot = ['tha_fgs_gse'] + ['tha_peef_en_eflux', 'tha_peef_velocity_dsl', 'tha_peif_en_eflux', 'tha_peif_velocity_dsl'] + \
                                ['erg_orb_l2_pos_gse'] + ['proton_density', 'flow_speed', 'Pressure'] + gmag_vars + ['thg_mag_fsmi_subtract_median']

            self.finished.emit(variables_to_plot)
            logging.info("Download completed successfully.")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

class DownloadThread(QThread):
    finished = pyqtSignal(list)

    def __init__(self, date_init, date_end, parent=None):
        super().__init__(parent)
        self.date_init = date_init
        self.date_end = date_end

    def run(self):
        worker = DownloadWorker(self.date_init, self.date_end)
        worker.finished.connect(self.finished)
        worker.run()

class LocalDataWorker(QObject):
    finished = pyqtSignal(list)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        try:
            logging.info(f"Loading local data from {self.file_path}")
            file_extension = os.path.splitext(self.file_path)[1]
            if file_extension in ['.cdf', '.nc', '.h5', '.csv', '.txt']:
                pytplot.cdf_to_tplot(self.file_path)
                variables_to_plot = pytplot.tplot_names()
                self.finished.emit(variables_to_plot)
                logging.info("Local data processing completed successfully.")
            else:
                logging.error(f"Unsupported file format: {file_extension}")
        except Exception as e:
            logging.error(f"An error occurred: {e}")

class LocalDataThread(QThread):
    finished = pyqtSignal(list)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        worker = LocalDataWorker(self.file_path)
        worker.finished.connect(self.finished)
        worker.run()