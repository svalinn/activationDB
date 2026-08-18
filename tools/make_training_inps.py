import numpy as np
import argparse
import yaml
import sqlite3
import make_training_filenames as mtf
import training_inp_params_to_dict as tiptd
import build_inp_blocks as bib


def make_all_input_files(training_child_dicts, flux_path_modifier, nuclib, volume, trunc_tolerance, inp_file_folder, filenames):
    '''
    :param: training_child_dicts (numpy array of dictionaries, with shape len(rel_on_time_factors) x len(flux_norm_factors) x len(flux_files)
            Each dictionary has the form below:
            {'type': 'pulse_entry',
                'pulse_length': (float),
                'pulse_length_unit': (str),
                'flux_filepath' : (str),
                'flux_norm' : (float),
                'pulse_history': (iterable of (int, float, str)),
                'delay_dur' : (float),
                'delay_dur_unit': (str)
            }
            )
    :param: flux_path_modifier (str, used to modify the end of the flux path)
            (This is motivated by the flux table in the SQLite DB containing the flux spectrum of the group structure,
            but the flux file used to run ALARA requires the flux spectrum to be repeated for each interval in the material loading.)
    :param: nuclib (str, path to ALARA nuclib used to build material loading lines)
    :param: volume (float, the volume of each ALARA interval)
    :param: trunc_tolerance (float, the relative density of a nuclide at which its decay chains are truncated)              
    :param: inp_file_folder (str, path to folder where the input files are written to)
    :param: filenames (numpy array with the same shape and physical dimensions as training_child_dicts)
    '''
    for training_dict_idx in np.ndindex(training_child_dicts.shape):
        if training_child_dicts[training_dict_idx] == None:
            continue
        else:
            child_dict = training_child_dicts[training_dict_idx]
            ph_dict = bib.make_ph_dict(child_dicts=[child_dict])
            flux_dict = bib.make_flux_dict(child_dicts=[child_dict])
            flux_lines = bib.make_flux_block(flux_dict, flux_path_modifier)
            all_ph_lines = bib.make_pulse_history_block(ph_dict)
            all_sched_lines = bib.make_schedule_block(child_dicts=[child_dict], ph_dict=ph_dict, flux_dict=flux_dict)
            nuclib_lines = bib.read_nuclib(nuclib)
            vol_lines, load_lines, mix_lines = bib.make_volume_block(nuclib_lines, volume)
            assembled_lines = bib.make_input_lines(vol_lines, load_lines, mix_lines, flux_lines, all_ph_lines, all_sched_lines, trunc_tolerance)
            with open(inp_file_folder+"/"+filenames[training_dict_idx], 'w') as new_inp:
                new_inp.write(assembled_lines)    

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--training_case_yaml', help="Path (str) to YAML containing inputs to construct training data")
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
    # Connection to sqlite db with a flux spectra table
    sqlite_conn_db_name = inputs['sqlite_db_name']
    nuclib = inputs['nuclib_path']
    volume = inputs['volume']
    trunc_tolerance = inputs['trunc_tolerance']
    inp_file_folder = inputs['temp_inp_file_folder']
    flux_path_modifier = inputs['flux_path_modifier']

    training_inp_info = tiptd.make_flux_tirr_combos(rel_on_time_factors, flux_norm_factors, flux_files)
    training_child_dicts = tiptd.write_training_params_dict(training_inp_info, min_on_times, time_unit)

    sqlite_conn = sqlite3.connect(sqlite_conn_db_name)
    filenames = mtf.make_filename_strings(training_inp_info, sqlite_conn, min_on_times, time_unit, trunc_tolerance)
    sqlite_conn.close()

    make_all_input_files(training_child_dicts, flux_path_modifier, nuclib, volume, trunc_tolerance, inp_file_folder, filenames)

if __name__ == "__main__":
    main()