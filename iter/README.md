# README for ITER Activation Comparisons

This directory runs activation calculations for Be and W, two proposed ITER first wall materials, with ITER flux spectra provided by FISPACT [[1]](#1).

These calculations are broken up into a series of 2, 4, 8, 32, and 64 pulses, with duty cycles of 100% (steady-state), 90%, 50%, and 25%. These duty cycles
have the effect of increasing the dwell time between successive pulses, while the pulse length is only a function of the number of pulses and the total burn time.
For these calculations, the total active burn time is 4 years. The table below summarizes the dwell times as a function of duty cycle and total number of pulses.

| # Pulses | 90% | 50% | 25% |
| ---------|-----|-----|-----|
|  2 | 0.222 | 2 | 6 |
|  4 | 0.111 | 1 | 3 |
|  8 | 0.056 | 0.5 | 1.5 |
| 32 | 0.01389 | 0.125 | 0.375 |
| 64 | 0.006944 | 0.0625 | 0.1875 |

## References
<a id="1">[1]</a>
https://fispact.ukaea.uk/wiki/Reference_input_spectra (accessed Nov. 24, 2025).
