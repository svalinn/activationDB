import string
from itertools import count
"""
The following data structure (child_dicts) is
an iterable of dictionaries, where each dictionary contains the details
of a schedule entry or a pulse entry. In the case of a schedule entry,
the value of the "children" key is a dictionary that follows the same format
as its parent.
[
{'type': 'schedule',
    'children': [{...}],
    'flux_name' : (str),
    'pulse_history': (iterable of (int, float, str)),
    'delay_dur': (float),
    'delay_dur_unit': (str)
},

{'type': 'pulse_entry',
    'pulse_length': (float),
    'pulse_length_unit': (str),
    'flux_name' : (str),
    'pulse_history': (iterable of (int, float, str)),
    'delay_dur' : (float),
    'delay_dur_unit': (str)
}
]
"""

def make_ph_dict(child_dicts, counter=None):
    '''
    Create a dictionary where the key is the name of the pulse history,
    and the value is a tuple corresponding to the 
    number of pulses, pulse dwell time, and the unit of the dwell time.
    Each pulse history in the dictionary is unique.
    '''
    if counter is None:
        counter = count(1)

    ph_dict = {}

    for entry in child_dicts:
        ph_dict[f'pulse_history_{next(counter)}'] = entry['pulse_history']

        if entry['type'] == 'schedule':
            ph_dict |= make_ph_dict(entry['children'], counter)

    return ph_dict


def make_pulse_history_block(ph_dict):
    '''
    Creates the lines comprising the pulse history block of an ALARA input file.
    '''
    ph_template_string = """pulsehistory  $ph_name
    $ph_lines
    end
    """
    template_obj = string.Template(ph_template_string)

    all_ph_lines = ""
    for ph_name in ph_dict:
        ph_iter = ph_dict[ph_name]
        ph_lines = ""
        for entry in ph_iter:
            ph_lines += (f'{entry[0]}\t' + f'{entry[1]}\t' + f'{entry[2]}' +
                         '\n')
        child_lines = template_obj.substitute(ph_name=ph_name, ph_lines=ph_lines)
        all_ph_lines += child_lines
    return all_ph_lines

def make_schedule_block(child_dicts, ph_dict, counter=None, sched_name="top"):
    '''
    Creates the lines comprising the schedule block of an ALARA input file.
    '''
    if counter is None:
        counter = count(1)
    top_sched_template_string = """schedule $sched_name
    $sched_lines
    end
    """
    current_sched_lines = ""
    child_lines = ""
    top_sched_temp_obj = string.Template(top_sched_template_string)

    for entry in child_dicts:
        if entry['type'] == 'pulse_entry':
            current_sched_lines += (
                f"{entry['pulse_length']}\t"
                f"{entry['pulse_length_unit']}\t"
                f"{entry['flux_name']}\t"
                + next(ph_name for ph_name, hist in ph_dict.items()
                       if entry['pulse_history'] == hist) + "\t"
                f"{entry['delay_dur']}\t"
                f"{entry['delay_dur_unit']}\n"
            )

        elif entry['type'] == 'schedule':
            child_name = f"sched_{next(counter)}"

            current_sched_lines += (
                f"{child_name}\t"
                f"{entry['flux_name']}\t"
                f"{entry['delay_dur']}\t"
                f"{entry['delay_dur_unit']}\n"
            )
            child_block = make_schedule_block(
                entry['children'],
                ph_dict,
                counter,
                sched_name=child_name
            )

            child_lines += child_block

    current_sched_lines = top_sched_temp_obj.substitute(
        sched_name=sched_name,
        sched_lines=current_sched_lines
    )
    return current_sched_lines + child_lines