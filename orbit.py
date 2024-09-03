import matplotlib.pyplot as plt
import plotly.express as px
from pyspedas.mms.mms_orbit_plot import mms_orbit_plot
from pytplot import get_data
import pytplot
import os
import pyspedas
import logging
from datetime import datetime
import spacepy.pycdf as cdf
import pandas as pd
import plotly.graph_objects as go
import numpy as np


class Orbit2D:
    def __init__(self, date_range=None, local_file=None):
        self.date_range = date_range
        self.local_file = local_file
        self.xsize = 8.0
        self.ysize = 8.0
        self.mms_state_vars = []

        # The pyspedas.mms module contains a nice PNG of the earth that we can add to our orbit plots.
        from pyspedas.mms import __file__ as mmsinitfile
        mms_init_file_path = os.path.realpath(mmsinitfile)
        mms_parent_dir = os.path.dirname(mms_init_file_path)
        self.png_path = os.path.join(mms_parent_dir, 'mec', 'earth_polar1.png')
        self.im = plt.imread(self.png_path)

    def download_data(self):
        if self.date_range is not None:
            logging.info(f"Downloading MMS data for date range: {self.date_range}")
            pyspedas.mms.mec(trange=self.date_range, time_clip=True)
        elif self.local_file is not None:
            logging.info(f"Loading local file: {self.local_file}")
            pytplot.tplot(self.local_file)
        else:
            logging.error("Either date_range or local_file must be provided.")
            return

        # Get the MMS state variables
        self.mms_state_vars = [var for var in pytplot.tplot_names() if 'mms' in var and 'mec' in var]
        for v in self.mms_state_vars:
            pytplot.tkm2re(v, newname=v)

    def plot(self):
        self.download_data()

        # Create plots for XY, XZ, and YZ planes
        xyfig, xyaxis = self.create_plot('GSE X Position, Re', 'GSE Y Position, Re')
        xzfig, xzaxis = self.create_plot('GSE X Position, Re', 'GSE Z Position, Re')
        yzfig, yzaxis = self.create_plot('GSE Y Position, Re', 'GSE Z Position, Re')

        # Plot the orbits
        for var in self.mms_state_vars:
            d = get_data(var)
            if d is not None and len(d.y.shape) == 2:
                xyaxis.plot(d.y[:, 0], d.y[:, 1], color='b')
                xzaxis.plot(d.y[:, 0], d.y[:, 2], color='b')
                yzaxis.plot(d.y[:, 1], d.y[:, 2], color='b')

        # Label the MMS probe
        xyaxis.plot([], [], color='b', label='MMS')

        # Show the legend
        xyaxis.legend(loc='lower right')

        # Show the plots
        plt.show()

    def create_plot(self, xlabel, ylabel):
        fig, axis = plt.subplots(sharey=True, sharex=True, figsize=(self.xsize, self.ysize))
        axis.set_aspect('equal')
        axis.set_xlim([-60, 60])
        axis.set_ylim([-60, 60])
        axis.imshow(self.im, extent=(-1, 1, -1, 1))
        axis.set_xlabel(xlabel)
        axis.set_ylabel(ylabel)
        return fig, axis

    def save_plot(self, directory='plots'):
        if not os.path.exists(directory):
            os.mkdir(directory)

        self.download_data()

        # Create plots for XY, XZ, and YZ planes
        xyfig, xyaxis = self.create_plot('GSE X Position, Re', 'GSE Y Position, Re')
        xzfig, xzaxis = self.create_plot('GSE X Position, Re', 'GSE Z Position, Re')
        yzfig, yzaxis = self.create_plot('GSE Y Position, Re', 'GSE Z Position, Re')

        # Plot the orbits
        for var in self.mms_state_vars:
            d = get_data(var)
            if d is not None and len(d.y.shape) == 2:
                if d.y.shape[1] >= 2:
                    xyaxis.plot(d.y[:, 0], d.y[:, 1], color='b')
                if d.y.shape[1] >= 3:
                    xzaxis.plot(d.y[:, 0], d.y[:, 2], color='b')
                    yzaxis.plot(d.y[:, 1], d.y[:, 2], color='b')

        # Label the MMS probe
        xyaxis.plot([], [], color='b', label='MMS')

        # Get the data values for the high-pressure magnetopause boundary and plot on the XY plane.
        mp_dat = pytplot.get_data('mpause_gse_hi')

        xyaxis.plot(mp_dat.y[:, 0], mp_dat.y[:, 1], color='k', linestyle='solid',
                    label="T96 magnetopause, P_dyn = 14 nPa")

        # Get the data values for the low-pressure magnetopause boundary and plot on the XY plane.
        mp_dat = pytplot.get_data('mpause_gse_low')
        xyaxis.plot(mp_dat.y[:, 0], mp_dat.y[:, 1], color='k', linestyle='dotted',
                    label='T96 magnetopause, P_dyn = 3 nPa')

        # Place the legend at the lower right where it won't cover anything interesting
        xyaxis.legend(loc='lower right')

        today_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        xyfig.savefig(os.path.join(directory, f"orbit_xy_{today_date}.png"))
        xzfig.savefig(os.path.join(directory, f"orbit_xz_{today_date}.png"))
        yzfig.savefig(os.path.join(directory, f"orbit_yz_{today_date}.png"))
        plt.close('all')


