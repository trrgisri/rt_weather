#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file sr05.py
@brief Record observation data of Hukseflux SR05-D1A3

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2025 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import sys

from rt_weather.instruments.sr05 import SR05

# %%
if __name__ == '__main__':

    args = sys.argv

    device_name = "/dev/ttyUSB3"

    def print_usage():
        print('Usage: sr05.py [-h] [port]')
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

    sr05 = SR05(device_name)

    sr05.record()
