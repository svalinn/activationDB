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
    return t_irr_arr

def open_flux_file(flux_file):
    with open(flux_file, 'r') as flux_data:
        flux_str = flux_data.read()
    all_flux_entries = np.array(flux_str.split(), dtype=float)
    if len(all_flux_entries) == 0:
        raise Exception("The chosen flux file is empty.")
    return all_flux_entries


def parse_flux_str(all_flux_entries, num_groups):
    '''
    Uses provided list of flux lines and group structure applied to the run to create an array of flux entries, with:
    # rows = # of intervals = total # flux entries / # group structure bins
    # columns = # group structure bins
    input : all_flux_entries (data (numpy array) from ALARA flux file)
            num_groups : total number (int) of energy groups from group structure
    output : flux_array (numpy array of shape # intervals x # energy groups)
    '''
    num_intervals = len(all_flux_entries) // num_groups
    if len(all_flux_entries) % num_groups != 0:
        raise Exception("The number of intervals must be an integer.")
    flux_array = all_flux_entries.reshape(num_intervals, num_groups)
    return flux_array


def modify_adf_columns(adf):
    adf = adf.filter_rows(filter_dict={
        "time": -1,
        "variable": adf.VARIABLE_ENUM["Number Density"]
    })
    #Remove some columns:
    adf.drop(columns=[
        'time', 'time_unit', 'variable', 'var_unit', 'block', 'block_num'
    ],
             inplace=True)
    #Rename some columns:
    adf.rename(columns={'value': 'num_dens_(atoms/cm3)'}, inplace=True)

    return adf

def map_adf_flux_tirr(adf, norm_flux_arr, t_irr_arr_mod):

    block_names = adf['block_name'].unique()
    flux_map = dict(zip(block_names, norm_flux_arr))

    # Normalized flux spectrum shape:
    adf['flux_spec_shape'] = adf['block_name'].map(flux_map)
    adf['t_irr'] = t_irr_arr_mod
    return adf


def write_to_sqlite(adf):
    sqlite_conn = sqlite3.connect('activation_results.db')
    adf.to_sql('number_densities',
               sqlite_conn,
               if_exists='append',
               method="multi")

    try:
        cursor = sqlite_conn.cursor()
        sqlite_conn.commit()
        result = cursor.fetchall()
        cursor.close()

        if sqlite_conn:
            sqlite_conn.close()
    except sqlite3.OperationalError as error:
        print(error)
