import alara_output_processing as aop
import numpy as np


def generate_adf(run_lbl, output_filepath):
    alara_data = aop.FileParser(output_filepath, run_lbl, 's')
    adf = alara_data.extract_tables()
    return adf

