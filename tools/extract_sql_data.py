import polars as pl
import numpy as np

def make_dict_from_small_table(conn):
    '''
    Makes a dictionary where the keys are the integer IDs in the flux_spectra table,
    and the values are the spectra that the IDs correspond to.
    '''
    query = """
    SELECT flux_spectra.flux_spec_shape_id, flux_spectra.flux_spec_shape
    FROM flux_spectra
    """
    dict_df = pl.read_database(query=query,
                               connection=conn,
                               schema_overrides = {'flux_spec_shape_id' : pl.UInt8,
                                                   'flux_spec_shape' : pl.Categorical
                                                   }
                                )
    dict_df = dict(zip(dict_df['flux_spec_shape_id'], dict_df['flux_spec_shape']))
    return dict_df

def make_dfs_from_num_dens_table(conn, filter_str, batch_size, child_nucs, parent_nucs, approx_name=None):
    '''
    Makes separate Polars dataframes with the size of each dataframe given by the batch_size
    parameter.
    approx_none: Name of the approximation used with testing data (str), one of 'flattening' or 'compression'
    '''
    query = """
    SELECT nuclide, run_lbl, block_name, [num_dens_(atoms/cm3)], flux_spec_shape_id, t_irr, avg_flux_mag
    FROM number_densities
    JOIN alara_simulations
        ON number_densities.run_lbl = alara_simulations.id
    WHERE alara_simulations.input_file LIKE ?    
    """
    if approx_name is not None:
        query.replace("number_densities", "testing_number_densities")
    if approx_name == "flattening":
        query.replace("t_irr", "t_irr_flat")
    if approx_name == "compression":
        query.replace("t_irr, t_irr_compressed")

    partial_training_df_chunks = pl.read_database(query=query,
                                   connection=conn,
                                   iter_batches = True,
                                   batch_size = batch_size,
                                   execute_options={"parameters":(filter_str,)},
                                   schema_overrides={'nuclide' : pl.Enum(child_nucs),
                                                     'run_lbl' : pl.Categorical,
                                                     'block_name' : pl.Enum(parent_nucs),
                                                    'flux_spec_shape_id' : pl.UInt8
                                                    }
                                                    )
    return partial_training_df_chunks