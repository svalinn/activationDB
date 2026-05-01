import string
import uuid
"""
The following data structure (hereafter referred to as child_dicts) is
an iterable of dictionaries, where each dictionary contains the details
of a schedule entry or a pulse entry. In the case of a schedule entry,
the value of the "children" key is a dictionary that follows the same format
as its parent.
[
{'type': 'schedule',
    'children': [{...}],
    'flux_name' : (str)
    'pulse_history': (iterable of (int, float, str)),
    'delay_dur': (float),
},

{'type': 'pulse_entry',
    'pulse_length': (float),
    'flux_name' : (str)
    'pulse_history': (iterable of (int, float, str)),
    'delay_dur' : (float)
}
]
"""


def make_ph_dict(child_dicts, counter=1):
    ph_dict = {}
    for entry in child_dicts:
        ph_dict[f'pulse_history_{counter}'] = entry['pulse_history']
        counter += 1
        if entry['type'] == 'schedule':
            child_ph_dict = make_ph_dict(entry['children'], counter)
            ph_dict |= child_ph_dict
        else:
            continue
    return ph_dict


def make_pulse_history_block(ph_dict):
    ph_template_string = """pulsehistory  $ph_name
    $ph_lines
    end
    """
    template_obj = string.Template(ph_template_string)

    all_lines = ""
    for ph_name in ph_dict:
        ph_iter = ph_dict[ph_name]
        ph_lines = ""
        for entry in ph_iter:
            ph_lines += (f'{entry[0]}\t' + f'{entry[1]}\t' + f'{entry[2]}' +
                         '\n\t') #causes minor formatting issues
        child_lines = template_obj.substitute(ph_name=ph_name, ph_lines=ph_lines)
        all_lines += child_lines
    with open('pulse_history', 'w') as new_inp:
        new_inp.write(all_lines)

def make_schedule_block(child_dicts, ph_dict, counter=1, sched_name="top"):
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
                f"{entry['delay_dur_unit']}\n\t"
            )

        elif entry['type'] == 'schedule':
            child_name = f"sched_{counter}"

            current_sched_lines += (
                f"{child_name}\t"
                f"{entry['flux_name']}\t"
                f"{entry['delay_dur']}\t"
                f"{entry['delay_dur_unit']}\n\t"
            )
            child_block = make_schedule_block(
                entry['children'],
                ph_dict,
                counter + 1,
                sched_name=child_name
            )

            child_lines += child_block
            counter += 1

    current_block = top_sched_temp_obj.substitute(
        sched_name=sched_name,
        sched_lines=current_sched_lines
    )
    return current_block + child_lines   

def main():
    child_dicts = [{
        'type':
        'schedule',
        'children': [{
            'type':
            'pulse_entry',
            'pulse_length':
            7.6,
            'pulse_length_unit' : 'm',
            'flux_name' : 'flux_1',
            'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
            'delay_dur':
            5.1,
            'delay_dur_unit' : 's'

        }, {
            'type':
            'pulse_entry',
            'pulse_length':
            7.6,
            'pulse_length_unit' : 's',
            'flux_name' : 'flux_2',
            'pulse_history': [(1, 8.0, 'm'), (2, 3, 's'), (9, 1.1, 'c')],
            'delay_dur':
            5.8,
            'delay_dur_unit' : 'm'
        }],
        'flux_name' : 'flux_4',
        'pulse_history': [(7, 9.5, 'd'), (3, 2.3, 'y')],
        'delay_dur':
        6.3,
        'delay_dur_unit' : 'm'
    }, {
        'type':
        'pulse_entry',
        'pulse_length':
        7.4,
        'pulse_length_unit' : 'd',
        'flux_name' : 'flux_3',
        'pulse_history': [(3, 7.9, 'm'), (2, 5.5, 's'), (9, 1.2, 'c')],
        'delay_dur':
        5.33,
        'delay_dur_unit' : 'c'
    }]
    ph_dict = make_ph_dict(child_dicts)
    make_pulse_history_block(ph_dict)
    child_lines = make_schedule_block(child_dicts, ph_dict, counter = 1, sched_name = "top")
    with open(f'sched_history', 'w') as new_inp:
        new_inp.write(child_lines)
    

if __name__ == '__main__':
    main()
