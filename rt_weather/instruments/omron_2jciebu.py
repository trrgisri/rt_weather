#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file  env_sensor.py
@brief Read and analyze the environmental data of Omron 2jciebu

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2022 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import serial
import time
import datetime
import os
import pandas as pd

from .opt.sample_2jciebu import s16, calc_crc

##
# @brief Class implementing the functionality of Omron 2jciebu
class Omron2jciebu(object):
    # LED display rule. Normal Off.
    _DISPLAY_RULE_NORMALLY_OFF = 0

    # LED display rule. Normal On.
    _DISPLAY_RULE_NORMALLY_ON = 1

    ##
    # @brief Constructor
    #
    def __init__(self, port="/dev/ttyUSB0"):
        self.port = port
        self.data = None
        self.temperature = 0
        self.relative_humidity = 0
        self.illuminance = 0
        self.barometric_pressure = 0
        self.sound_noise = 0
        self.is_open = False

    def open(self):
        self._serial_device = serial.Serial(self.port, 115200, serial.EIGHTBITS, serial.PARITY_NONE)
        self.is_open = True

    def close(self):
        self._serial_device.close()
        self.is_open = False

    def receive(self):
        if self._serial_device.isOpen():
            # Get Latest data Long.
            command = bytearray([0x52, 0x42, 0x05, 0x00, 0x01, 0x21, 0x50])
            command = command + calc_crc(command, len(command))
            tmp = self._serial_device.write(command)
            time.sleep(0.1)

            self.data = None
            self.temperature = 0
            self.relative_humidity = 0
            self.illuminance = 0
            self.barometric_pressure = 0
            self.sound_noise = 0

            if (nbytes := self._serial_device.inWaiting()) > 0:
                self.data = self._serial_device.read(nbytes)
                if nbytes == 58:
                    self.temperature = s16(int(hex(self.data[9]) + '{:02x}'.format(self.data[8], 'x'), 16)) / 100
                    self.relative_humidity = int(hex(self.data[11]) + '{:02x}'.format(self.data[10], 'x'), 16) / 100
                    self.illuminance = int(hex(self.data[13]) + '{:02x}'.format(self.data[12], 'x'), 16)
                    self.barometric_pressure = int(hex(self.data[17]) + '{:02x}'.format(self.data[16], 'x')
                                + '{:02x}'.format(self.data[15], 'x') + '{:02x}'.format(self.data[14], 'x'), 16) / 1000
                    self.sound_noise = int(hex(self.data[19]) + '{:02x}'.format(self.data[18], 'x'), 16) / 100
                else:
                    #print("Invalid data received: %d bytes, %s", nbytes, self.data)
                    raise ValueError(f"Invalid data received: {nbytes} bytes, {self.data}")
            else:
                #print("No data received.")
                raise ValueError("No data received")
        else:
            raise RuntimeError("Device not open")

    def led_on(self):
        """
        LED On. Color of Green.
        """
        if self._serial_device.isOpen():
            command = bytearray([0x52, 0x42, 0x0a, 0x00, 0x02, 0x11, 0x51, self._DISPLAY_RULE_NORMALLY_ON, 0x00, 0, 255, 0])
            command = command + calc_crc(command, len(command))
            self._serial_device.write(command)
            time.sleep(0.1)
            ret = self._serial_device.read(self._serial_device.inWaiting())
            return ret

    def led_off(self):
        """
        LED Off.
        """
        if self._serial_device.isOpen():
            command = bytearray([0x52, 0x42, 0x0a, 0x00, 0x02, 0x11, 0x51, self._DISPLAY_RULE_NORMALLY_OFF, 0x00, 0, 0, 0])
            command = command + calc_crc(command, len(command))
            self._serial_device.write(command)
            time.sleep(0.1)
            ret = self._serial_device.read(self._serial_device.inWaiting())
            return ret

    @staticmethod
    def conv_to_numeric(s):
        try:
            if '.' in s:
                return float(s)
            else:
                return int(s)
        except ValueError:
            return s

    @staticmethod
    def load_csvfile(fpath, timezone='Asia/Tokyo'):
        #df_tmp = pd.read_csv(fpath, encoding='utf_8', names=['header.stamp.sec', 'header.stamp.nanosec', 'header.frame_id', 'relative_humidity', 'variance'])
        df_tmp = pd.read_csv(fpath, encoding='utf_8')
        if df_tmp.empty:
            raise ValueError(f'>>> Empty file: {fpath}')
        if df_tmp.iloc[0,0] == 'header.stamp.sec':
            #print(df_tmp.index)
            df_tmp = df_tmp.drop(index=0)
            #print(df_tmp.index+1)
            df_tmp.index = df_tmp.index - 1

        #print(df_tmp.columns[0], isinstance(df_tmp.columns[0], int), type(df_tmp.columns[0]))
        #print(df_tmp)
        if df_tmp.columns[0] != 'header.stamp.sec':
            #_original_columns = df_tmp.columns.tolist()
            _original_columns = [Omron2jciebu.conv_to_numeric(x) for x in df_tmp.columns.tolist()]
            df_tmp.loc[-1] = _original_columns
            df_tmp.index = df_tmp.index + 1
            df_tmp = df_tmp.sort_index()
            df_tmp.columns = ['header.stamp.sec', 'header.stamp.nanosec', 'header.frame_id', 'value', 'variance']
            #print(df_tmp)

        #print(df_tmp)
        #df_tmp['%time'] = pd.to_datetime(df_tmp['%time'].astype(int), utc=True).dt.tz_convert(timezone)
        #print(df_tmp)
        df_tmp['header.stamp.sec'] = pd.to_datetime(df_tmp['header.stamp.sec'].astype(int), unit='s', utc=True).dt.tz_convert(timezone)
        #print(df_tmp['%time'].dt.tz)
        #print(df_tmp)
        return df_tmp.sort_values('header.stamp.sec')

    @staticmethod
    def plot_csvfile(fpath, timezone='Asia/Tokyo',
                        ax=None,
                        columnstr='temperature',
                        plot_range=(10, 40),
                        titlestr='Air Temperature',
                        legendstr='2JCIEBU',
                        color=None,
                        previous_day_fpath=None,
                        ):
        df_tmp = Omron2jciebu.load_csvfile(fpath, timezone)
        #print(df_tmp)

        _datestr = df_tmp.loc[0,'header.stamp.sec'].strftime('%Y-%m-%d')
        if df_tmp.columns[3] == 'value':
            df_tmp.columns.values[3] = columnstr

        #_titlestr = titlestr + ' (' + df_tmp.loc[0,'%time'].strftime('%Y-%m-%d') + ')'
        _titlestr = titlestr + ' (' + _datestr + ')'
        #_df = df_tmp.drop(['field.header.seq','field.header.stamp','field.header.frame_id','field.variance'], axis=1)
        #print(_df)

        if previous_day_fpath and os.path.exists(previous_day_fpath):
            try:
                df_prev = Omron2jciebu.load_csvfile(previous_day_fpath, timezone=timezone)
            except(ValueError):
                # Calc today's detection rates due to bad yesterday's data.
                #df['Detection Rate'] = df['n_obstacles'].rolling(window_for_detection_rate).apply(ObstacleGroup.calc_detection_rate)
                pass
            else:
                # Concat yesterday's last data.
                df_prev = df_prev.iloc[-3600:]
                df_tmp = pd.concat([df_prev, df_tmp], join='inner').sort_values('header.stamp.sec')
                #print(df_prev)

        _stime = pd.to_datetime(_datestr+' 00:00:00').tz_localize(timezone)
        _x_limit = (_stime, _stime + datetime.timedelta(days=1))
        if legendstr != None:
            _df = df_tmp.rename(columns={columnstr: legendstr})
            _columnstr = legendstr
            _legend = True
        else:
            _df = df_tmp
            _columnstr = columnstr
            _legend = False

        ax = _df.plot.line(x='header.stamp.sec', y=_columnstr,
                        title=_titlestr, xlabel='',
                        legend=_legend,
                        color=color,
                        ax=ax)
        ax.set_ylim(plot_range)
        ax.set_xlim(_x_limit)
        #_df.plot()
        return ax, df_tmp

