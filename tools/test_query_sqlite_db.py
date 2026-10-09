import pytest
import query_sqlite_db as qsd
import sqlite3
import json

@pytest.mark.parametrize("sqlite_conn, column_name, row_value, exp_flux_spec_shape_id", [
    (
        sqlite3.connect(":memory:").cursor().execute(
                """
                CREATE TABLE flux_spectra (
                flux_spec_shape_id INTEGER PRIMARY KEY,
                flux_file TEXT,
                flux_spectrum TEXT,
                UNIQUE(flux_file, flux_spectrum)
                )
                """
            ).executemany("INSERT INTO flux_spectra (flux_file, flux_spectrum) VALUES (?, ?)",
            list(zip(*{
                'flux_file' : ['../fnsf', '../iter_dt'],
                'flux_spectrum' : ['[3, 9,12]', json.dumps([5,7, 11, 13, 25])]
            }.values()))).connection,
        'flux_spectrum',
        [3,9, 12],
        1
    ),

    (
        sqlite3.connect(":memory:").cursor().execute(
                """
                CREATE TABLE flux_spectra (
                flux_spec_shape_id INTEGER PRIMARY KEY,
                flux_file TEXT,
                flux_spectrum TEXT,
                UNIQUE(flux_file, flux_spectrum)
                )
                """
            ).executemany("INSERT INTO flux_spectra (flux_file, flux_spectrum) VALUES (?, ?)",
            list(zip(*{
                'flux_file' : ['../fnsf', '../iter_dt'],
                'flux_spectrum' : ['[3, 9, 12]', json.dumps([5, 7, 11, 13, 25])]
            }.values()))).connection,
        'flux_file',
        '../iter_dt',
        2
    )
     ])

def test_find_flux_spec_shape_id(sqlite_conn, column_name, row_value, exp_flux_spec_shape_id):
    obs_flux_spec_shape_id = qsd.find_flux_spec_shape_id(sqlite_conn, column_name, row_value)
    assert obs_flux_spec_shape_id == exp_flux_spec_shape_id