class Orbit3D:
    """

    Orbit2DSimple2 class is used for plotting the spacecraft orbital data.

    """
    def __init__(self):
        # Load the CDF file, should format always be mms1_mec_srvy_l2_epht89q_20240608 ?
        cdf_file_path = 'trash/orbit_data/mms1_mec_srvy_l2_epht89q_20240608_v2.2.0.cdf'
        cdf_file = cdf.CDF(cdf_file_path)

        # Extract the relevant data
        epoch = cdf_file['Epoch'][...]
        r_gse = cdf_file['mms1_mec_r_gse'][...]

        # Close the CDF file
        cdf_file.close()

        # Convert the data to a pandas DataFrame
        data_dict = {
            'Epoch': epoch,
            'X_GSE': r_gse[:, 0],
            'Y_GSE': r_gse[:, 1],
            'Z_GSE': r_gse[:, 2]
        }
        df = pd.DataFrame(data_dict)

        # Calculate the radial distance of the probe
        df['Radial_Distance'] = np.sqrt(df['X_GSE'] ** 2 + df['Y_GSE'] ** 2 + df['Z_GSE'] ** 2)

        # Define the magnetopause parameters
        r_0 = 10.8 * 6371  # Scaling magnetopause to Earth's radius in kilometers
        m = 0.1
        beta_0 = -1.03
        beta_1 = -0.07
        beta_2 = -0.02
        beta_3 = 0.09
        c_n = -6
        d_n = -10
        e_n = 1
        c_s = -7
        d_s = -6
        e_s = 1
        theta_n = 0.64
        phi_n = np.pi
        theta_s = 1.25
        phi_s = np.pi

        # Create the theta and phi angles for the spacecraft positions
        theta = np.arccos(df['Z_GSE'] / df['Radial_Distance'])
        phi = np.arctan2(df['Y_GSE'], df['X_GSE'])

        # Calculate psi_n and psi_s for the spacecraft positions
        psi_n = np.arccos(np.cos(theta) * np.cos(theta_n) + np.sin(theta) * np.sin(theta_n) * np.cos(phi - phi_n))
        psi_s = np.arccos(np.cos(theta) * np.cos(theta_s) + np.sin(theta) * np.sin(theta_s) * np.cos(phi - phi_s))

        # Calculate Q for the spacecraft positions
        Q = c_n * np.exp(d_n * psi_n ** e_n) + c_s * np.exp(d_s * psi_s ** e_s)

        # Calculate beta for the spacecraft positions
        beta = beta_0 + beta_1 * np.cos(phi) + beta_2 * np.sin(phi) + beta_3 * (np.sin(phi)) ** 2

        # Ensure beta is within a reasonable range
        beta = np.clip(beta, -2, 2)

        # Calculate the magnetopause boundary for the spacecraft positions
        magnetopause_boundary = r_0 * (np.cos(theta / 2) + m * np.sin(2 * theta) * (1 - np.exp(-theta))) ** beta + Q

        # Identify the first crossing point
        first_crossing_index = np.where(df['Radial_Distance'] < magnetopause_boundary)[0]
        if first_crossing_index.size > 0:
            first_crossing_index = first_crossing_index[0]
            first_crossing_time = df.loc[first_crossing_index, 'Epoch']
            print(f"First magnetopause crossing at: {first_crossing_time}")

        # Create the 3D scatter plot for the MMS orbit data
        scatter_plot = go.Scatter3d(
            x=df['X_GSE'],
            y=df['Y_GSE'],
            z=df['Z_GSE'],
            mode='markers',
            marker=dict(size=2, color=df['Radial_Distance'] < magnetopause_boundary, colorscale='RdYlGn',
                        colorbar=dict(title='Magnetopause Crossing')),
            name='MMS Orbit'
        )

        # Create a 3D mesh for Earth
        # Define a function to create a sphere
        def create_sphere(radius=1, center=(0, 0, 0), resolution=50):
            u = np.linspace(0, 2 * np.pi, resolution)
            v = np.linspace(0, np.pi, resolution)
            x = radius * np.outer(np.cos(u), np.sin(v)) + center[0]
            y = radius * np.outer(np.sin(u), np.sin(v)) + center[1]
            z = radius * np.outer(np.ones(np.size(u)), np.cos(v)) + center[2]
            return x, y, z

        # Create Earth mesh
        earth_radius = 6371  # Approximate radius of Earth in kilometers
        earth_center = (0, 0, 0)
        x, y, z = create_sphere(radius=earth_radius, center=earth_center)

        # Rotate the Earth mesh
        def rotate_y(x, y, z, angle):
            cos_angle = np.cos(angle)
            sin_angle = np.sin(angle)
            x_rot = x * cos_angle + z * sin_angle
            y_rot = y
            z_rot = -x * sin_angle + z * cos_angle
            return x_rot, y_rot, z_rot

        angle = np.pi / 2  # 90 degrees in radians
        x_rot, y_rot, z_rot = rotate_y(x, y, z, angle)

        earth_mesh = go.Surface(
            x=x_rot, y=y_rot, z=z_rot,
            colorscale='Blues',
            opacity=0.6,
            name='Earth'
        )

        # Create the theta and phi angles for the grid
        theta_grid = np.linspace(0, np.pi, 100)
        phi_grid = np.linspace(0, 2 * np.pi, 100)
        theta_grid, phi_grid = np.meshgrid(theta_grid, phi_grid)

        # Calculate psi_n and psi_s for the grid
        psi_n_grid = np.arccos(
            np.cos(theta_grid) * np.cos(theta_n) + np.sin(theta_grid) * np.sin(theta_n) * np.cos(phi_grid - phi_n))
        psi_s_grid = np.arccos(
            np.cos(theta_grid) * np.cos(theta_s) + np.sin(theta_grid) * np.sin(theta_s) * np.cos(phi_grid - phi_s))

        # Calculate Q for the grid
        Q_grid = c_n * np.exp(d_n * psi_n_grid ** e_n) + c_s * np.exp(d_s * psi_s_grid ** e_s)

        # Calculate beta for the grid
        beta_grid = beta_0 + beta_1 * np.cos(phi_grid) + beta_2 * np.sin(phi_grid) + beta_3 * (np.sin(phi_grid)) ** 2

        # Ensure beta is within a reasonable range
        beta_grid = np.clip(beta_grid, -2, 2)

        # Calculate the radial distance r for the grid
        r_grid = r_0 * (np.cos(theta_grid / 2) + m * np.sin(2 * theta_grid) * (
                    1 - np.exp(-theta_grid))) ** beta_grid + Q_grid

        # Normalize r to avoid extremely large or small values
        r_grid = np.clip(r_grid, -50 * earth_radius, 50 * earth_radius)

        x_magnetopause_grid = r_grid * np.sin(theta_grid) * np.cos(phi_grid)
        y_magnetopause_grid = r_grid * np.sin(theta_grid) * np.sin(phi_grid)
        z_magnetopause_grid = r_grid * np.cos(theta_grid)

        # Rotate the magnetopause grid
        x_rot_grid, y_rot_grid, z_rot_grid = rotate_y(x_magnetopause_grid, y_magnetopause_grid, z_magnetopause_grid,
                                                      angle)

        # Create the magnetopause plot with reduced opacity
        magnetopause = go.Surface(x=x_rot_grid, y=y_rot_grid, z=z_rot_grid, colorscale='Viridis', opacity=0.5,
                                  showscale=False)

        # Combine the plots
        fig = go.Figure(data=[scatter_plot, earth_mesh, magnetopause])

        # Set plot title and labels
        fig.update_layout(
            title='MMS Orbit with Earth and Magnetopause (Rotated)',
            scene=dict(
                xaxis_title='X_GSE',
                yaxis_title='Y_GSE',
                zaxis_title='Z_GSE'
            )
        )

        # Show the plot
        fig.show()


class Orbit2DSimple:
    def __init__(self):
        mms_orbit_plot(trange=['2015-10-16', '2015-10-17'],
                       probes=[3, 4],
                       data_rate='srvy',
                       xr=None,
                       yr=None,
                       plane='xz',
                       coord='gse',
                       xsize=5,
                       ysize=5,
                       marker='x',
                       markevery=10,
                       markersize=5,
                       earth=True,
                       dpi=300,
                       save_png='test.png',
                       save_pdf='',
                       save_eps='',
                       save_jpeg='',
                       save_svg='',
                       return_plot_objects=False,
                       display=True
                       )


