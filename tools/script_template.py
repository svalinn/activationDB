import argparse
import yaml
import numpy as np
import openmc

def calc_time_params(active_burn_time, duty_cycle_list, num_pulses):
    '''
    Uses provided pulsing information to determine dwell time and total irradiation time.
    Assumes that the active irradiation time per pulse and dwell time between pulses both remain constant in any given simulation.
    (This is always maintained for a single-level schedule and single-level pulse history.)

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
        flux_lines = flux_data.readlines()
    return flux_lines

def parse_flux_lines(flux_lines):
    '''
    Uses provided list of flux lines and group structure applied to the run to create an array of flux entries, with:
    # rows = # of intervals = total # flux entries / # group structure bins
    # columns = # group structure bins
    input : flux_lines (list of lines from ALARA flux file)
    output : flux_array (numpy array of shape # intervals x number of energy groups)
    '''
    energy_bins = openmc.mgxs.GROUP_STRUCTURES['VITAMIN-J-175']           
    all_entries = np.array(' '.join(flux_lines).split(), dtype=float)
    if len(all_entries) == 0:
        raise Exception("The chosen flux file is empty.")
    num_groups = len(energy_bins) - 1
    num_intervals = len(all_entries) // num_groups
    if len(all_entries) % num_groups != 0:
        raise Exception("The number of intervals must be an integer.")
    flux_array = all_entries.reshape(num_intervals, num_groups)
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

def main():        
    args = parse_args()
    inputs = read_yaml(args.db_yaml)

    flux_file = inputs['flux_file'] 
    flux_lines = open_flux_file(flux_file)
    flux_array = parse_flux_lines(flux_lines)

    active_burn_time = np.asarray(inputs['active_burn_time'])
    duty_cycle_list = np.asarray(inputs['duty_cycles'])
    num_pulses = np.asarray(inputs['num_pulses'])
    pulse_lengths, abs_dwell_times, t_irr_arr = calc_time_params(active_burn_time, duty_cycle_list, num_pulses)

    total_flux = np.sum(flux_array, axis=1) #sum over the bin widths of flux array
    avg_flux_arr = calc_flux_mag_flattened(total_flux, active_burn_time, t_irr_arr)
    # normalize flux spectrum by the total flux in each interval
    norm_flux_arr =  flux_array / total_flux.reshape(len(total_flux), 1) # 2D array of shape num_intervals x num_groups
    # for each interval, calculate flux averaged over time elapsed between the start of the 1st pulse and the end of the last
    avg_flux_arr = np.multiply.outer(total_flux, active_burn_time / t_irr_arr) # array of shape num_intervals x len(duty_cycles) x len(num_pulses)

if __name__ == "__main__":
    main()