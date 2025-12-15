import argparse
import yaml
import alara_output_processing as aop
import openmc
import numpy as np

def write_out_tables(run_out, run_lbl, time_unit):
    '''
    Takes the output of a single ALARA run and converts output tables to Pandas DataFrame
    inputs: 
        run_out (path to ALARA output file)
        run_lbl (name of the run)
        time_unit (units for cooling time)
    output: output_tables (Pandas DataFrame containing all output data)
    '''
    alara_data = aop.FileParser(run_out, run_lbl, time_unit)
    output_tables = alara_data.extract_tables()
    return output_tables

def open_flux_file(flux_file):
    flux_lines = open(flux_file, 'r').readlines()
    return flux_lines

def parse_flux_lines(flux_lines):
    '''
    Uses provided list of flux lines and group structure applied to the run to create an array of flux entries, with:
    # rows = # flux entries / # group structure bins
    # columns = # group structure bins
    input : flux_lines (list of lines from ALARA flux file)
    output : flux_array (numpy array of shape # zones/intervals/mixtures x )
    '''
    energy_bins = openmc.mgxs.GROUP_STRUCTURES['VITAMIN-J-175']     
    bin_widths = energy_bins[1:] - energy_bins[:-1]
    all_entries = []
    for flux_line in flux_lines:
        if flux_line.strip(): #if the current line is not blank
            all_entries.extend(flux_line.split())
    all_entries = np.array(all_entries, dtype=float)
    flux_array = all_entries.reshape(int(len(all_entries) / len(bin_widths)), len(bin_widths))
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

    run_out = list(inputs['runs_100_4y'].values())[0]
    run_lbl = list(inputs['runs_100_4y'].keys())[0]
    time_unit = inputs['time_unit']

    output_tables = write_out_tables(run_out, run_lbl, time_unit)

    flux_file = inputs['flux_file'] 
    flux_lines = open_flux_file(flux_file)
    flux_array = parse_flux_lines(flux_lines)

if __name__ == "__main__":
    main()    