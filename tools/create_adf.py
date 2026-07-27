import alara_output_processing as aop
import numpy as np


def generate_adf(run_lbl, output_filepath):
    alara_data = aop.FileParser(output_filepath, run_lbl, 's')
    adf = alara_data.extract_tables()
    return adf

def generate_adfs_from_dict(run_dict):
    # generating multiple adfs as adf_to_sqlite.py is set up to work with one adf at a time
    adf_list = []
    for run_lbl, output_filepath in run_dict.items():
        adf = generate_adf(run_lbl, output_filepath)
        adf_list.append(adf)
    return adf_list

def generate_adfs_from_mult_dicts(run_dicts):
    adf_dict_list = []
    for run_dict in run_dicts:
        adf_list = generate_adfs_from_dict(run_dict)
        adf_dict_list.extend(adf_list)
    return adf_dict_list    
