#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file omron_2jciebu.py
@brief Print measurement data of Omron 2JCIEBU

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2025 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import argparse
import datetime
import time

from rt_weather.instruments.omron_2jciebu import Omron2jciebu

def main():
    parser = argparse.ArgumentParser(description='Print measurement data of Omron 2JCIEBU.',
                                        formatter_class=argparse.RawDescriptionHelpFormatter,
                                        )
    parser.add_argument('device_name', metavar='DEV', nargs='?', default='/dev/ttyUSB0', help='device name (default: %(default)s)')
    parser.add_argument('--led_on', action='store_true', help='LED on')
    parser.add_argument('--interval', default=1, type=int, help='measurement interval (sec, default: 1)')

    args = parser.parse_args()

    o2 = Omron2jciebu(args.device_name)
    o2.open()

    if args.led_on:
        o2.led_on()

    try:
        while o2.is_open:
            o2.receive()
            _dt = datetime.datetime.today().strftime('%Y-%m-%d %H:%M:%S')
            print(f"---")
            print(f"Time: \'{_dt}\'")
            print(f"Temperature: {o2.temperature}")
            print(f"RelativeHumidity: {o2.relative_humidity}")
            print(f"Illuminance: {o2.illuminance}")
            print(f"BarometricPressure: {o2.barometric_pressure}")
            print(f"SoundNoise: {o2.sound_noise}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        o2.led_off()
        o2.close()

# %%
if __name__ == '__main__':
    main()
