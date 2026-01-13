#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file pwd10.py
@brief Read and analyze the visibility data of Vaisala PWD10

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2024 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import sys
import serial
import re
import math
import datetime
import pandas as pd

from .base import WeatherInstrument
#from base import WeatherInstrument

# %%
class PWD10(WeatherInstrument):
    DEVICE_NAME = 'PWD10'

    ##
    # abstract methods
    def _init_serial(self, port='/dev/ttyUSB0'):
        self.port = port
        self.baudrate = 9600
        self.bytesize = serial.SEVENBITS
        self.parity = serial.PARITY_EVEN
        self.stopbits = serial.STOPBITS_ONE
        self.timeout = 1

    def open(self):
        super().open()

    def close(self):
        super().close()

    def record(self, logfile_basename=DEVICE_NAME, log_directory=WeatherInstrument.LOG_DIRECTORY):
        super().record(logfile_basename, log_directory)

    # Description: '^A'PW id'^B'error MOR1m  MOR10m'^C'
    # Telegram   : "\x01PW  1\x0200   2000  2000\x03"
    def receive(self):
        return super().receive()

    ##
    # @brief Retrieve the one-line telegram string of PWD10
    # @param telegramstr    one-line telegram string
    # @return               list of error code, MOR[1min] and MOR[10min]
    @staticmethod
    def retrieve(telegramstr: str):
        _datastr = re.search(r"\x02.+?\x03", telegramstr).group()
        _l_data = [int(i) for i in re.findall(r"\d+", _datastr)]

        return _l_data

    @staticmethod
    ## PWD10 csv
    # Description:  [Date Time]                  '^A'PW id'^B'error MOR1m  MOR10m'^C'
    # Telegram   : "[2024-05-15 00:00:00.063059] \x01PW  1\x0200   2000  2000\x03"
    def load_csvfile(fpath, timezone='Asia/Tokyo', verbose=False):
        #_df = pd.DataFrame(columns=['error','mor_1min','mor_10min'])
        _l_datetime = []
        _l_val = []
        with open(fpath, encoding='utf8', newline='') as f:
            for _line in f:
                try:
                    _datestr = re.search(r"\[.+?\]", _line).group()
                    _datetime = pd.to_datetime(_datestr, format='[%Y-%m-%d %H:%M:%S.%f]').tz_localize(timezone)
                    _datastr = re.search(r"\x02.+?\x03", _line).group()

                    # if incorrect data, do not exec the following.
                    _l_datetime.append(_datetime)
                    _l_data = [int(i) for i in re.findall(r"\d+", _datastr)]
                    _t5 = math.exp(5.0*math.log(0.02)/_l_data[1]) * 100.0  # calc T5 from MOR1min
                    _l_data.append(_t5)
                    _l_val.append(_l_data)
                except (AttributeError, ValueError) as e:
                    if verbose:
                        print(f"{e.__class__.__name__}: {e}")
                        _, _, e_trace = sys.exc_info()
                        print(f"   at line {e_trace.tb_lineno} in {e_trace.tb_frame.f_code.co_filename}")

        return pd.DataFrame(_l_val,
                            columns=['error','MOR_1min','MOR_10min', 'T5'],
                            index=_l_datetime)

    @staticmethod
    def plot_csvfile(fpath, timezone='Asia/Tokyo',
                        l_ax=[None, None],
                        columnstr='MOR_1min',
                        l_plot_range=[(0, 2100), (50, 100)],
                        l_titlestr=['MOR', 'Spatial Transmittance: 5m'],
                        l_legendstr=['PWD10', 'PWD10'],
                        l_color=[None, None],
                        ):
        df_tmp = PWD10.load_csvfile(fpath, timezone)
        #print(df_tmp)

        _datestr = df_tmp.index[0].strftime('%Y-%m-%d')
        _stime = pd.to_datetime(_datestr+' 00:00:00').tz_localize(timezone)
        _x_limit = (_stime, _stime + datetime.timedelta(days=1))

        _titlestr = l_titlestr[0] + ' (' + _datestr + ')'
        _df = df_tmp.rename(columns={columnstr: l_legendstr[0]})
        l_ax[0] = _df.plot.line(use_index=True, y=l_legendstr[0],
                            title=_titlestr,
                            xlabel='',
                            legend=(False if l_legendstr[0]==None else True),
                            color=l_color[0],
                            ax=l_ax[0])
        l_ax[0].set_ylim(l_plot_range[0])
        l_ax[0].set_xlim(_x_limit)

        _titlestr = l_titlestr[1] + ' (' + _datestr + ')'
        _df = df_tmp.rename(columns={'T5': l_legendstr[1]})
        l_ax[1] = _df.plot.line(use_index=True, y=l_legendstr[1],
                            title=_titlestr,
                            xlabel='',
                            legend=(False if l_legendstr[1]==None else True),
                            color=l_color[1],
                            ax=l_ax[1])
        l_ax[1].set_ylim(l_plot_range[1])
        l_ax[1].set_xlim(_x_limit)

        return l_ax, df_tmp


class PWD10_debug(PWD10):
    TELEGRAM_EXAMPLES = ["\x01PW  1\x0200   2000  2000\x03",
                            "\x01PW  1\x0200   2001  3000\x03",
                            "\x01PW  1\x0200   2002  4000\x03",
                            "\x01PW  1\x0200   2003  5000\x03",
                            "\x01PW  1\x0200   2004  6000\x03",
    ]
    example_count = 0

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def receive(self):
        self.example_count += 1
        return self.TELEGRAM_EXAMPLES[self.example_count % 5], datetime.datetime.now()

# %%
if __name__ == '__main__':

    pwd = PWD10_debug('/dev/ttyUSB1')

    pwd.record()
