import numpy as np
import argparse
import yaml
import sqlite3
import make_training_filenames as mtf
import query_sqlite_db as qsd
import training_inp_params_to_dict as tiptd
import build_inp_blocks as bib


def make_all_dicts(training_inp_info, min_on_times, time_unit):
    all_training_dicts = np.empty((len(min_on_times),) + training_inp_info.shape, dtype=object)
    for (min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx) in np.ndindex(all_training_dicts.shape):
        if training_inp_info[rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx] is None:
            all_training_dicts[min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx] = None
        else:
            training_dict = tiptd.write_training_params_dict(training_inp_info, min_on_times[min_on_time_idx], time_unit)
            all_training_dicts[min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx] = training_dict
    return all_training_dicts

def make_all_input_files(all_training_dicts, nuclib, volume, trunc_tolerance, inp_file_folder, filenames):
    for training_dict_idx in np.ndindex(all_training_dicts.shape):
        child_dict = all_training_dicts[training_dict_idx]
        ph_dict = bib.make_ph_dict([child_dict])
        flux_dict = bib.make_flux_dict([child_dict])
        flux_lines = bib.make_flux_block(flux_dict)
        all_ph_lines = bib.make_pulse_history_block(ph_dict)
        all_sched_lines = bib.make_schedule_block([child_dict], ph_dict, flux_dict)
        nuclib_lines = bib.read_nuclib(nuclib)
        vol_lines, load_lines, mix_lines = bib.make_volume_block(nuclib_lines, volume)
        assembled_lines = bib.make_input_lines(vol_lines, load_lines, mix_lines, flux_lines, all_ph_lines, all_sched_lines, trunc_tolerance)
        with open(inp_file_folder+filenames[training_dict_idx], 'w') as new_inp:
            new_inp.write(assembled_lines)    

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--training_case_yaml', default = "make_training_cases.yaml", help="Path (str) to YAML containing inputs to construct training data")
    args = parser.parse_args()
    return args

def read_yaml(yaml_arg):
    '''
    input:
        yaml_arg : output of parse_args() corresponding to args.training_case_yaml
    '''
    with open(yaml_arg, 'r') as yaml_file:
        inputs = yaml.safe_load(yaml_file)
    return inputs


def main():
    args = parse_args()
    inputs = read_yaml(args.training_case_yaml)

    rel_on_time_factors = inputs['rel_on_time_factors']
    flux_norm_factors = inputs['flux_norm_factors']
    flux_files = inputs['flux_files']
    min_on_times = inputs['min_on_times']
    time_unit = inputs['min_on_time_unit']
    sqlite_conn_db_name = inputs['sqlite_db_name']
    nuclib = inputs['nuclib_path']
    volume = inputs['volume']
    trunc_tolerance = inputs['trunc_tolerance']
    inp_file_folder = inputs['inp_file_folder']

    sqlite_conn = sqlite3.connect(sqlite_conn_db_name) 
    training_inp_info = tiptd.make_flux_tirr_combos(rel_on_time_factors, flux_norm_factors, flux_files)

    filenames = mtf.make_filename_strings(training_inp_info, sqlite_conn, min_on_times, time_unit)
    all_training_dicts = make_all_dicts(training_inp_info, min_on_times, time_unit)

    make_all_input_files(all_training_dicts, nuclib, volume, trunc_tolerance, inp_file_folder, filenames)

if __name__ == "__main__":
    main()    

