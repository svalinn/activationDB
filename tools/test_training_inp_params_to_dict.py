import pytest
import training_inp_params_to_dict
import numpy as np


@pytest.mark.parametrize("rel_on_time_factors, flux_norm_factors, flux_files, exp_training_inp_info", [
    (
    np.array([2, 4]),
    np.array([1, 0.3]),
    np.array(['../iter_flux', '../frascati_flux']),
    np.array([
        [
            [
            None,
            None
            ],

            [
            (2, 0.3, '../iter_flux'),
      
      (2, 0.3, '../frascati_flux')
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
      ], dtype=object)
     )
     ])

def test_make_flux_tirr_combos(rel_on_time_factors, flux_norm_factors, flux_files, exp_training_inp_info):
    obs_training_inp_info = training_inp_params_to_dict.make_flux_tirr_combos(rel_on_time_factors, flux_norm_factors, flux_files)
    assert np.array_equal(obs_training_inp_info, exp_training_inp_info)

@pytest.mark.parametrize("training_inp_info, min_on_times, time_unit, exp_training_child_dicts", [
    (
    np.array([
        [
            [
            None,
            None
            ],

            [
            (2, 0.3, '../iter_flux'),
      
      (2, 0.3, '../frascati_flux')
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
    [1, 2],
    'y',
    np.array([
        [
        [
            [
            None,
            None
            ],

            [
            {'type': 'pulse_entry',
      'pulse_length' : 2,
      'pulse_length_unit': 'y',
      'flux_filepath' : '../iter_flux',
      'flux_norm' : 0.3,
      'pulse_history': [(1, 0, 's')],
      'delay_dur' : 0.0,
      'delay_dur_unit' : 's'},
      
      {'type': 'pulse_entry',
      'pulse_length' : 2,
      'pulse_length_unit': 'y',
      'flux_filepath' : '../frascati_flux',
      'flux_norm' : 0.3,
      'pulse_history': [(1, 0, 's')],
      'delay_dur' : 0.0,
      'delay_dur_unit' : 's'}
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
            {'type': 'pulse_entry',
      'pulse_length' : 4,
      'pulse_length_unit': 'y',
      'flux_filepath' : '../iter_flux',
      'flux_norm' : 0.3,
      'pulse_history': [(1, 0, 's')],
      'delay_dur' : 0.0,
      'delay_dur_unit' : 's'},
      
      {'type': 'pulse_entry',
      'pulse_length' : 4,
      'pulse_length_unit': 'y',
      'flux_filepath' : '../frascati_flux',
      'flux_norm' : 0.3,
      'pulse_history': [(1, 0, 's')],
      'delay_dur' : 0.0,
      'delay_dur_unit' : 's'}
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
    ])
     )
     ])


def test_write_training_params_dict(training_inp_info, min_on_times, time_unit, exp_training_child_dicts):
    obs_training_child_dicts = training_inp_params_to_dict.write_training_params_dict(training_inp_info, min_on_times, time_unit)
    assert np.array_equal(obs_training_child_dicts, exp_training_child_dicts)