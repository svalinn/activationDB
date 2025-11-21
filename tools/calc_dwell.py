import numpy as np
from sympy import symbols, Eq, solve

duty_cycle_list = [1, 0.9, 0.5, 0.25]
num_pulses = [2, 4, 8, 32, 64]
# Only one total irradation time for now
tot_irr_time = 4 # years

dwell_time = symbols('dwell_time')
for duty_cycle in duty_cycle_list:
    for num in num_pulses:
        pulse_length = tot_irr_time / num
        eq_1 = Eq(pulse_length / (pulse_length + dwell_time), duty_cycle)
        solution = solve((eq_1),(dwell_time))
        print(f"duty_cycle={duty_cycle}, num={num}, dwell_time = {solution} y")