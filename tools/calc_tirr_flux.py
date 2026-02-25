import numpy as np
import argparse
import sys
import os

def search_for_match(top_dict, search_str):
    '''
    Takes a nested top dictionary and searches all sub-dictionaries for matches with a provided string.
    '''
    matches = []
    for key, value in top_dict.items():
        if key.startswith(search_str):
            matches.append(value)
        elif isinstance(value, dict):
            match_res = search_for_match(value, search_str)
            matches.extend(match_res)
    return matches

def process_out_params(spp, lines): #imaginary lines for now
    pulse_dict = spp.read_pulse_histories(lines)
    sch_dict = spp.make_nested_dict(lines)
    
    pulse_length = search_for_match(sch_dict, "pe_dur")
    num_pulses = search_for_match(pulse_dict, "num_pulses_all_levels")
    dwell_time = search_for_match(pulse_dict, "delay_seconds_all_levels")
    return pulse_length, num_pulses, dwell_time
    
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--spp_path', '-s', required=True, help="Path (str) to folder containing sched_post_processor.py")
    arg = parser.parse_args()
    return arg

def main():
    arg = parse_args()
    spp_path = arg.spp_path
    sys.path.insert(0, spp_path)
    import sched_post_processor as spp
    pulse_length, num_pulses, dwell_time = process_out_params(spp, lines)
    t_irr_flat = pulse_length * num_pulses + dwell_time * (num_pulses - 1)
    #total flux = imaginary flux summed over all energy bins
    avg_flux_flat = total_flux / t_irr_flat 

if __name__ == "__main__":
    main()