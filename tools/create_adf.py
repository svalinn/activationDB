import alara_output_processing as aop


def generate_single_adf(run_lbl, output_filepath):
    '''
    Creates a single ALARA DFrame object for a single run.
    :param: run_lbl (str, identifying label for run)
    :param: output_filepath (str, path to ALARA output file that run_lbl refers to)
    '''
    # Any cooling time unit may be chosen as this column gets overwritten in adf_to_sqlite.py
    alara_data = aop.FileParser(output_filepath, run_lbl, 's')
    adf = alara_data.extract_tables()
    return adf

def generate_adfs_from_dict(run_dict):
    '''
    Creates a list of ALARA DFrame objects. A separate adf is generated for each run
    as adf_to_sqlite.py is set up to work with one adf at a time. 
    :param: run_dict (dict of the form {'run_lbl_1' : 'output_filepath_1',
                                        'run_lbl_2' : 'output_filepath_2'
                                        })
    '''
    adf_list = []
    for run_lbl, output_filepath in run_dict.items():
        adf = generate_single_adf(run_lbl, output_filepath)
        adf_list.append(adf)
    return adf_list
