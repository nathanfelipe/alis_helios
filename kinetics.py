import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import spacepy.datamodel


class CDFDataProcessor:
    def __init__(self, cdf_file):
        self.cdf_file = cdf_file
        self.data_frame = self.load_cdf_to_dataframe()

    def load_cdf_to_dataframe(self):
        """Load the CDF file into a DataFrame."""
        mms_dm_cdf = spacepy.datamodel.fromCDF(self.cdf_file)
        mms_df = mms_dm_cdf.toDataFrame('mms1_fgm_b_bcs_srvy_l2')
        mms_df.index = pd.to_datetime(mms_df.index)

        return mms_df

    def get_data_frame(self):
        """Return the loaded DataFrame."""
        return self.data_frame


class KineticCheckGradient:
    def __init__(self, data_frame):
        self.data_frame = data_frame
        self.gradient_df = pd.DataFrame()
        # self.mms_df = CDFDataProcessor.mms_df

    def filter_valid_time_intervals(self, time_numeric):
        """Identify and remove zero differences in time_numeric."""
        valid_time_intervals = np.diff(time_numeric) != 0
        valid_time_indices = np.where(valid_time_intervals)[0]

        if len(valid_time_indices) > 0:
            valid_time_indices = np.append(valid_time_indices, valid_time_indices[-1] + 1)
            return valid_time_indices
        else:
            print("No valid time intervals")
            return []

    def compute_gradients(self):
        """Compute the gradients for each magnetic field component."""
        time_numeric = self.data_frame.index.astype(np.int64)  # // 10**9
        valid_time_indices = self.filter_valid_time_intervals(time_numeric)

        if valid_time_indices.size > 0:
            time_numeric_filtered = time_numeric[valid_time_indices]

            for column in self.data_frame.columns:
                data_filtered = self.data_frame[column].iloc[valid_time_indices].astype(float)
                gradient = np.gradient(data_filtered, time_numeric_filtered)
                self.gradient_df[column] = pd.Series(gradient, index=self.data_frame.index[valid_time_indices])
        else:
            self.gradient_df = pd.DataFrame(np.nan, index=self.data_frame.index, columns=self.data_frame.columns)

    def plot_gradient(self, component):
        """Plot the gradients of the specified magnetic field component."""
        plt.figure(figsize=(10, 6))
        if component in self.gradient_df.columns:
            plt.plot(self.data_frame.index, self.gradient_df[component], label=f'{component} Gradient', color='tab:red')
            plt.xlabel('Time')
            plt.ylabel(f'{component} Gradient (nT/s)')
            plt.title(f'{component} Gradient')
            plt.legend()
            plt.grid(True)
            plt.savefig("kinetic_test.png")
        else:
            print(f"Component {component} not found in gradient DataFrame")

    def plot_all_gradients(self):
        """Plot the gradients for all magnetic field components."""
        for component in self.data_frame.columns:
            self.plot_gradient(component)

    def get_gradient_df(self):
        """Return the gradient DataFrame."""
        return self.gradient_df