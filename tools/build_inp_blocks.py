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
    'pulse_history': (iterable of (int, float, str)),
    'delay_dur': (float),
    'delay_dur_unit': (str)
},

{'type': 'pulse_entry',
    'pulse_length': (float),
    'pulse_length_unit': (str),
    'flux_filepath' : (str),
    'flux_norm' : (float),
    'pulse_history': (iterable of (int, float, str)),
    'delay_dur' : (float),
    'delay_dur_unit': (str)
}
]
"""


def make_ph_dict(child_dicts, ph_counter=None):
    '''
    Create a dictionary where the key is an iterable of tuples, with each tuple containing
    the number of pulses (int), pulse dwell time (float), and the unit of the dwell time (str).
    The value is a name assigned to the pulse history.
    Each unique pulse history tuple maps to a single pulse history name.
    '''
    if ph_counter is None:
        ph_counter = count(1)

    ph_dict = {}

    for child_dict in child_dicts:
        ph_dict[tuple(
            child_dict['pulse_history'])] = f'pulse_history_{next(ph_counter)}'

        if child_dict['type'] == 'schedule':
            ph_dict |= make_ph_dict(child_dict['children'], ph_counter)

    return ph_dict


def make_flux_dict(child_dicts, flux_counter=None):
    if flux_counter is None:
        flux_counter = count(1)
    flux_dict = {}
    for child_dict in child_dicts:
        if child_dict['type'] == 'pulse_entry':
            flux_dict[
                (child_dict['flux_filepath'], child_dict['flux_norm'])] = f'flux_{next(flux_counter)}'
        elif child_dict['type'] == 'schedule':
            flux_dict |= make_flux_dict(child_dict['children'], flux_counter)

    return flux_dict


def make_flux_block(flux_dict):
    '''
    Create the flux block of an ALARA input file.
    '''
    flux_lines = ""
    for (flux_path, flux_norm), flux_name in flux_dict.items():
        flux_lines += f"flux {flux_name} {flux_path} {flux_norm} 0 default\n"
    return flux_lines + "\n"


def make_pulse_history_block(ph_dict):
    '''
    Creates the lines comprising the pulse history block of an ALARA input file.
    '''

    all_ph_lines = ""
    for ph_list, ph_name in ph_dict.items():
        ph_lines = ""
        for level in ph_list:
            ph_lines += '\t'.join([str(e) for e in level]) + '\n'
        all_ph_lines += f"pulsehistory {ph_name}\n{ph_lines}\nend\n"
    return all_ph_lines + "\n"


def make_schedule_block(child_dicts, ph_dict, flux_dict, sched_counter=None, sched_name="top"):
    '''
    Creates the lines comprising the schedule block of an ALARA input file.
    '''
    if sched_counter is None:
        sched_counter = count(1)
    current_sched_lines = ""
    child_lines = ""

    for child_dict in child_dicts:
        if child_dict['type'] == 'pulse_entry':
            current_sched_lines += (
                f"{child_dict['pulse_length']}\t"
                f"{child_dict['pulse_length_unit']}\t"
                f"{flux_dict[(child_dict['flux_filepath'], child_dict['flux_norm'])]}\t"
                f"{ph_dict[tuple(child_dict['pulse_history'])]}\t"
                f"{child_dict['delay_dur']}\t"
                f"{child_dict['delay_dur_unit']}\n"
            )

        elif child_dict['type'] == 'schedule':
            child_name = f"sched_{next(sched_counter)}"

            current_sched_lines += (
                f"{child_name}\t"
                f"{ph_dict[tuple(child_dict['pulse_history'])]}\t"
                f"{child_dict['delay_dur']}\t"
                f"{child_dict['delay_dur_unit']}\n"
            )
            child_block = make_schedule_block(
                child_dict['children'],
                ph_dict,
                flux_dict,
                sched_counter,
                sched_name=child_name
            )

            child_lines += child_block

    current_sched_lines = f"schedule {sched_name}\n{current_sched_lines}\nend\n"
    all_sched_lines = current_sched_lines + child_lines
    return all_sched_lines


def read_nuclib(nuclib="nuclib.std"):
    nuclib_lines = open(
        nuclib, 'r').readlines()
    return nuclib_lines

def make_volume_block(nuclib_lines, volume):
    vol_lines = "volume\n"
    load_lines = "mat_loading\n"
    mix_lines = ""
    for line in nuclib_lines:
        line = line.strip().split()
        nuc = line[0]
        if ':' in nuc:
            vol_lines += f'\t {volume}\t{nuc}\n'
            load_lines += f'\t{nuc}\t mix_{nuc}\n'
            mix_lines += f'mixture mix_{nuc}\n\t element {nuc} 1 1.0 \nend \n'
    return vol_lines + "end\n", load_lines + "end\n", mix_lines


def make_input_lines(vol_lines, load_lines, mix_lines, flux_lines, all_ph_lines, all_sched_lines,
                     trunc_tolerance):
    """
    Collect volume, loading, and mixture blocks from make_volume_block().
    Assemble with data and output block-related lines that are expected to change infrequently.
    Finally combine with flux, schedule, and ph blocks, along with truncation tolerance.
    Write all lines to a file.
    :param: trunc_tolerance (float)
    :param: input_filename (str)
    :param: nuclib (str, path to ALARA nuclide library)
    """
    data_output_lines = """material_lib matlib.sample
    element_lib elelib.std
    data_library alaralib fendl2bin

    output zone
        specific_activity
        number_density
    end
    """
    assembled_lines = "geometry rectangular\n" + vol_lines + load_lines + mix_lines + data_output_lines \
                    + "\n" + flux_lines + all_sched_lines + "\n" + all_ph_lines + f"truncation {trunc_tolerance}"
    return assembled_lines


def write_inp_file(assembled_lines, input_filename):
    with open(input_filename, 'w') as new_inp:
        new_inp.write(assembled_lines)
