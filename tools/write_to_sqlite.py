import alara_output_processing as aop
import numpy as np
import openmc
import argparse
import yaml
import pandas as pd
import sqlite3
from sympy import symbols, Eq, solve

def open_flux_file(flux_file):
    flux_lines = open(flux_file, 'r').readlines()
    return flux_lines

def calc_time_params(active_burn_time, duty_cycle_list, num_pulses):
    t_irr_arr = np.ndarray((len(num_pulses), len(duty_cycle_list)), dtype=float)
    dwell_time_arr = t_irr_arr.copy()
    dwell_time = symbols('dwell_time')
    pulse_length_list = []
    
    for num_ind, num in enumerate(num_pulses):
        pulse_length = active_burn_time / num
        pulse_length_list.append(pulse_length)
        for duty_cycle_ind, duty_cycle in enumerate(duty_cycle_list):
            dwell_time_eq = Eq(pulse_length / (pulse_length + dwell_time), duty_cycle)
            dwell_time_sol = solve((dwell_time_eq),(dwell_time))
            dwell_time_arr[num_ind, duty_cycle_ind] = dwell_time_sol[0]
            # The total irradiation time can be calculated once the dwell time has been found
            t_irr = pulse_length * num + dwell_time_sol[0] * (num - 1)
            t_irr_arr[num_ind, duty_cycle_ind] = t_irr   
    return pulse_length_list, dwell_time_arr, t_irr_arr
             
def write_out_adf(runs_list):
    #start with one dictionary of runs (runs_list[0]) first
    for runs in runs_list[0]:
        lib = aop.DataLibrary()
        adf = lib.make_entries(runs)
    return adf

def parse_flux_lines(flux_lines, num_blocks):
    energy_bins = openmc.mgxs.GROUP_STRUCTURES['VITAMIN-J-175'] 
    bin_widths = []
    for bin_index in range(len(energy_bins) - 1):
        bin_width = energy_bins[bin_index + 1] - energy_bins[bin_index]
        bin_widths.append(bin_width)

    all_entries = []
    for flux_line in flux_lines:
        if flux_line.strip(): #if the current line is not blank
            all_entries.extend(flux_line.split())
    all_entries = np.array(all_entries, dtype=float)
    flux_array = all_entries.reshape(num_blocks, len(bin_widths))
    return bin_widths, flux_array

def normalize_flux_spectrum(flux_array, bin_widths, num_blocks, total_flux): #flux spectrum shape
    norm_flux_array = flux_array.copy()

    for zone_idx in range(num_blocks):
        norm_flux_array[zone_idx,:] = (norm_flux_array[zone_idx,:] / bin_widths) * (1 / total_flux[zone_idx])  
    return norm_flux_array

def calc_avg_flux_mag(total_flux, active_burn_time):
    avg_flux = total_flux[0] / active_burn_time
    # total_flux[0] = total_flux[...]
    return avg_flux

def calc_avg_flux_mag_on_off(total_flux, num_pulses, pulse_length_list, dwell_time_arr): #avg flux magnitude
    #avg = total flux (for each zone) over all energy bins, time-integrated, divided by total irradiation time
    # for now, the flux across all zones is assumed to be the same
    avg_flux_arr = dwell_time_arr.copy()
    for dwell_time_ind, dwell_time in enumerate(dwell_time_arr):
        on_time = pulse_length_list[dwell_time_ind] * num_pulses[dwell_time_ind]
        off_time = dwell_time * (num_pulses[dwell_time_ind] - 1)
        # total_flux[0] = total_flux[...]
        avg_flux_arr[dwell_time_ind, :] =  (on_time * total_flux[0] + off_time * 0) / (on_time + off_time)
    # (on_time * total_flux[0] (one value for now) + off_time * 0 flux) / (on_time + off_time)
    return avg_flux_arr

def write_sqlite(adf, inputs, norm_flux_array, avg_flux):
    #Add new columns to dataframe
    adf['active_t_irr_(s)'] = inputs['active_burn_time']
    adf['active_t_irr_(s)'] = aop.convert_times(adf['active_t_irr_(s)'], from_unit='y', to_unit='s')
    new_columns = {'flux_spectrum_shape' : [norm_flux_array[0]] *  len(adf.index), 
                    'avg_flux_mag' : avg_flux,
                    'run_lbl' : [list(inputs.keys())[4]] * len(adf.index)
                  }
    adf = adf.assign(**new_columns)

    #Remove some columns:
    adf.drop(columns=['time', 'time_unit', 'variable', 'var_unit', 'block', 'block_num'], inplace=True)

    #Rename some columns:
    adf.rename(columns={'value':'num_dens_(atoms/cm3)'}, inplace=True)
    
    sqlite_conn = sqlite3.connect('activation_results.db')
    adf.to_sql('number_densities', sqlite_conn, if_exists='replace', method="multi")

    try:
        cursor = sqlite_conn.cursor()  
        sqlite_conn.commit()
        #cursor.execute("SELECT * FROM number_densities")
        result = cursor.fetchall()

        cursor.close()

        if sqlite_conn:
            sqlite_conn.close()
    except sqlite3.OperationalError as error:
        print(error)        

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

def main():        
    args = parse_args()
    inputs = read_yaml(args.db_yaml)  
    flux_file = inputs['flux_file']    
    active_burn_time = inputs['active_burn_time']
    duty_cycle_list = inputs['duty_cycles']
    num_pulses = inputs['pulse_list'] 
    runs_list = [inputs['runs_100_4y'], inputs['runs_90_4y'], inputs['runs_50_4y'], inputs['runs_25_4y']]

    flux_lines = open_flux_file(flux_file)
    pulse_length_list, dwell_time_arr, t_irr_arr = calc_time_params(active_burn_time, duty_cycle_list, num_pulses)
    adf = write_out_adf(runs_list)
    num_blocks = adf['block_num'].nunique()
    bin_widths, flux_array = parse_flux_lines(flux_lines, num_blocks)
    total_flux = np.sum(flux_array, axis=1) #sum over the bin widths of flux array
    norm_flux_array = normalize_flux_spectrum(flux_array, bin_widths, num_blocks, total_flux)
    avg_flux_arr = calc_avg_flux_mag_on_off(total_flux, num_pulses, pulse_length_list, dwell_time_arr)
    avg_flux = calc_avg_flux_mag(total_flux, active_burn_time)
    write_sqlite(adf, inputs, norm_flux_array, avg_flux)

if __name__ == "__main__":
    main()
