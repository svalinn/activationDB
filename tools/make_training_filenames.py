import query_sqlite_db as qsd
import numpy as np


'''
For the training set, where each simulation runs a single pulse with no dwell times, variation is introduced with
the maximum flux magnitude, minimum irradiation time, and scaling factors of flux magnitude and irradiation time.
This is repeated for a series of flux spectra.
'''

def make_filename_strings(training_inp_info, sqlite_conn, min_on_times, time_unit):
    """
    :param: training_inp_info (3D numpy array where each dimension corresponds to
    relative fluence factors (float), flux normalization factors (float), and paths to flux files (str), respectively)
    Each entry of training_inp_info is a 3-tuple of (relative fluence factor, flux normalization factor, flux file)
    :param: sqlite_conn (SQLite connection object to database containing flux table)
    :param: min_on_times (iterable of minimum steady-state operational times used to define the total fluence)
    :param: time_unit (unit (str) of min_on_times)
    """
    filenames = np.empty((len(min_on_times),) + training_inp_info.shape, dtype=object)
    for (min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx), _ in np.ndenumerate(filenames):
        entry = training_inp_info[rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx]
        if entry is None:
            filenames[min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx] = None
        else:
            rel_on_time_factor, flux_norm_factor, flux_file = entry
            flux_id = qsd.find_flux_spec_shape_id(sqlite_conn, "flux_file", flux_file)
            filename = f"{flux_id}_{flux_norm_factor}_{min_on_times[min_on_time_idx]}{time_unit}_{rel_on_time_factor}"
            filenames[min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx] = filename
    return filenames

