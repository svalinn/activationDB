def flatten_pulse_history(pulse_length, num_pulses, dwell_time):
    """
    Apply the flux flattening approximation to a series of pulses.

    Consider a series of pulses of uniform magnitude and duration, separated by
    a dwell time with zero flux and a uniform duration.  The flux flattening
    approximation calculates an equivalent steady state flux magnitude that
    preserves both the total time between the beginning of the first pulse and
    the end of the last pulse, and the total fluence.

    :param pulse_length: (float) the duration of each pulse
    :param num_pulses: (int) the number of pulses
    :param dwell_time: (float) the duration of the gap between each pulse
    """
    t_irr_flat = (num_pulses-1) * (pulse_length + dwell_time) + pulse_length
    flux_factor_flat = num_pulses * pulse_length / t_irr_flat

    return t_irr_flat, flux_factor_flat

def compress_pulse_history(pulse_length, num_pulses):
    '''
    Applies the compression algorithm to a series of pulses. This algorithm
    preserves the total active irradiation time between the start of the first
    and end of the last pulse, and the total fluence.
    
    :param pulse_length: (float) the duration of each pulse
    :param num_pulses: (int) the number of pulses
    '''
    t_irr_comp = num_pulses * pulse_length

    return t_irr_comp


def flatten_ph_exact_pulses(pulse_length, num_tot_pulses, dwell_time,
                            num_final_pulses):
    '''
    Applies the flattening approximation to a series of pulses. Preserves an arbitrary
    number of final pulses, and the total amount of time elapsed between the 
    start of the first of the initial set of pulses and the end of the last. The
    set of final pulses is considered to be exact in duration and delay time as the initial set.

    :param pulse_length: (float) the duration of each initial pulse
    :param num_tot_pulses: (int) the total number of pulses (initial + final)
    :param dwell_time: (float) the duration of the gap between each initial pulse
    :param num_final_pulses: (int) the number of final pulses
    '''
    num_init_pulses = num_tot_pulses - num_final_pulses
    t_irr_flat_exact_pulses, ff_flat_exact_pulses = flatten_pulse_history(pulse_length, num_init_pulses, dwell_time)
    return t_irr_flat_exact_pulses, ff_flat_exact_pulses


def flatten_ph_levels(pulse_length, pulse_history):
    '''
    Apply the flattening algorithm to all levels of a multi-level pulsing history
    with a single-level schedule block.  
    
    :param pulse_length: active irradiation time from schedule block
    :param pulse_history : (iterable of (int, float))
    '''
    tot_ff_flat = 1
    tot_t_irr_flat = pulse_length
    for num_pulses, dwell_time in pulse_history:
        tot_t_irr_flat, ff = flatten_pulse_history(tot_t_irr_flat,
                                                   num_pulses,
                                                   dwell_time)
        tot_ff_flat *= ff
    return tot_t_irr_flat, tot_ff_flat


def flatten_schedule(child_dicts, pulse_history=[(1, 0)]):
    '''
    Calculate irradiation time and flux factor for a schedule containing an arbitrary number of pulse entries
    and/or sub-schedules.
    :param child_dicts: iterable of dictionaries, with the form:
    [
    {'type': 'schedule',
     'children': [{...}]
     'pulse_history': (iterable of (int, float)),
     'delay_dur': (float),
    },

    {'type': 'pulse_entry',
     'pulse_length': (float),
     'pulse_history': (iterable of (int, float)),
     'delay_dur' : (float)
    }
    ]
    It is possible for the value of the 'children' key at any level to consist entirely of pulse entries.
    '''
    t_irr = 0
    active_burn_time = 0
    for child_dict in child_dicts:
        if child_dict['type'] == 'schedule':
            child_tirr, child_ff = flatten_schedule(
                child_dict['children'],
                child_dict['pulse_history'])
        if child_dict['type'] == 'pulse_entry':
            child_tirr, child_ff = flatten_ph_levels(child_dict['pulse_length'],
                                               child_dict['pulse_history'])
        active_burn_time += child_tirr * child_ff
        t_irr += child_tirr + child_dict['delay_dur']
    t_irr -= child_dicts[-1]['delay_dur'] 
    ff = active_burn_time / t_irr

    t_irr, new_ff = flatten_ph_levels(
        t_irr,
        pulse_history)

    ff *= new_ff    

    return t_irr, ff


def compress_ph_levels(pulse_length, nums_pulses):
    '''
    Apply the compression algorithm to all levels of a multi-level pulsing history
    with a single-level schedule block.  
    
    :param pulse_lengths: active irradiation time from schedule block
    :param nums_pulses: (iterable) number of pulses at each level
    '''
    tot_t_irr_comp = pulse_length
    for num_pulses in nums_pulses:
        tot_t_irr_comp = compress_pulse_history(tot_t_irr_comp, num_pulses)
    return tot_t_irr_comp
