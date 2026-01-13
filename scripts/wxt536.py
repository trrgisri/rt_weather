#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file wxt536.py
@brief Record observation data of Vaisala WXT536

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2025 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import sys

#from emulated_srs_py.weather.wxt536 import WXT536
from rt_weather.instruments.wxt536 import WXT536

# %%
if __name__ == '__main__':

    args = sys.argv

    device_name = "/dev/ttyUSB0"

    def print_usage():
        print('Usage: wxt536.py [-h] [port]')
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

    wxt = WXT536(device_name)

    wxt.record()
