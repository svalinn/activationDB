import adf_to_sqlite
import create_adf
import sqlite3
import training_inp_params_to_dict as tiptd
import make_training_filenames as mtf
import argparse
import yaml
import numpy as np
import uuid
import sched_post_processor
import schedule_transforms
import alara_bookkeeping

# def search_for_match(top_dict, search_str):
#     '''
#     Takes a top dictionary with nested lists and sub-dictionaries and searches for matches with a provided string.
#     '''
#     matches = []
#     for key, value in top_dict.items():
#         if key.startswith(search_str):
#             matches.append(value)
#         elif isinstance(value, dict):
#             match_res = search_for_match(value, search_str)
#             matches.extend(match_res)
#         elif isinstance(value, list):
#             for item in value:
#                 if isinstance(item, dict):
#                     results_from_list = search_for_match(item, search_str)
#                     matches.extend(results_from_list)
#     return matches

def search_for_ph(top_dict, corr_ph_name, pulse_dict):
    '''

    '''
    for key, value in top_dict.items():
        if value == corr_ph_name:
            top_dict[value] = pulse_dict[value]
        elif isinstance(value, dict):
            match_res = search_for_ph(value, corr_ph_name, pulse_dict)
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    results_from_list = search_for_ph(item, corr_ph_name, pulse_dict)
    return top_dict


def attach_pulse_to_sch_dict(pulse_dict, sch_dict):
    search_str = "corr_ph_name"
    corr_ph_name = search_for_match(search_str)[0]



def save_out_to_db(training_inp_info, filename_array, inp_file_folder, out_file_folder, flux_path_modifier, sqlite_conn, git_hash):
    for (min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx), _ in np.ndenumerate(filename_array):
        inp_filename = filename_array[min_on_time_idx, rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx]
        if inp_filename is None:
            # by construction, a filename_array entry is None only whenever a training_inp_info entry is None (and vice versa)
            continue
        else:
            output_path = out_file_folder + "/" + inp_filename + "_out"
            run_lbl = uuid.uuid4()
            flux_file = training_inp_info[rel_on_time_factor_idx, flux_norm_factor_idx, flux_file_idx][2]
            all_flux_entries = adf_to_sqlite.open_flux_file(flux_file+flux_path_modifier)
            # hard-code number of stable nuclides?
            num_groups = int(len(all_flux_entries) / 286)
            flux_array = adf_to_sqlite.parse_flux_str(all_flux_entries, num_groups)
            norm_flux_arr = adf_to_sqlite.normalize_flux(flux_array)
            adf = create_adf.generate_single_adf(run_lbl, output_path)
            adf = adf_to_sqlite.modify_adf_for_db(adf)


            lines = sched_post_processor.read_out(output_path)
            pulse_dict = sched_post_processor.read_pulse_histories(lines)
            sch_dict = sched_post_processor.make_nested_dict(lines)
            sch_dict = sch_dict['top_schedule']['children']
            pulse_length = sch_dict['top_schedule']['pulse_length']
            pulse_history_verbose_dict = pulse_dict[sch_dict[0]['corr_ph_name']]
            pulse_history_tuple = (pulse_history_verbose_dict["num_pulses_all_levels"], pulse_history_verbose_dict["delay_seconds_all_levels"])
            t_irr = schedule_transforms.flatten_pulse_history(pulse_length, pulse_history_tuple)[0]

            t_irr_arr_mod = np.asarray([t_irr]*len(adf))
            adf = adf_to_sqlite.map_adf_flux_tirr(adf, norm_flux_arr, sqlite_conn, t_irr_arr_mod)
            conn_cursor = adf_to_sqlite.write_to_sqlite(adf, sqlite_conn)

            alara_bookkeeping.create_sqlite_table(conn_cursor)
            data_dict = {"id" : [run_lbl],
                         "input_file" : [inp_file_folder+inp_filename],
                         "output_file" : [output_path],
                         "flux_file" : [flux_file],
                         "git_hash" : [git_hash]
                         }
            alara_bookkeeping.populate_table(conn_cursor, data_dict)
            return conn_cursor


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

    min_on_times = inputs['min_on_times']
    time_unit = inputs['min_on_time_unit']
    rel_on_time_factors = inputs['rel_on_time_factors']
    flux_norm_factors = inputs['flux_norm_factors']
    flux_files = inputs['flux_files']
    sqlite_conn_db_name = inputs['sqlite_db_name']
    flux_path_modifier = inputs['flux_path_modifier']
    trunc_tolerance = inputs['trunc_tolerance']
    inp_file_folder = inputs['inp_file_folder']
    out_file_folder = inputs['out_file_folder']
    git_hash = inputs['git_hash']

    training_inp_info = tiptd.make_flux_tirr_combos(rel_on_time_factors, flux_norm_factors, flux_files)
    sqlite_conn = sqlite3.connect(sqlite_conn_db_name)
    filename_array = mtf.make_filename_strings(training_inp_info, sqlite_conn, min_on_times, time_unit, trunc_tolerance)
    conn_cursor = save_out_to_db(training_inp_info, filename_array, inp_file_folder, out_file_folder, flux_path_modifier, sqlite_conn, git_hash)
    conn_cursor.commit()
    adf_to_sqlite.close_sqlite_conn(conn_cursor)


if __name__ == "__main__":
    main()
