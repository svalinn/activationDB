import pytest
import testing_case_inp_params_to_dict as tcipd
import numpy as np

@pytest.mark.parametrize("num_pulses, dwell_time, dwell_time_unit, min_on_time, rel_on_time_factors, " \
                        "flux_norm_factors, flux_files, pulse_length_unit, exp_testing_child_dicts", [
    (
    5,
    10,
    'm',
    1,
    np.array([2, 4]),
    np.array([1, 0.3]),
    np.array(['../iter_flux', '../frascati_flux']),
    'y',
    np.array([
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
      'pulse_history': [(5, 10, 'm')],
      'delay_dur' : 0.0,
      'delay_dur_unit' : 's'},
      
      {'type': 'pulse_entry',
      'pulse_length' : 2,
      'pulse_length_unit': 'y',
      'flux_filepath' : '../frascati_flux',
      'flux_norm' : 0.3,
      'pulse_history': [(5, 10, 'm')],
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
      ])
     )
     ])

def test_write_testing_params_dict(num_pulses, dwell_time, dwell_time_unit, min_on_time,
                                   rel_on_time_factors, flux_norm_factors, flux_files, pulse_length_unit, exp_testing_child_dicts):
    obs_testing_child_dicts = tcipd.write_testing_params_dict(num_pulses, dwell_time, dwell_time_unit, 
                                                                                   min_on_time, rel_on_time_factors, flux_norm_factors, 
                                                                                   flux_files, pulse_length_unit)
    assert np.array_equal(obs_testing_child_dicts, exp_testing_child_dicts)