import argparse
import yaml
import numpy as np
import pandas as pd
import alara_output_processing as aop
import sqlite3

def calc_time_params(active_burn_time, duty_cycle_list, num_pulses):
    '''
    Uses provided pulsing information to determine dwell time and total irradiation time.
    Assumes that the active irradiation time per pulse and dwell time between pulses both remain constant in any given simulation.
    Iterates over the number of pulses, and for each number, calculates dwell time.
    The duty cycle is defined as the pulse length / (pulse length + dwell time).
    inputs:
        active_burn_time : total active irradiation time (float) in any chosen unit
        duty_cycle_list : list of chosen duty cycles (float)
        num_pulses : list of number of pulses (int) that the active irradiation period is divided into
    '''
    pulse_lengths = active_burn_time / num_pulses
    rel_dwell_times = (1 - duty_cycle_list) / duty_cycle_list
    abs_dwell_times = np.outer(rel_dwell_times, pulse_lengths)
    t_irr_arr = active_burn_time + abs_dwell_times * (num_pulses - 1)
    return pulse_lengths, abs_dwell_times, t_irr_arr

def open_flux_file(flux_file):
    with open(flux_file, 'r') as flux_data:
        flux_str = flux_data.read()
    all_flux_entries = np.array(flux_str.split(), dtype=float)
    if len(all_flux_entries) == 0:
        raise Exception("The chosen flux file is empty.")
    return all_flux_entries

def get_energy_bins(vit_j_file):
    with open(vit_j_file, 'r') as vit_j:
        energy_bins = vit_j.read()
    energy_bins = np.fromstring(energy_bins, sep=' ')    
    return energy_bins    

def parse_flux_str(all_flux_entries, energy_bins):
    '''
    Uses provided list of flux lines and group structure applied to the run to create an array of flux entries, with:
    # rows = # of intervals = total # flux entries / # group structure bins
    # columns = # group structure bins
    input : all_flux_entries (data (numpy array) from ALARA flux file)
    output : flux_array (numpy array of shape # intervals x number of energy groups)
    '''
    num_groups = len(energy_bins) - 1
    num_intervals = len(all_flux_entries) // num_groups
    if len(all_flux_entries) % num_groups != 0:
        raise Exception("The number of intervals must be an integer.")
    flux_array = all_flux_entries.reshape(num_intervals, num_groups)
    return flux_array

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db_yaml', default = "iter_dt_out.yaml", help="Path (str) to YAML containing inputs")
    args = parser.parse_args()
    return args

def read_yaml(yaml_arg):
    '''
    input:
        yaml_arg : output of parse_args() corresponding to args.db_yaml
    '''
    with open(yaml_arg, 'r') as yaml_file:
        inputs = yaml.safe_load(yaml_file)
    return inputs  

def modify_adf(adf, norm_flux_arr, t_irr_arr, inputs):
    adf = adf.filter_rows(
        filter_dict=
        {
            "time": -1,
            "variable" : adf.VARIABLE_ENUM["Number Density"]
        }
    )
    #Remove some columns:
    adf.drop(columns=['time', 'time_unit', 'variable', 'var_unit', 'block', 'block_num'], inplace=True)    
    #Rename some columns:
    adf.rename(columns={'value':'num_dens_(atoms/cm3)'}, inplace=True)
    block_names = adf['block_name'].unique()
    flux_map = dict(zip(block_names, norm_flux_arr))

    # Normalized flux spectrum shape:
    adf['flux_spec_shape'] = adf['block_name'].map(flux_map)

    num_pulses = inputs['num_pulses']
    duty_cycles = inputs['duty_cycles']

    # Extract the number of pulses and duty cycles from the run label
    pulse_num_dc = adf['run_lbl'].str.extract(r'_(\d+)p_(\d+)_').astype(int)

    # Map num_pulses and duty_cycles to an index
    pulse_idx = pulse_num_dc[0].map({pulse_num: i for i, pulse_num in enumerate(num_pulses)})
    duty_cycle_idx  = (pulse_num_dc[1]/100).map({duty_cycle: i for i, duty_cycle in enumerate(duty_cycles)})

    # Add flattened irradiation time:
    adf['t_irr_flat'] = t_irr_arr.T[pulse_idx.to_numpy(), duty_cycle_idx.to_numpy()]
    adf['t_irr_flat'] = aop.convert_times(adf['t_irr_flat'], from_unit='y', to_unit='s')

    return adf

def write_to_sqlite(adf):
    sqlite_conn = sqlite3.connect('activation_results.db')
    adf.to_sql('number_densities', sqlite_conn, if_exists='replace', method="multi")

    try:
        cursor = sqlite_conn.cursor()  
        sqlite_conn.commit()
        result = cursor.fetchall()
        cursor.close()

        if sqlite_conn:
            sqlite_conn.close()
    except sqlite3.OperationalError as error:
        print(error)  

def main():        
    args = parse_args()
    inputs = read_yaml(args.db_yaml)

    flux_file = inputs['flux_file']
    vit_j_file = inputs['vit_j_file']
    all_flux_entries = open_flux_file(flux_file)
    energy_bins = get_energy_bins(vit_j_file)
    flux_array = parse_flux_str(all_flux_entries, energy_bins)

    active_burn_time = np.asarray(inputs['active_burn_time'])
    duty_cycle_list = np.asarray(inputs['duty_cycles'])
    num_pulses = np.asarray(inputs['num_pulses'])
    pulse_lengths, abs_dwell_times, t_irr_arr = calc_time_params(active_burn_time, duty_cycle_list, num_pulses)

    total_flux = np.sum(flux_array, axis=1) # sum over the bin widths of flux array
    # normalize flux spectrum by the total flux in each interval
    norm_flux_arr =  flux_array / total_flux.reshape(len(total_flux), 1) # 2D array of shape num_intervals x num_groups

    # Assume adf exists
    adf = modify_adf(adf, norm_flux_arr, t_irr_arr, inputs)
    write_to_sqlite(adf)

if __name__ == "__main__":
    main()