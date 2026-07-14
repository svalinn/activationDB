import numpy as np
import query_sqlite_db as qsd

def make_single_level_ph_filename_strings(max_fluence_factors, sqlite_conn, nums_pulses, dwell_times, min_on_times, on_time_unit, dwell_time_unit, trunc_tol):
    """
    Creates filenames for pulse histories with a single level.
    :param: max_fluence_factors (3D numpy array where each dimension corresponds to
    relative fluence factors (float), flux normalization factors (float), and paths to flux files (str), respectively)
    Each entry of max_fluence_factors is a 3-tuple of (relative fluence factor, flux normalization factor, flux file)
    :param: sqlite_conn (SQLite connection object to database containing flux table)
    :param: nums_pulses (iterable of number of pulses in each single-level pulse history)
    :param: dwell_times (iterable of dwell times between subsequent pulses, where each dwell time is for each single-level pulse history)
    :param: min_on_times (iterable of minimum steady-state operational times used to define the total fluence)
    :param: on_time_unit (unit (str) of min_on_times)
    :param: dwell_time_unit (unit (str) of dwell_times)
    :param: trunc_tol (truncation tolerance (float) used to build input files)
    """
    filenames = np.empty((len(min_on_times), len(nums_pulses), len(dwell_times)) + max_fluence_factors.shape, dtype=object)
    for (num_pulse_idx, dwell_time_idx, min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx), _ in np.ndenumerate(filenames):
        entry = max_fluence_factors[rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx]
        if entry is None:
            filenames[num_pulse_idx, dwell_time_idx, min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx] = None
        else:
            rel_on_time_factor, flux_norm_factor, flux_file = entry
            flux_id = qsd.find_flux_spec_shape_id(sqlite_conn, "flux_file", flux_file)
            filename = f"{nums_pulses[num_pulse_idx]}_{dwell_times[dwell_time_idx]}{dwell_time_unit}_{flux_id}_{flux_norm_factor}_{min_on_times[min_on_time_idx]}{on_time_unit}_{rel_on_time_factor}_{trunc_tol:.3e}"
            filenames[num_pulse_idx, dwell_time_idx, min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx] = filename
    return filenames