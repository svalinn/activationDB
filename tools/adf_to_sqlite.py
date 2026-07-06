import numpy as np
import sqlite3
import json


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
    :param: all_flux_entries: (data (numpy array) from ALARA flux file)
    :param: num_groups : total number (int) of energy groups from group structure
    '''
    if len(all_flux_entries) % num_groups != 0:
        raise Exception("The number of intervals must be an integer.")
    num_intervals = len(all_flux_entries) // num_groups
    flux_array = all_flux_entries.reshape(num_intervals, num_groups)
    return flux_array

def normalize_flux(flux_array):
    '''
    Obtain the total flux by summing over the bin widths of the flux array,
    then normalize the spectrum by the total flux in each interval.
    :param: flux_array: (numpy array of shape # intervals x # energy groups)
    '''
    total_flux = np.sum(flux_array, axis=1)
    #norm_flux_arr = 2D array of shape num_intervals x num_groups
    norm_flux_arr = flux_array / total_flux.reshape(len(total_flux), 1)
    return norm_flux_arr


def find_flux_spec_shape_id(sqlite_conn, flux_spec_shape):
    '''
    Assuming that a table called flux_spectra exists in the database, find
    the id of the desired flux spectrum from the table. Assumes that
    the data in the table is stored in json/text format.
    :param: sqlite_conn (sqlite3 connection object)
    :param: flux_spec_shape (iterable, normalized flux spectrum with the number of entries 
                            being the number of groups in the structure)
    '''
    result = sqlite_conn.execute(
    "SELECT flux_spec_shape_id FROM flux_spectra WHERE flux_spec_shape = ?",
    (json.dumps(flux_spec_shape.tolist()),)
    )
    flux_spec_shape_id = result.fetchone()[0]
    return flux_spec_shape_id


def modify_adf_for_db(adf):
    '''
    Filters the adf for the pre-shutdown state and the number density.
    Removes columns that do not add information required for the database.
    :param: adf: ALARA DFrame object
    '''
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


def map_adf_flux_tirr(adf, norm_flux_arr, sqlite_conn, t_irr_arr_mod):
    '''
    Finds the unique block names in the adf and maps the correct flux spectrum
    to the block. Assigns a column to store irradiation time.
    :param: norm_flux_arr: numpy array of flux spectrum shape (# intervals x # energy groups)
    :param: t_irr_arr_mod: numpy array of irradiation times where the total number of entries
    is the number of rows in the adf
    '''

    block_names = adf['block_name'].unique()
    for unique_bn, flux_spec_shape in zip(block_names, norm_flux_arr):
        flux_spec_shape_id = find_flux_spec_shape_id(sqlite_conn, flux_spec_shape)
        adf.loc[adf["block_name"] == unique_bn, "flux_spec_shape_id"] = flux_spec_shape_id
    adf['t_irr'] = t_irr_arr_mod
    return adf

def write_to_sqlite(adf, sqlite_conn):
    '''
    Initialize a connection to a SQLite database, and write the adf
    to it. Catches any errors produced during this process.
    '''
    try:
        adf.to_sql('number_densities',
                   sqlite_conn,
                   if_exists='append',
                   method="multi",
                   index=False)
        sqlite_conn.commit()
    except sqlite3.OperationalError as error:
        print(error)
    return sqlite_conn.cursor()


def close_sqlite_conn(cursor):
    '''
    Closes inidividual SQLite cursor objects, and the connection
    to the database. To be executed after running write_to_sqlite()
    or anytime a SQLite connection has been established.
    :param: cursor: SQLite cursor object
    '''
    try:
        cursor.close()
        if cursor.connection:
            cursor.connection.close()
    except sqlite3.OperationalError as error:
        print(error)
