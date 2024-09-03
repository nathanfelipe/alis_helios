import logging
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QProgressBar, QDialog, QComboBox, QCheckBox, QFileDialog
from downloader import DownloadThread, LocalDataThread
import pytplot
from orbit import Orbit2D, Orbit3D
import os
from datetime import datetime
import webbrowser
from kinetics import CDFDataProcessor, KineticCheckGradient
from power_spectral_density import PowerSpectralDensity

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class WelcomeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome")
        self.setFixedSize(675, 475)

        layout = QVBoxLayout()


        self.image_label = QLabel()
        pixmap = QPixmap("logos/logo.jpeg")  # Provide the correct path to your image
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.image_label)

        self.label = QLabel("Welcome to Alis Helios, a tool for spacecraft data access & advanced time series analysis")
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Close the dialog after 5l seconds
        QTimer.singleShot(1000, self.accept)


class MissionSelectionDialog(QDialog):
    mission_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Mission")
        self.setFixedSize(300, 100)

        layout = QVBoxLayout()

        self.label = QLabel("Select the mission you want to analyze:")
        layout.addWidget(self.label)

        self.mission_dropdown = QComboBox()
        self.mission_dropdown.addItems(["THEMIS", "MMS"])
        layout.addWidget(self.mission_dropdown)

        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.select_mission)
        layout.addWidget(self.select_button)

        self.setLayout(layout)

    def select_mission(self):
        selected_mission = self.mission_dropdown.currentText()
        self.mission_selected.emit(selected_mission)
        self.accept()


class KineticTestingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kinetic Testing")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Select the Property to test the Kinetic ordering")
        layout.addWidget(self.label)

        self.dropdown = QComboBox()
        self.dropdown.addItems(["beta", "grad B", "delta B", "grad n_{i,e}", "PSD"])
        layout.addWidget(self.dropdown)

        self.calculate_button = QPushButton("Perform Calculation")
        self.calculate_button.clicked.connect(self.perform_calculation)
        layout.addWidget(self.calculate_button)

        self.setLayout(layout)

    def perform_calculation(self):
        selected_option = self.dropdown.currentText()

        option_to_column = {
            "beta": "beta_column_name",
            "grad B": "Bt        ",
            "delta B": "delta_B_column_name",
            "grad n_{i,e}": "grad_n_ie_column_name",
            "PSD": "power_spectral_density_column_name"
        }

        column_name = option_to_column.get(selected_option)

        if not column_name:
            self.result_label = QLabel(f"Error: Column for {selected_option} not found")
            self.layout().addWidget(self.result_label)
            return

        if selected_option == "grad B":
        # Load the data (assuming you have the file path and it's accessible)
            cdf_file = 'data/mms1_fgm_srvy_l2_20240222_v5.440.0.cdf'  # Update with the actual file path
            data_processor = CDFDataProcessor(cdf_file)
            data_frame = data_processor.get_data_frame()

        # Perform the kinetic calculation
            kinetic_check = KineticCheckGradient(data_frame)
            kinetic_check.compute_gradients()

        # Debug: print the gradient_df columns
            print("Gradient DataFrame columns before plotting:", kinetic_check.gradient_df.columns)

        # Plot the result for the selected component
            kinetic_check.plot_gradient(column_name)

        elif selected_option == "PSD":

            # Load the data (assuming you have the file path and it's accessible)
            cdf_file = 'data/mms1_fgm_srvy_l2_20240222_v5.440.0.cdf'  # Update with the actual file path
            data_processor = CDFDataProcessor(cdf_file)
            data_frame = data_processor.get_data_frame()

            # Perform the kinetic calculation
            psd = PowerSpectralDensity(data_frame)
            psd.load_cdf_to_dataframe()

            # Debug: print the gradient_df columns
            print("Power Spectra Density plotted:")  # , kinetic_check.gradient_df.columns)

        # Display the result in the GUI
        self.result_label = QLabel(f"Result: Gradient of {selected_option} calculated")
        self.layout().addWidget(self.result_label)

        # Optionally, show the plot in the PyQt window
        self.display_plot_in_window(f"{selected_option}.png")

    def display_plot_in_window(self, plot_path):
        plot_label = QLabel()
        pixmap = QPixmap(plot_path)
        plot_label.setPixmap(pixmap)
        plot_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout().addWidget(plot_label)


class LoadingDialog(QDialog):
    def __init__(self, date_init=None, date_end=None, parent=None, is_local=False):
        super().__init__(parent)
        self.setWindowTitle("Loading")
        self.setFixedSize(450, 100)

        layout = QVBoxLayout()
        if is_local:
            self.label = QLabel(f"Loading local data from {date_init}")
        else:
            self.label = QLabel(f"Downloading MMS time series from {date_init} to {date_end}")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress bar

        layout.addWidget(self.label)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)


