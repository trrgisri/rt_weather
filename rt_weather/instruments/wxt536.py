#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file wxt536.py
@brief Read and analyze the weather observation data of Vaisala WXT536

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2024 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import re
import datetime
import pandas as pd

from .base import WeatherInstrument
#from base import WeatherInstrument

# %%
class WXT536(WeatherInstrument):
    DEVICE_NAME = 'WXT536'

    # abstract methods
    def _init_serial(self, port='/dev/ttyS1'):
        super()._init_serial(port)
        self.baudrate = 19200

    def open(self):
        super().open()

    def close(self):
        super().close()

    ##
    # @brief Receive telegrams of WXT536
    #
    # # Examples of telegrams
    #
    # * 0R1: Wind
    #   - Dn: Min direction, Dm: Ave direction, Dx: Max direction
    #   - Sn: Min speed (m), Sm: Ave speed (m), Sx: Max Speed (m)
    #
    #         "0R1,Dn=177D,Dm=207D,Dx=244D,Sn=0.3M,Sm=0.4M,Sx=0.6M"
    #
    # * R2: Air
    #   - Ta: Air temperature (C), Ua: Relative humidity (%), Pa: Barometric Pressure (hpa)
    #
    #         "0R2,Ta=14.8C,Ua=77.0P,Pa=1013.8H"
    #
    # * R3: Precipitation
    #   - Rc: Cumulative precipitation (mm), Rd: Precipitation time (s), Ri: Precipitation rate (mm/h)
    #   - Hc, Hd, Hi: Hailfalll
    #
    #         "0R3,Rc=144.09M,Rd=26760s,Ri=0.0M,Hc=0.0M,Hd=0s,Hi=0.0M"
    #
    # * R5: Status
    #
    #         "0R5,Th=15.1C,Vh=15.0N,Vs=15.2V,Vr=3.589V"
    def receive(self):
        return super().receive()

    ##
    # @brief Retrieve the one-line telegram string of WXT536
    # @param telegramstr    the one-line telegram string
    # @return               dictionary of the values, e.g. {'ID':'0R2', 'Ta':14.8, 'Ua':77.0, 'Pa':1013.8}
    @staticmethod
    def retrieve(telegramstr: str):
        parts = [p.strip() for p in telegramstr.split(',')]
        result = {}
        if parts[0] in ('0R1', '0R2', '0R3', '0R5'):
            result = {'ID': parts[0]}
            for p in parts[1:]:
                match = re.match(r'^([a-zA-Z]+)=([-+]?\d*\.?\d+)[a-zA-Z]*$', p)
                if match:
                    key = match.group(1)
                    value = float(match.group(2))
                    result[key] = value

        return result

    ##
    # @brief Record telegrams of WXT536
    #
    # The telegram is recorded in "log_directory/logfile_basename_'%Y-%m-%d'.txt"
    #
    # @param logfile_basename  Basename of the log file
    # @param log_directory     Directory path of the log file
    #
    def record(self, logfile_basename=DEVICE_NAME, log_directory=WeatherInstrument.LOG_DIRECTORY):
        super().record(logfile_basename, log_directory)

    @staticmethod
    def _to_float(s):
        #match = re.sub(r"[^+-\d.]","",s)
        match = re.search(r"[-+]?\d*\.\d+|\d+", s)
        return float(match.group()) if match else float('nan')

    @staticmethod
    def _conv_weather_data(df_w, timezone):
        if df_w.empty:
            return df_w
        columns = [i[0:2] for i in df_w.iloc[0][1:]]
        #print(columns)
        df_w['T'] = df_w['T'].map(lambda x:pd.to_datetime(x[:-4], format='[%Y-%m-%d %H:%M:%S.%f]').tz_localize(timezone))
        #df_w['T'].map(lambda x:pd.to_datetime(x[:-4], format='[%Y-%m-%d %H:%M:%S.%f]'))
        df2 = df_w.set_index('T')
        #l_datetime = [pd.to_datetime(x[:-4], format='[%Y-%m-%d %H:%M:%S.%f]').tz_localize(timezone) for x in df_w['T']]
        #df2 = df_w.drop('T',axis=1).set_axis(l_datetime, axis='index')
        #return df2.applymap(WXT536._to_float).set_axis(columns, axis=1)
        return df2.map(WXT536._to_float).set_axis(columns, axis=1)

    ##
    # @brief Load WXT536 telegrams from a CSV file and convert them to Pandas DataFrames
    #
    # @param fpath          String, Path of the CSV file
    # @param timezone       String, Pandas timezone
    # @return               List of the DataFrames, [df_R1, df_R2, df_R3]
    # @retval df_R1         DataFrame on Wind
    # @retval df_R2         DataFrame on Air
    # @retval df_R3         DataFrame on Precipitation
    #
    # # Example of DataFrame of Wind
    #
    #     [                                    Dn     Dm     Dx   Sn   Sm   Sx
    #     T                                                                   
    #     2024-05-23 17:34:51.434581+09:00   52.0   99.0  127.0  0.8  1.2  1.5
    #     2024-05-23 17:34:56.443924+09:00   52.0   84.0  122.0  0.4  0.7  1.0
    #     2024-05-23 17:35:00.456798+09:00  112.0  144.0  211.0  0.3  0.5  0.8
    #     ...                                 ...    ...    ...  ...  ...  ...
    #     2024-05-23 23:59:46.022431+09:00  113.0   49.0  330.0  0.1  0.2  0.3
    #     2024-05-23 23:59:51.032443+09:00   32.0   69.0  102.0  0.2  0.3  0.4
    #     2024-05-23 23:59:56.042466+09:00   91.0  129.0  171.0  0.3  0.3  0.3
    #     [4622 rows x 6 columns]
    #
    @staticmethod
    def load_csvfile(fpath, timezone='Asia/Tokyo'):
        df_tmp = pd.read_csv(fpath, encoding='utf_8', names=['T',1,2,3,4,5,6])
        #print(df_tmp)
        #df_tmp['%time'] = pd.to_datetime(df_tmp['%time'].astype(int), utc=True).dt.tz_convert(timezone)
        #df_tmp['field.header.stamp'] = pd.to_datetime(df_tmp['field.header.stamp'].astype(int), utc=True).dt.tz_convert(timezone)
        #print(df_tmp['%time'].dt.tz)
        #print(df_tmp)
        df_tmp = df_tmp.dropna(subset=['T'])
        #print(df_tmp)
        l_df = [df_tmp.query('T.str.endswith("'+s+'")').dropna(how='all', axis=1) for s in [' 0R1',' 0R2',' 0R3',' 0R5']]

        #l_df = [df_tmp.query('T.str.endswith("'+s+'")').dropna(how='all', axis=1) for s in [' 0R1',' 0R2',' 0R3',' 0R5']]
        #print(l_df)
        return [WXT536._conv_weather_data(d,timezone) for d in l_df]

    ##
    # @brief Load WXT536 telegrams from a CSV file and plot them with Matplotlib.
    #
    @staticmethod
    def plot_csvfile(fpath, timezone='Asia/Tokyo',
                        l_ax=[None, None, None, None, None],
                        l_df_index=[0, 1, 1, 1, 2],
                        l_df_key=['Sx', 'Ta', 'Ua', 'Pa', 'Ri'],
                        l_plot_range=[(0, 30), (0,40), (0,100), (950,1050), (0,40)],
                        l_titlestr=['Wind', 'Air Temperature','Relative Humidity', 'Barometric Pressure', 'Precipitation'],
                        l_rolling=[60, None, None, None, None],
                        l_legendstr=['WXT536', 'WXT536', 'WXT536', 'WXT536', 'WXT536'],
                        l_color=[None, None, None, None, None],
                        ):
        l_df = WXT536.load_csvfile(fpath, timezone)
        #print(l_df)
        datestr = l_df[0].index[0].strftime('%Y-%m-%d')
        _l_titlestr = [s + ' (' + datestr + ')' for s in l_titlestr]

        _stime = pd.to_datetime(datestr+' 00:00:00').tz_localize(timezone)
        _x_limit = (_stime, _stime + datetime.timedelta(days=1))

        for i, i_df in enumerate(l_df_index):
            if l_legendstr[i] is None:
                _df = l_df[i_df]
                _columnstr = l_df_key[i]
                _legend = False
            else:
                _df = l_df[i_df].rename(columns={l_df_key[i]: l_legendstr[i]})
                _columnstr = l_legendstr[i]
                _legend = True

            if _df.empty:
                continue

            if l_rolling[i] != None:
                #_df = _df[l_df_key[i]].rolling(l_rolling[i]).mean()
                _df = _df[_columnstr].rolling(l_rolling[i]).mean()

            l_ax[i] = _df.plot.line(use_index=True, y=_columnstr,
                            title=_l_titlestr[i],
                            xlabel='',
                            legend=_legend,
                            color=l_color[i],
                            ax=l_ax[i])
            l_ax[i].set_ylim(l_plot_range[i])
            l_ax[i].set_xlim(_x_limit)

        #_df.plot()
        return l_ax, l_df

class WXT536_debug(WXT536):
    TELEGRAM_EXAMPLES = ["0R1,Dn=305D,Dm=312D,Dx=335D,Sn=0.1M,Sm=0.3M,Sx=0.5M",
                            "0R2,Ta=27.8C,Ua=83.2P,Pa=1008.4H",
                            "0R5,Th=27.7C,Vh=15.0N,Vs=14.9V,Vr=3.610V",
                            "0R3,Rc=109.50M,Rd=58910s,Ri=0.0M,Hc=0.0M,Hd=0s,Hi=0.0M",
    ]
    example_count = 0

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def receive(self):
        self.example_count += 1
        return self.TELEGRAM_EXAMPLES[self.example_count % 4], datetime.datetime.now()

# %%
if __name__ == '__main__':

    wxt = WXT536_debug('/dev/ttyUSB0')

    wxt.record()
