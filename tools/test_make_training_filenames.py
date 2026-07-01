import pytest
import numpy as np
import sqlite3
import make_training_filenames as mtf

@pytest.mark.parametrize("training_inp_info, sqlite_conn, min_on_times, time_unit, exp_filenames", [
    (
np.array([
        [
            [
            None,
            None
            ],

            [
            (2, 0.3, '../fnsf'),
      
      (2, 0.3, '../iter_dt')
            ]
        ],

        [
            [
            None,
            None
            ],

            [
            None,
            None
            ]
        ]
      ], dtype=object),
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
                'flux_spectrum' : ['[3, 9,12]', '[5,7, 11, 13, 25]']
            }.values()))).connection,
        [10, 20],
        's',
        np.array([[
        [
            [
            None,
            None
            ],

            [
            "1_0.3_10s_2",
      
      "2_0.3_10s_2"
            ]
        ],

        [
            [
            None,
            None
            ],

            [
            None,
            None
            ]
        ]
    ],
    [
        [
            [
            None,
            None
            ],

            [
            "1_0.3_20s_2",
      
      "2_0.3_20s_2"
            ]
        ],

        [
            [
            None,
            None
            ],

            [
            None,
            None
            ]
        ]
    ]
    ], dtype=object)
)])

def test_make_filename_strings(training_inp_info, sqlite_conn, min_on_times, time_unit, exp_filenames):
    obs_filenames = mtf.make_filename_strings(training_inp_info, sqlite_conn, min_on_times, time_unit)
    assert np.array_equal(obs_filenames, exp_filenames)