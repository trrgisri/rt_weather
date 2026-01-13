#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file pwd10.py
@brief Record observation data of Vaisala PWD10

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2025 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import sys

#from emulated_srs_py.weather.pwd10 import PWD10
from rt_weather.instruments.pwd10 import PWD10

# %%
if __name__ == '__main__':

    args = sys.argv

    device_name = "/dev/ttyUSB2"

    def print_usage():
        print('Usage: pwd10.py [-h] [port]')
        print(f'  port:    serial port (\"{device_name}\" default)')
        print('  -h:      print this')

    if '-h' in args:
        print_usage()
        sys.exit(0)

    if len(args) == 2:
        try:
            device_name = args[1]
        except(IndexError, ValueError):
            print_usage()
            sys.exit(1)

    pwd10 = PWD10(device_name)

    pwd10.record()
