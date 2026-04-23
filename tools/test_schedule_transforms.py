import pytest
import schedule_transforms as st

@pytest.mark.parametrize( "pulse_length,pulse_history,exp_dur,exp_fluence",
                          [
                            (1, (1, 1), 1, 1),
                            (1, (2, 1), 3, 2),
                            (2, (4, 6), 26, 8)
                          ])
def test_single_pulse_history(pulse_length, pulse_history, exp_dur, exp_fluence):
    obs_dur, obs_fluence = st.flatten_pulse_history(pulse_length, pulse_history)

    assert obs_dur == exp_dur
    assert obs_fluence == exp_fluence

@pytest.mark.parametrize( "pulse_length,pulse_history,num_final_pulses,exp_dur,exp_fluence",
                          [
                            (1, (5, 2), 1, 10, 4),
                            (5, (5, 1), 1, 23, 20),
                            (5, (5, 1), 3, 11, 10)
                          ])
def test_flatten_ph_exact_pulses(pulse_length, pulse_history, num_final_pulses, exp_dur, exp_fluence):
    obs_dur, obs_fluence = st.flatten_ph_exact_pulses(pulse_length, pulse_history, num_final_pulses)

    assert obs_dur == exp_dur
    assert obs_fluence == exp_fluence

@pytest.mark.parametrize( "pulse_length,pulse_history,exp_dur",
                          [
                            (1, (1, 1), 1),
                            (1, (2, 2), 2),
                            (10, (5, 5), 50)
                          ])
def test_compress_pulse_history(pulse_length, pulse_history, exp_dur):
    obs_dur = st.compress_pulse_history(pulse_length, pulse_history)

    assert obs_dur == exp_dur

@pytest.mark.parametrize( "pulse_length,pulse_history,exp_tot_dur,exp_tot_fluence",
                          [
                            (1, [(1,1), (1,1)], 1, 1),
                            (1, [(2,1), (2,2)], 8, 4),
                            (2, [(1,2), (2,2)], 6, 4)
                          ])
def test_flatten_ph_levels(pulse_length, pulse_history, exp_tot_dur, exp_tot_fluence):
    obs_tot_dur, obs_tot_fluence = st.flatten_ph_levels(pulse_length, pulse_history)

    assert obs_tot_dur == exp_tot_dur
    assert obs_tot_fluence == exp_tot_fluence

@pytest.mark.parametrize( "pulse_length,pulse_history,exp_tot_dur",
                          [
                            (1, [(1,1), (1,1)], 1),
                            (1, [(2,2), (2,2)], 4),
                            (2, [(5,5), (7,7)], 70)
                          ])
def test_compress_ph_levels(pulse_length, pulse_history, exp_tot_dur):
    obs_tot_dur = st.compress_ph_levels(pulse_length, pulse_history)

    assert obs_tot_dur == exp_tot_dur

class Test_Flattened_Compressed:
    common_args = ("child_dicts, pulse_history, exp_fluence",
                          [
                            ([
                                {
                                'type': 'schedule',
                                'pulse_history':[(1,1)],
                                'delay_dur': 1,
                                'children':
                                    [
                                    {'type': 'pulse_entry',
                                    'pulse_length': 1,
                                    'pulse_history':[(1,1)],
                                    'delay_dur' : 1
                                    },

                                    {'type': 'pulse_entry',
                                    'pulse_length': 1,
                                    'pulse_history':[(1,1)],
                                    'delay_dur' : 1
                                    }
                                    ]
                               }
                            ],

                               [(1,0)],
                               2),

                            ([
                                {
                                'type': 'schedule',
                                'pulse_history':[(1,1)],
                                'delay_dur': 5,
                                'children':
                                    [
                                    {'type': 'pulse_entry',
                                    'pulse_length': 10,
                                    'pulse_history':[(1,1)],
                                    'delay_dur' : 20
                                    },

                                    {'type': 'pulse_entry',
                                    'pulse_length': 2,
                                    'pulse_history':[(1,1)],
                                    'delay_dur' : 10
                                    },

                                    {'type': 'schedule',
                                    'pulse_history':[(1,1)],
                                    'delay_dur': 2,
                                    'children':
                                        [
                                        {'type': 'pulse_entry',
                                        'pulse_length': 5,
                                        'pulse_history':[(1,1)],
                                        'delay_dur' : 10
                                        }
                                        ]
                                    },
                                    {'type': 'schedule',
                                    'pulse_history':[(1,1)],
                                    'delay_dur': 2,
                                    'children':
                                        [
                                        {'type': 'pulse_entry',
                                        'pulse_length': 5,
                                        'pulse_history':[(1,1)],
                                        'delay_dur' : 3
                                        }
                                        ]
                                    }

                                    ]
                                }
                               ],

                               [(1,0)],
                               22),

                            ([
                                {
                                'type': 'schedule',
                                'delay_dur': 1,
                                'pulse_history': [(2,0)],
                                'children':
                                    [
                                    {'type': 'pulse_entry',
                                    'pulse_length': 1,
                                    'pulse_history': [(2,0)],
                                    'delay_dur' : 1
                                    }
                                    ]
                                },
                               ],

                               [(1,0)],
                               4),

                            ([
                                {
                                'type': 'schedule',
                                'delay_dur': 1,
                                'pulse_history': [(2,0)],
                                'children':
                                    [
                                    {'type': 'pulse_entry',
                                    'pulse_length': 1,
                                    'pulse_history': [(2,0)],
                                    'delay_dur' : 1
                                    }
                                    ],
                                },
                                {   
                                'type': 'schedule',
                                'delay_dur': 1,
                                'pulse_history': [(2,0)],
                                'children':
                                    [
                                    {'type': 'pulse_entry',
                                    'pulse_length': 1,
                                    'pulse_history': [(2,0)],
                                    'delay_dur' : 1
                                    }
                                    ],
                                },
                               ],

                               [(1,0)],
                               8),

                          ])
    durations = [3, 54, 4, 9]
    @pytest.mark.parametrize("child_dicts, pulse_history, exp_fluence, exp_dur",
                             [
                                (*args, dur) for args, dur in zip(common_args[1], durations)
                             ])
    def test_flatten_schedule(self, child_dicts, pulse_history,
                            exp_fluence, exp_dur):
        obs_dur, obs_fluence = st.flatten_schedule(child_dicts, pulse_history)

        assert obs_dur == pytest.approx(exp_dur)
        assert obs_fluence == pytest.approx(exp_fluence)

    @pytest.mark.parametrize(*common_args)
    def test_compress_schedule(self, child_dicts, pulse_history,
                           exp_fluence):
        obs_dur = st.compress_schedule(child_dicts, pulse_history)

        assert obs_dur == pytest.approx(exp_fluence)