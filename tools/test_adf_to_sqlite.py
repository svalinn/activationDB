import numpy as np
import alara_output_processing as aop
import adf_to_sqlite as ats
import sqlite3
import pytest
import json
import pandas as pd

@pytest.mark.parametrize( "all_flux_entries, num_groups, exp_flux_arr",
                          [(np.array([2,4,6,8,10,2,4,6,8,10]), 5, np.array([[2,4,6,8,10], [2,4,6,8,10]]))
                           ])

def test_parse_flux_str(all_flux_entries, num_groups, exp_flux_arr):
    obs_flux_arr = ats.parse_flux_str(all_flux_entries, num_groups)
    assert obs_flux_arr.all() == exp_flux_arr.all()

@pytest.mark.parametrize( "flux_arr, exp_norm_flux_arr",
                          [
                            (np.array([[2,4,6,8,10], [2,4,6,8,10]]), np.array([[num / 30 for num in [2,4,6,8,10]], 
                                                                               [num / 30 for num in [2,4,6,8,10]]
                                                                               ])
                                                                               )
                          ])

def test_normalize_flux(flux_arr, exp_norm_flux_arr):
    obs_norm_flux_arr = ats.normalize_flux(flux_arr)
    assert obs_norm_flux_arr.all() == exp_norm_flux_arr.all()

@pytest.mark.parametrize( "flux_arr, t_irr, flux_norm, exp_avg_flux_arr",
                          [
                            (np.array([[2,4,6,8,10], [2,4,6,8,20]]), 
                             5,
                             0.5,
                             np.array([30*0.5/5, 40*0.5/5])
                            )
                          ])

def test_average_flux(flux_arr, t_irr, flux_norm, exp_avg_flux_arr):
    obs_avg_flux_arr = ats.average_flux(flux_arr, t_irr, flux_norm)
    assert obs_avg_flux_arr.all() == exp_avg_flux_arr.all()    

@pytest.mark.parametrize( "adf",
                          [
                            (aop.ALARADFrame(data=
        {"value": [5.678e-11]*2,
        "time": [-1]*2,
        "time_unit" : ["s"]*2,
        "variable": [0]*2,
        "var_unit": ["atoms/cm3"]*2,
        "block" : [1,2],
        "block_name": ["Be", "W"],
        "block_num": [2]*2,
        "nuclide": ["h-1"]*2,
        "half_life": ["-1"]*2,
        "run_lbl": ["test_case", "test_case"]}))
                          ])

def test_modify_adf_for_db(adf):
    '''
    Ensure that the expected columns exist in the adf.
    '''
    adf = ats.modify_adf_for_db(adf)
    assert not any(col in adf for col in [
        "value",
        "time",
        "time_unit",
        "variable",
        "var_unit",
        "block",
        "block_num",
    ])
    assert (all(col in adf
                for col in ["num_dens_(atoms/cm3)", "half_life", "block_name"]))

@pytest.mark.parametrize( "test_adf, flux_array, sqlite_conn, t_irr, flux_norm, exp_mod_adf",
                          [
                            (aop.ALARADFrame(data=
                            {"num_dens_(atoms/cm3)": [5.678e-11]*2,
                            "block_name": ["Be", "W"],
                            "nuclide": ["h-1"]*2,
                            "half_life": ["-1"]*2,
                            "run_lbl": ["test_case", "test_case"]}),
                            np.array([[1,3,5,7,9], [2,4,6,8,10]]),
                            sqlite3.connect(":memory:").execute("""CREATE TABLE IF NOT EXISTS flux_spectra (
                            flux_spec_shape_id INT PRIMARY KEY,
                            flux_spec_shape TEXT) 
                            """).executemany("INSERT INTO flux_spectra (flux_spec_shape_id, flux_spec_shape) VALUES (?, ?)",
                            list(zip(*{
                                    'flux_spec_shape_id' : [1.0,2.0],
                                    'flux_spec_shape' : [json.dumps([num / 25 for num in [1,3,5,7,9]]),
                                                    json.dumps([num / 30 for num in [2,4,6,8,10]])]
                                    }.values()))
                                    ).connection,
                            5,
                            0.5,
                            aop.ALARADFrame(data=
                            {"num_dens_(atoms/cm3)": [5.678e-11]*2,
                            "block_name": ["Be", "W"],
                            "nuclide": ["h-1"]*2,
                            "half_life": ["-1"]*2,
                            "run_lbl": ["test_case", "test_case"],
                            "flux_spec_shape_id" : [1,2],
                            "avg_flux_mag" : [5*0.5,6*0.5],
                            "t_irr" : [5]*2
                            })
                            )
                          ])

def test_map_adf_flux_tirr(test_adf, flux_array, sqlite_conn, t_irr, flux_norm, exp_mod_adf):
    obs_mod_adf = ats.map_adf_flux_tirr(test_adf, flux_array, sqlite_conn, t_irr, flux_norm)
    pd.testing.assert_frame_equal(obs_mod_adf, exp_mod_adf, check_dtype=False)

@pytest.mark.parametrize( "mod_adf",
                          [
                            (aop.ALARADFrame(data=
        {"num_dens_(atoms/cm3)": [5.678e-11]*2,
        "block_name": ["Be", "W"],
        "nuclide": ["h-1"]*2,
        "half_life": ["-1"]*2,
        "run_lbl": ["test_case", "test_case"]}))
                          ])
    
def test_write_to_sqlite(mod_adf):
    cursor = ats.write_to_sqlite(mod_adf, sqlite3.connect(":memory:"))
    cursor.execute("SELECT * FROM number_densities")
    result = cursor.fetchall()
    assert len(result) == len(mod_adf["half_life"])
    assert len(result[0]) == 5

@pytest.mark.parametrize( "test_cursor",
                          [sqlite3.connect(":memory:").cursor()])    

def test_close_sqlite_conn(test_cursor):
    # This function has a built-in test in the form of catching operational errors
    ats.close_sqlite_conn(test_cursor)