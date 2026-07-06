import build_inp_blocks
import pytest

def normalize_lines(lines):
    '''
    Ignore differences in indentation and formatting when running a pytest.
    '''
    return [" ".join(line.split()) for line in lines.splitlines() if line.strip()]

@pytest.mark.parametrize("child_dicts, ph_counter, exp_ph_dict", [
    ([{
        'type': 'schedule',
        'children': [
            {
                'type': 'pulse_entry',
                'pulse_length': 7.6,
                'pulse_length_unit': 'm',
                'flux_filepath': './ex_flux',
                'flux_norm' : 0.5,
                'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
                'delay_dur': 5.1,
                'delay_dur_unit': 's'
            }, {
                'type': 'pulse_entry',
                'pulse_length': 7.6,
                'pulse_length_unit': 's',
                'flux_filepath': '../flux_file',
                'flux_norm' : 0.9,
                'pulse_history': [(1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')],
                'delay_dur': 5.8,
                'delay_dur_unit': 'm'
            }
        ],
        'pulse_history': [(7, 9.5, 'd'), (3, 2.3, 'y')],
        'delay_dur': 6.3,
        'delay_dur_unit': 'm'
    }, {
        'type': 'pulse_entry',
        'pulse_length': 7.4,
        'pulse_length_unit': 'd',
        'flux_filepath': './iter_flux',
        'flux_norm' : 1,
        'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
        'delay_dur': 5.33,
        'delay_dur_unit': 'c'
    }], 
    None, 
    {
        ((7, 9.5, 'd'), (3, 2.3, 'y')) : 'pulse_history_1',
        ((3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')): 'pulse_history_4',
        ((1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')) : 'pulse_history_3'
    })
])

def test_make_ph_dict(child_dicts, ph_counter, exp_ph_dict):
    obs_ph_dict = build_inp_blocks.make_ph_dict(child_dicts, ph_counter)
    assert obs_ph_dict == exp_ph_dict

@pytest.mark.parametrize("child_dicts, flux_counter, exp_flux_dict", [
    ([{
        'type': 'schedule',
        'children': [
            {
                'type': 'pulse_entry',
                'pulse_length': 7.6,
                'pulse_length_unit': 'm',
                'flux_filepath': './ex_flux',
                'flux_norm' : 0.7,
                'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
                'delay_dur': 5.1,
                'delay_dur_unit': 's'
            }, {
                'type': 'pulse_entry',
                'pulse_length': 7.6,
                'pulse_length_unit': 's',
                'flux_filepath': '../flux_file',
                'flux_norm' : 1,
                'pulse_history': [(1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')],
                'delay_dur': 5.8,
                'delay_dur_unit': 'm'
            }
        ],
        'pulse_history': [(7, 9.5, 'd'), (3, 2.3, 'y')],
        'delay_dur': 6.3,
        'delay_dur_unit': 'm'
    }, {
        'type': 'pulse_entry',
        'pulse_length': 7.4,
        'pulse_length_unit': 'd',
        'flux_filepath': '../flux_file',
        'flux_norm' : 0.6,
        'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
        'delay_dur': 5.33,
        'delay_dur_unit': 'c'
    }],
    None,
    {
        ('./ex_flux', 0.7) : 'flux_1',
        ('../flux_file', 1) : 'flux_2',
        ('../flux_file', 0.6) : 'flux_3'
    })
    ])

def test_make_flux_dict(child_dicts, flux_counter, exp_flux_dict):
    obs_flux_dict = build_inp_blocks.make_flux_dict(child_dicts, flux_counter)
    assert obs_flux_dict == exp_flux_dict

@pytest.mark.parametrize("flux_dict, exp_flux_block", [
    ({
        ('./ex_flux', 1) : 'flux_1',
        ('../flux_file', 2) : 'flux_3'
    },
    """
    flux flux_1 ./ex_flux 1 0 default
    flux flux_3 ../flux_file 2 0 default
    """
    )
    ])

def test_make_flux_block(flux_dict, exp_flux_block):
    obs_flux_block = build_inp_blocks.make_flux_block(flux_dict)
    assert normalize_lines(obs_flux_block) == normalize_lines(exp_flux_block)

@pytest.mark.parametrize("ph_dict, exp_ph_block", [
    ({
        ((7, 9.5, 'd'), (3, 2.3, 'y')): 'pulse_history_1',
        ((3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')): 'pulse_history_2',
        ((1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')): 'pulse_history_3'
    },
    """pulsehistory  pulse_history_1
        7	9.5	d
        3	2.3	y
    end
    pulsehistory  pulse_history_2
        3	7.9	m
        2	5.5	s
        9	1.2	c
    end
    pulsehistory  pulse_history_3
        1	8.0	m
        2	3	s
        9	1.1	c
    end""")
    ])

def test_make_pulse_history_block(ph_dict, exp_ph_block):
    obs_ph_block = build_inp_blocks.make_pulse_history_block(ph_dict)
    assert normalize_lines(obs_ph_block) == normalize_lines(exp_ph_block)

@pytest.mark.parametrize("child_dicts, ph_dict, flux_dict, sched_counter, sched_name, exp_sched_block", [
    ([{
        'type': 'schedule',
        'children': [
            {
                'type': 'pulse_entry',
                'pulse_length': 7.6,
                'pulse_length_unit': 'm',
                'flux_filepath': './iter_flux_2',
                'flux_norm' : 0.2,
                'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
                'delay_dur': 5.1,
                'delay_dur_unit': 's'
            }, {
                'type': 'pulse_entry',
                'pulse_length': 7.6,
                'pulse_length_unit': 's',
                'flux_filepath': '../frascati_flux_1',
                'flux_norm' : 5,
                'pulse_history': [(1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')],
                'delay_dur': 5.8,
                'delay_dur_unit': 'm'
            }
        ],
        'pulse_history': [(7, 9.5, 'd'), (3, 2.3, 'y')],
        'delay_dur': 6.3,
        'delay_dur_unit': 'm'
    }, {
        'type': 'pulse_entry',
        'pulse_length': 7.4,
        'pulse_length_unit': 'd',
        'flux_filepath': '../frascati_flux_1',
        'flux_norm' : 5,
        'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
        'delay_dur': 5.33,
        'delay_dur_unit': 'c'
    }],
    {
        ((7, 9.5, 'd'), (3, 2.3, 'y')): 'pulse_history_1',
        ((3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')): 'pulse_history_2',
        ((1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')): 'pulse_history_3'
    },
    {
        ('./iter_flux_2', 0.2) : 'flux_1',
        ('../frascati_flux_1', 5) : 'flux_3'
    },
    None,
    "top",
    """schedule top
        sched_1 pulse_history_1	6.3	m
        7.4	d	flux_3	pulse_history_2	5.33	c
    end

    schedule sched_1
        7.6	m	flux_1	pulse_history_2	5.1	s
        7.6	s	flux_3	pulse_history_3	5.8	m
    end""")
    ])

def test_make_schedule_block(child_dicts, ph_dict, flux_dict, sched_counter,
                             sched_name, exp_sched_block):
    obs_sched_block = build_inp_blocks.make_schedule_block(
        child_dicts, ph_dict, flux_dict, sched_counter, sched_name)
    assert normalize_lines(obs_sched_block) == normalize_lines(exp_sched_block)

@pytest.mark.parametrize("flux_lines, all_ph_lines, all_sched_lines, trunc_tolerance, nuclib_lines, exp_assembled_lines", [
    ("""
    flux flux_1 ./ex_flux 3 0 default
    flux flux_3 ../flux_file 0.3 0 default
    """,
    """pulsehistory  pulse_history_1
        7	9.5	d
        3	2.3	y
    end
    pulsehistory  pulse_history_2
        3	7.9	m
        2	5.5	s
        9	1.2	c
    end
    pulsehistory  pulse_history_3
        1	8.0	m
        2	3	s
        9	1.1	c
    end
    """,
    """schedule top
        sched_1 pulse_history_1	6.3	m
        7.4	d	flux_3	pulse_history_2	5.33	c
    end

    schedule sched_1
        7.6	m	flux_1	pulse_history_2	5.1	s
        7.6	s	flux_3	pulse_history_3	5.8	m
    end
    """,
    1e-05,
    ['h       0.100790E+01   1      0.899000E-04   2\n',
    '1      0.999850E+02\n',
    '2      0.150000E-01\n',
    'h:1   1.00783E+00   1   8.98933E-05 1\n',
    '1 100\n',
    'h:2   2.01410E+00   1   1.79649E-04 1\n',
    '2 100\n'
    ],
    """
    geometry rectangular
    volume
        1    h:1
        1    h:2
    end    
    mat_loading
        h:1 mix_h:1
        h:2 mix_h:2
    end
    mixture mix_h:1
        element h:1 1 1.0
    end
    mixture mix_h:2
        element h:2 1 1.0
    end
    material_lib matlib.sample
    element_lib elelib.std
    data_library alaralib fendl2bin

    output zone
        specific_activity
        number_density
    end
    flux flux_1 ./ex_flux 3 0 default
    flux flux_3 ../flux_file 0.3 0 default
    schedule top
        sched_1 pulse_history_1	6.3	m
        7.4	d	flux_3	pulse_history_2	5.33	c
    end

    schedule sched_1
        7.6	m	flux_1	pulse_history_2	5.1	s
        7.6	s	flux_3	pulse_history_3	5.8	m
    end
    pulsehistory  pulse_history_1
        7	9.5	d
        3	2.3	y
    end
    pulsehistory  pulse_history_2
        3	7.9	m
        2	5.5	s
        9	1.2	c
    end
    pulsehistory  pulse_history_3
        1	8.0	m
        2	3	s
        9	1.1	c
    end
    truncation 1e-05
    """
    )
    ])

def test_make_input_lines(flux_lines, all_ph_lines, all_sched_lines,
                          trunc_tolerance, nuclib_lines, exp_assembled_lines):
    vol_lines, load_lines, mix_lines = build_inp_blocks.make_volume_block(nuclib_lines, volume=1)
    obs_assembled_lines = build_inp_blocks.make_input_lines(
        vol_lines, load_lines, mix_lines, flux_lines, all_ph_lines, all_sched_lines, trunc_tolerance)
    assert normalize_lines(obs_assembled_lines) == normalize_lines(
        exp_assembled_lines)
