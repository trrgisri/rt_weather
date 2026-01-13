#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file thies_lpm.py
@brief Record observation data of Thies LPM

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2025 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import sys

#from emulated_srs_py.weather.thies_lpm import ThiesLPM
from rt_weather.instruments.thies_lpm import ThiesLPM

# %%
if __name__ == '__main__':

    args = sys.argv

    device_name = "/dev/ttyUSB1"
    log_dir = "./Weather"

    def print_usage():
        print('Usage: thies_lpm.py [-h] [port]')
        print(f'  port:    serial port (\"{device_name}\" default)')
        print('  -h       print this')

    if '-h' in args:
        print_usage()
        sys.exit(0)

    if len(args) == 2:
        try:
            device_name = args[1]
        except(IndexError, ValueError):
            print_usage()
            sys.exit(1)

    lpm = ThiesLPM(device_name)

    lpm.record(log_directory=log_dir)