class PlotSelectionDialog(QDialog):
    def __init__(self, variables_to_plot, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window
        self.setWindowTitle("Select Plot Action")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout()

        self.label = QLabel("Select a plot to save or display:")
        layout.addWidget(self.label)

        self.plot_dropdown = QComboBox()
        self.plot_dropdown.addItems(variables_to_plot)
        layout.addWidget(self.plot_dropdown)

        self.save_button = QPushButton("Save Plot")
        self.save_button.clicked.connect(lambda: self.save_or_display_plot(save=True))
        layout.addWidget(self.save_button)

        self.display_button = QPushButton("Display Plot")
        self.display_button.clicked.connect(lambda: self.save_or_display_plot(save=False))
        layout.addWidget(self.display_button)

        self.setLayout(layout)

    def save_or_display_plot(self, save):
        selected_plot = self.plot_dropdown.currentText()
        if selected_plot in pytplot.tplot_names():
            if save:
                # Check if 'plots' directory exists
                if not os.path.exists("plots"):
                    os.mkdir("plots")

                # Create a new directory with the current date
                today_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                new_dir = os.path.join("plots", f"plot_created_on_{today_date}")
                os.mkdir(new_dir)

                plot_path = os.path.join(new_dir, f"{selected_plot}.png")
                pytplot.tplot(selected_plot, save_png=plot_path)
                logging.info(f"Plot saved as {plot_path}")
            else:
                self.main_window.display_plot(selected_plot)
        else:
            logging.warning(f"Variable {selected_plot} not found in pytplot")
        self.accept()


class OrbitPlotSelectionDialog(QDialog):
    plot_type_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Orbit Plot Type")
        self.setFixedSize(300, 100)

        layout = QVBoxLayout()

        self.label = QLabel("Select the type of orbit plot:")
        layout.addWidget(self.label)

        self.plot_type_dropdown = QComboBox()
        self.plot_type_dropdown.addItems(["2D (live magnetopause)", "3D (modelled magnetopause)"])
        layout.addWidget(self.plot_type_dropdown)

        self.select_button = QPushButton("Select")
        self.select_button.clicked.connect(self.select_plot_type)
        layout.addWidget(self.select_button)

        self.setLayout(layout)

    def select_plot_type(self):
        selected_type = self.plot_type_dropdown.currentText()
        self.plot_type_selected.emit(selected_type)
        self.accept()


class MainWindow(QMainWindow):
    def __init__(self, selected_mission):
        super().__init__()

        self.selected_mission = selected_mission  # Store the selected mission
        self.setWindowTitle(f"{selected_mission} Time Series Downloader")
        self.setFixedSize(400, 300)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.layout = QVBoxLayout()  # take out self from all layouts in the class ?

        self.date_init_label = QLabel("Start Date (YYYY-MM-DD):")
        self.date_init_input = QLineEdit()
        self.layout.addWidget(self.date_init_label)
        self.layout.addWidget(self.date_init_input)

        self.date_end_label = QLabel("End Date (YYYY-MM-DD):")
        self.date_end_input = QLineEdit()
        self.layout.addWidget(self.date_end_label)
        self.layout.addWidget(self.date_end_input)

        self.use_existing_data_checkbox = QCheckBox("Use existing data")
        self.layout.addWidget(self.use_existing_data_checkbox)

        self.select_file_button = QPushButton("Select File")
        self.select_file_button.clicked.connect(self.select_file)
        self.layout.addWidget(self.select_file_button)

        self.download_button = QPushButton(f"Download {selected_mission} Time Series")
        self.download_button.clicked.connect(self.download_time_series)
        self.layout.addWidget(self.download_button)

        self.plot_orbit_button = QPushButton("Plot Orbit (MMS Only)")
        self.plot_orbit_button.clicked.connect(self.plot_orbit)
        self.layout.addWidget(self.plot_orbit_button)

        self.info_label = QLabel("Further Information:")
        self.layout.addWidget(self.info_label)

        self.info_dropdown = QComboBox()
        self.info_dropdown.addItems(["pySPEDAS", "pytplot", "THEMIS", "MMS"])
        self.info_dropdown.currentIndexChanged.connect(self.open_info_url)
        self.layout.addWidget(self.info_dropdown)

        self.kinetic_testing_button = QPushButton("Kinetic Testing")
        self.kinetic_testing_button.clicked.connect(self.open_kinetic_testing_dialog)
        self.layout.addWidget(self.kinetic_testing_button)

        central_widget.setLayout(self.layout)

    def open_kinetic_testing_dialog(self):
        self.kinetic_testing_dialog = KineticTestingDialog(self)
        self.kinetic_testing_dialog.exec()

    def open_info_url(self):
        selected_info = self.info_dropdown.currentText()
        urls = {
            "pySPEDAS": "https://pyspedas.readthedocs.io/en/latest/index.html",
            "pytplot": "https://pytplot.readthedocs.io/en/latest/index.html",
            "THEMIS": "https://themis.igpp.ucla.edu/overview.shtml",
            "MMS": "https://lasp.colorado.edu/mms/sdc/public/"
        }
        url = urls.get(selected_info)
        if url:
            webbrowser.open(url)

    def select_file(self):
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFile)
        file_dialog.setNameFilter("Data files (*.cdf *.nc *.h5 *.csv *.txt)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                self.selected_file = selected_files[0]
                self.use_existing_data_checkbox.setChecked(True)
                logging.info(f"Selected file: {self.selected_file}")
                self.load_existing_data()

    def download_time_series(self):
        if self.use_existing_data_checkbox.isChecked():
            self.load_existing_data()
        else:
            date_init = self.date_init_input.text()
            date_end = self.date_end_input.text()
            if not date_init or not date_end:
                logging.error("Both dates must be provided.")
                return  # Add proper error handling here

            self.loading_dialog = LoadingDialog(date_init, date_end, self)
            self.loading_dialog.show()

            logging.info("Starting download thread.")
            # Start the download thread with the date parameters
            self.download_thread = DownloadThread(self.selected_mission, date_init, date_end)
            self.download_thread.finished.connect(self.on_download_finished)
            self.download_thread.start()

    def load_existing_data(self):
        logging.info("Using existing data.")
        if hasattr(self, 'selected_file'):
            self.loading_dialog = LoadingDialog(date_init=self.selected_file, is_local=True, parent=self)
            self.loading_dialog.show()

            logging.info("Starting local data thread.")
            self.local_data_thread = LocalDataThread(self.selected_file)
            self.local_data_thread.finished.connect(self.on_download_finished)
            self.local_data_thread.start()
        else:
            logging.error("No file selected for analysis.")

    def on_download_finished(self, variables_to_plot):
        logging.info("Data loading finished, closing loading dialog.")
        if hasattr(self, 'loading_dialog'):
            self.loading_dialog.close()

        if not variables_to_plot:
            logging.error("No data downloaded. Please check your date range and try again.")
            self.download_button.setText("Download Failed")
            self.download_button.setEnabled(True)
            return

        self.plot_selection_dialog = PlotSelectionDialog(variables_to_plot, self, self)
        self.plot_selection_dialog.exec()

        # Update UI to indicate process completion
        self.download_button.setText("Process Complete")
        self.download_button.setEnabled(False)

    def display_plot(self, plot_name):
        pytplot.tplot(plot_name)
        logging.info(f"Plot displayed: {plot_name}")
        self.plot_selection_dialog = PlotSelectionDialog(pytplot.tplot_names(), self, self)
        self.plot_selection_dialog.exec()

    def plot_orbit(self):
        if self.selected_mission == "MMS":
            date_init = self.date_init_input.text()
            date_end = self.date_end_input.text()

            dialog = OrbitPlotSelectionDialog(self)
            dialog.plot_type_selected.connect(
                lambda plot_type: self.handle_plot_type_selection(plot_type, date_init, date_end))
            dialog.exec()
        else:
            logging.warning("Orbit plotting is only available for MMS mission.")

    def handle_plot_type_selection(self, plot_type, date_init, date_end):
        if plot_type == "2D (live magnetopause)":
            self.plot_2d_orbit(date_init, date_end)
        elif plot_type == "3D (modelled magnetopause)":
            self.plot_3d_orbit(date_init, date_end)

    def plot_2d_orbit(self, date_init, date_end):
        if self.use_existing_data_checkbox.isChecked() and hasattr(self, 'selected_file'):
            logging.info("Plotting 2D orbit using local file.")
            orbit_plotter = Orbit2D(local_file=self.selected_file)
        elif date_init and date_end:
            logging.info("Plotting 2D orbit using date range.")
            orbit_plotter = Orbit2D(date_range=[date_init, date_end])
        else:
            logging.error("Either select a date range or check the 'Use existing data' option with a file selected.")
            return

        orbit_plotter.save_plot()
        logging.info("2D Orbit plot saved successfully.")

    def plot_3d_orbit(self, date_init, date_end):
        if self.use_existing_data_checkbox.isChecked() and hasattr(self, 'selected_file'):
            logging.info("Plotting 3D orbit using local file.")
            orbit_plotter = Orbit3D()  # (local_file=self.selected_file)
        elif date_init and date_end:
            logging.info("Plotting 3D orbit using date range.")
            orbit_plotter = Orbit3D()  # Orbit3D(date_range=[date_init, date_end])
        else:
            logging.error("Either select a date range or check the 'Use existing data' option with a file selected.")
            return

        # orbit_plotter.save_plot()
        # logging.info("3D Orbit plot saved successfully.")
        # Connect the "Plot Orbit" button to the new plot_orbit method
        self.plot_orbit_button.clicked.connect(self.plot_orbit)

