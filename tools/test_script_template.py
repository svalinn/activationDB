import argparse
import yaml
import numpy as np
import alara_output_processing as aop
import pandas as pd
import script_template as script_temp

'''
Runs and tests the methods in script_template.py using a series of run dictionaries
with various pulse numbers and duty cycles.
'''


def write_to_adf(run_dicts):
    adf_data = []
    for run_dict in run_dicts:
        lib = aop.DataLibrary()
        adf = lib.make_entries(run_dicts[run_dict])
        adf_data.append(adf)
        adf = pd.concat(adf_data)
    return adf


def test_modify_adf_columns(adf):
    '''
    Ensure that the expected columns exist in the adf.
    '''
    assert not any(col in adf for col in [
        "value",
        "time",
        "time_unit",
        "variable",
        "var_unit",
        "block",
        "block_num",
    ])
    assert (any(col in adf
                for col in ["num_dens_(atoms/cm3)", "half_life", "block_name"]))


def adf_map_flux_tirr(adf, norm_flux_arr, t_irr_arr, num_pulses, duty_cycles):
    '''
    Maps each of the number of pulses and duty cycle values from the run label to an iterator,
    from which the corresponding value of the irradiation time is identified. The irradiation
    time is added to a new column in the adf.
    '''
    pulse_num_dc = adf["run_lbl"].str.extract(r"_(\d+)p_(\d+)_").astype(int)
    # Map num_pulses and duty_cycles to an index
    pulse_idx = pulse_num_dc[0].map(
        {pulse_num: i
         for i, pulse_num in enumerate(num_pulses)})
    duty_cycle_idx = (pulse_num_dc[1] / 100).map(
        {duty_cycle: i
         for i, duty_cycle in enumerate(duty_cycles)})
    t_irr_arr_mod = t_irr_arr.T[pulse_idx.to_numpy(),
                                duty_cycle_idx.to_numpy()]
    script_temp.map_adf_flux_tirr(adf, norm_flux_arr, t_irr_arr_mod)
    adf["t_irr"] = aop.convert_times(adf["t_irr"], from_unit="y", to_unit="s")
    return adf


def test_adf_map_flux_tirr(adf):
    '''
    Ensure that two of the run labels are associated with the correct irradiation time.
    '''
    assert not ((adf["run_lbl"] == "iter_dt_2p_100_4y")
                & (adf["t_irr"] != 4 * 365 * 24 * 60 * 60)).any()
    assert not ((adf["run_lbl"] == "iter_dt_64p_25_4y")
                & (adf["t_irr"] != 15.8125 * 365 * 24 * 60 * 60)).any()


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--db_yaml",
        default="iter_dt_out.yaml",
        help="Path (str) to YAML containing inputs",
    )
    args = parser.parse_args()
    return args


def read_yaml(yaml_arg):
    """
    input:
        yaml_arg : output of parse_args() corresponding to args.db_yaml
    """
    with open(yaml_arg, "r") as yaml_file:
        inputs = yaml.safe_load(yaml_file)
    return inputs


def main():
    args = parse_args()
    inputs = read_yaml(args.db_yaml)

    num_energy_bins = inputs["num_energy_bins"]

    flux_file = inputs["flux_file"]
    all_flux_entries = script_temp.open_flux_file(flux_file)

    flux_array = script_temp.parse_flux_str(all_flux_entries, num_energy_bins)
    total_flux = np.sum(flux_array,
                        axis=1)  # sum over the bin widths of flux array
    # normalize flux spectrum by the total flux in each interval
    norm_flux_arr = flux_array / total_flux.reshape(
        len(total_flux), 1)  # 2D array of shape num_intervals x num_groups

    active_burn_time = np.asarray(inputs["active_burn_time"])
    duty_cycle_list = np.asarray(inputs["duty_cycles"])
    num_pulses = np.asarray(inputs["num_pulses"])
    t_irr_arr = script_temp.calc_time_params(active_burn_time, duty_cycle_list,
                                             num_pulses)

    run_dicts = inputs["run_dicts"]
    adf = write_to_adf(run_dicts)

    num_pulses = inputs["num_pulses"]
    duty_cycles = inputs["duty_cycles"]
    adf = script_temp.modify_adf_columns(adf)

    test_modify_adf_columns(adf)

    adf = adf_map_flux_tirr(adf, norm_flux_arr, t_irr_arr, num_pulses,
                            duty_cycles)
    test_adf_map_flux_tirr(adf)

    script_temp.write_to_sqlite(adf)


if __name__ == "__main__":
    main()
