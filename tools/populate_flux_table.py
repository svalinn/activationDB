import numpy as np
import make_flux_table as mft
from adf_to_sqlite import normalize_flux as nf
import sqlite3
import yaml
import argparse
import json

def prepare_flux_spectra(flux_spectra):
    '''
    Takes a set of flux spectra and modifies each spectrum to be a json-formatted string.
    :param: flux_spectra (iterable of iterables of fluxes (float))
    '''
    flux_spectra = np.asarray(flux_spectra)
    norm_flux_arr = nf(flux_spectra)
    norm_flux_arr_str = np.asarray([json.dumps(norm_flux_spec.tolist()) for norm_flux_spec in norm_flux_arr])
    return norm_flux_arr_str

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--flux_yaml", help="yaml file containing flux spectra labeled by the path to the flux file", default="flux_spectra.yaml")
    parser.add_argument("--db_name", help="sqlite connection object pointing to a database with a flux table", default="activation_results.db")
    args = parser.parse_args()
    return args

def read_yaml(yaml_arg):
    with open(yaml_arg, "r") as yaml_file:
        inputs = yaml.safe_load(yaml_file)
    return inputs

def main():
    args = parse_args()
    inputs = read_yaml(args.flux_yaml)
    flux_files = list(flux_file for flux_file in inputs)
    flux_spectra = list(inputs[flux_file] for flux_file in inputs)
    db_name = args.db_name

    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    norm_flux_arr_str = prepare_flux_spectra(flux_spectra)

    flux_data_dict = {'flux_files' : flux_files,
                      'flux_spec_shapes' : norm_flux_arr_str
                      }
    mft.create_flux_table(cur)
    mft.populate_flux_table(cur, flux_data_dict)

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()


