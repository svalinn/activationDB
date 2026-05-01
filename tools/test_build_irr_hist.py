import build_irr_hist
import pytest

def normalize_lines(lines):
    '''
    Ignore differences in indentation and formatting when running a pytest.
    '''
    return [" ".join(line.split()) for line in lines.splitlines() if line.strip()]

@pytest.mark.parametrize("child_dicts, counter, exp_ph_dict", [
    ([{
        'type':
        'schedule',
        'children': [
            {
                'type': 'pulse_entry',
                'pulse_length': 7.6,
                'pulse_length_unit': 'm',
                'flux_name': 'flux_1',
                'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
                'delay_dur': 5.1,
                'delay_dur_unit': 's'
            }, {
                'type': 'pulse_entry',
                'pulse_length': 7.6,
                'pulse_length_unit': 's',
                'flux_name': 'flux_2',
                'pulse_history': [(1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')],
                'delay_dur': 5.8,
                'delay_dur_unit': 'm'
            }
        ],
        'flux_name':
        'flux_4',
        'pulse_history': [(7, 9.5, 'd'), (3, 2.3, 'y')],
        'delay_dur':
        6.3,
        'delay_dur_unit':
        'm'
    }, {
        'type': 'pulse_entry',
        'pulse_length': 7.4,
        'pulse_length_unit': 'd',
        'flux_name': 'flux_3',
        'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
        'delay_dur': 5.33,
        'delay_dur_unit': 'c'
    }], None, {
        'pulse_history_1': [(7, 9.5, 'd'), (3, 2.3, 'y')],
        'pulse_history_2': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
        'pulse_history_3': [(1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')],
        'pulse_history_4': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')]
    })
])

def test_make_ph_dict(child_dicts, counter, exp_ph_dict):
    obs_ph_dict = build_irr_hist.make_ph_dict(child_dicts, counter)
    assert obs_ph_dict == exp_ph_dict

@pytest.mark.parametrize("ph_dict, exp_ph_block", [
    ({
        'pulse_history_1': [(7, 9.5, 'd'), (3, 2.3, 'y')],
        'pulse_history_2': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
        'pulse_history_3': [(1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')]
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
    obs_ph_block = build_irr_hist.make_pulse_history_block(ph_dict)
    assert normalize_lines(obs_ph_block) == normalize_lines(exp_ph_block)

@pytest.mark.parametrize("child_dicts, ph_dict, counter, sched_name, exp_sched_block", [
    ([{
        'type':
        'schedule',
        'children': [
            {
                'type': 'pulse_entry',
                'pulse_length': 7.6,
                'pulse_length_unit': 'm',
                'flux_name': 'flux_1',
                'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
                'delay_dur': 5.1,
                'delay_dur_unit': 's'
            }, {
                'type': 'pulse_entry',
                'pulse_length': 7.6,
                'pulse_length_unit': 's',
                'flux_name': 'flux_2',
                'pulse_history': [(1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')],
                'delay_dur': 5.8,
                'delay_dur_unit': 'm'
            }
        ],
        'flux_name':
        'flux_4',
        'pulse_history': [(7, 9.5, 'd'), (3, 2.3, 'y')],
        'delay_dur':
        6.3,
        'delay_dur_unit':
        'm'
    }, {
        'type': 'pulse_entry',
        'pulse_length': 7.4,
        'pulse_length_unit': 'd',
        'flux_name': 'flux_3',
        'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
        'delay_dur': 5.33,
        'delay_dur_unit': 'c'
    }],
    {
        'pulse_history_1': [(7, 9.5, 'd'), (3, 2.3, 'y')],
        'pulse_history_2': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
        'pulse_history_3': [(1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')]
    },
    None,
    "top",
    """schedule top
        sched_1	flux_4	6.3	m
        7.4	d	flux_3	pulse_history_2	5.33	c
    end

    schedule sched_1
        7.6	m	flux_1	pulse_history_2	5.1	s
        7.6	s	flux_2	pulse_history_3	5.8	m
    end""")
    ])    

def test_make_schedule_block(child_dicts, ph_dict, counter, sched_name, exp_sched_block):
    obs_sched_block = build_irr_hist.make_schedule_block(child_dicts, ph_dict, counter, sched_name)
    assert normalize_lines(obs_sched_block) == normalize_lines(exp_sched_block)