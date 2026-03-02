import pytest
import schedule_transforms as st

@pytest.mark.parametrize( "pulse_length,num_pulses,dwell_time,exp_tirr,exp_ff",
                          [
                            (1, 1, 1, 1, 1),
                            (1, 2, 1, 3, 2/3),
                            (2, 4, 6, 26, 8/26)                              
                          ])
def test_single_pulse_history(pulse_length, num_pulses, dwell_time, exp_tirr, exp_ff):
    obs_tirr, obs_ff = st.flatten_pulse_history(pulse_length, num_pulses, dwell_time)

    assert obs_tirr == exp_tirr
    assert obs_ff == exp_ff

@pytest.mark.parametrize( "pulse_length,num_tot_pulses,dwell_time,num_final_pulses,exp_tirr,exp_ff",
                          [
                            (1, 5, 2, 1, 10, 4/10),
                            (5, 5, 1, 1, 23, 20/23),
                            (5, 5, 1, 3, 11, 10/11)                              
                          ])
def test_flatten_ph_exact_pulses(pulse_length, num_tot_pulses, dwell_time, num_final_pulses, exp_tirr, exp_ff):
    obs_tirr, obs_ff = st.flatten_ph_exact_pulses(pulse_length, num_tot_pulses, dwell_time, num_final_pulses)

    assert obs_tirr == exp_tirr
    assert obs_ff == exp_ff
@pytest.mark.parametrize( "pulse_length,num_pulses,exp_tirr",
                          [
                            (1, 1, 1),
                            (1, 2, 2),
                            (10, 5, 50)                              
                          ])
def test_compress_pulse_history(pulse_length, num_pulses, exp_tirr):
    obs_tirr = st.compress_pulse_history(pulse_length, num_pulses)

    assert obs_tirr == exp_tirr

@pytest.mark.parametrize( "pulse_length,nums_pulses,dwell_times,exp_tot_tirr,exp_tot_ff",
                          [
                            (1, [1,1], [1,1], 1, 1),
                            (1, [2,2], [1,2], 8, 4/8),
                            (2, [1,2], [2,2], 6, 4/6)                              
                          ])
def test_flatten_ph_levels(pulse_length, nums_pulses, dwell_times, exp_tot_tirr, exp_tot_ff):
    obs_tot_tirr, obs_tot_ff = st.flatten_ph_levels(pulse_length, nums_pulses, dwell_times)

    assert obs_tot_tirr == exp_tot_tirr
    assert obs_tot_ff == exp_tot_ff

@pytest.mark.parametrize( "pulse_length,nums_pulses,exp_tot_tirr",
                          [
                            (1, [1,1], 1),
                            (1, [2,2], 4),
                            (2, [5,7], 70)                              
                          ])
def test_compress_ph_levels(pulse_length, nums_pulses, exp_tot_tirr):
    obs_tot_tirr = st.compress_ph_levels(pulse_length, nums_pulses)

    assert obs_tot_tirr == exp_tot_tirr


@pytest.mark.parametrize( "pulse_lengths,sched_dwell_times, nums_pulses,ph_dwell_times,exp_tot_sched_tirr,exp_tot_sched_ff",
                          [
                            ([1], [1], [1,1], [1,1], 1, 1),
                            ([2,2], [2,2], [2,2], [2,2], 30, 16/30),
                            ([1,1], [10,10], [2,2], [1,2], 26, 8/26)
                          ])
def test_calc_simple_sched_flattened_params(pulse_lengths, sched_dwell_times, nums_pulses, ph_dwell_times, exp_tot_sched_tirr,exp_tot_sched_ff):
    obs_tot_sched_tirr, obs_tot_sched_ff = st.calc_simple_sched_flattened_params(pulse_lengths, sched_dwell_times, nums_pulses, ph_dwell_times)
    
    assert obs_tot_sched_tirr == exp_tot_sched_tirr
    assert obs_tot_sched_ff == exp_tot_sched_ff
