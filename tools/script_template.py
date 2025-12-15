import argparse
import yaml
import openmc
import numpy as np

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

if __name__ == "__main__":
    main()    