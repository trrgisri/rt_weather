#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file sr05.py
@brief Read and analyze the weather observation data of Hukseflux SR05-D1A3

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2024 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import sys
import re
import datetime
import time
import struct
import pandas as pd

#from pymodbus import Framer
from pymodbus import FramerType, ModbusException
from pymodbus.client import ModbusSerialClient

from .base import WeatherInstrument
#from base import WeatherInstrument

# %%
class SR05(WeatherInstrument):
    DEVICE_NAME = 'SR05'
    DEVICE_ID = '00'

    ##
    # abstract methods
    def _init_serial(self, port='/dev/ttyUSB1'):
        super()._init_serial(port)
        #self.port = port
        self.baudrate = 19200
        self.bytesize = 8
        self.parity = 'E'
        self.stopbits = 1
        self.timeout = 3.0

        self._irradiance = None
        self._temperature = None
        self._nowday = None

    def open(self):
        # https://pymodbus.readthedocs.io/en/latest/source/client.html v3.6.9
        # self.msc = ModbusSerialClient(self.port, framer=Framer.RTU,
        #                                 baudrate=self.baudrate,
        #                                 bytesize=self.bytesize,
        #                                 parity=self.parity,
        #                                 stopbits=self.stopbits,
        #                                 timeout=self.timeout)
        #for pymodbus v3.7.2 up
        #from pymodbus import FramerType
        self.msc = ModbusSerialClient(self.port, framer=FramerType.RTU,
                                        baudrate=self.baudrate,
                                        bytesize=self.bytesize,
                                        parity=self.parity,
                                        stopbits=self.stopbits,
                                        handle_local_echo=False,
                                        name="comm")

        self.is_open = True

    def close(self):
        self.msc.close()
        self.is_open = False

    def receive(self):
        self.irradiance = SR05._retrieve_irradiance_data(self.msc)
        self.temperature = SR05._retrieve_temperature_data(self.msc)

        _datetime = datetime.datetime.today()
        self.telegramstr = self.DEVICE_ID + f", {self.irradiance:.2f}, {self.temperature:.2f}"
        return self.telegramstr, _datetime

    @staticmethod
    def retrieve(telegramstr):
        #self.receive()
        #return self._irradiance, self._temperature
        match = re.match(r'\s*[^,]+,\s*([-+]?\d*\.?\d+),\s*([-+]?\d*\.?\d+)', telegramstr)
        if not match:
            raise ValueError("Invalid line format")
        return float(match.group(1)), float(match.group(2))


    ##
    # @brief Record telegrams of SR05
    #
    # The telegram is recorded in "log_directory/logfile_basename_'%Y-%m-%d'.txt"
    # This method is based on SR05_logging.py by Masato Kodama <kodama.masato@aist.go.jp>.
    #
    # @param logfile_basename  Basename of the log file
    # @param log_directory     Directory path of the log file
    #
    # Example of telegram
    #         "[2024-05-15 00:00:51.321877] 00, 1.1234, 23.51"
    #
    def record(self, logfile_basename=DEVICE_NAME, log_directory=WeatherInstrument.LOG_DIRECTORY):
        self.open()

        if log_directory[-1] != '/': log_directory += '/'

        _current_day = datetime.datetime.today().date()
        _monthly_log_directory = log_directory + _current_day.strftime('%Y-%m/')

        logFile = self.create_new_logfile(None, logfile_basename, _monthly_log_directory)

        try:
            while True:

                try:
                    _telegramstr, _telegram_datetime = self.receive()
                    #irrval = SR05._retrieve_irradiance_data(self.msc)
                    #tmpval = SR05._retrieve_temperature_data(self.msc)
                except (ValueError, ModbusException) as e:
                    print(f"{e.__class__.__name__}: {e}")
                else:
                    #_nowday = datetime.datetime.today()
                    #telegramstr = self.DEVICE_ID + f", {irrval:.2f}, {tmpval:.2f}"
                    try:
                        if  _telegram_datetime.date() > _current_day:
                            _monthly_log_directory = log_directory + _telegram_datetime.strftime('%Y-%m/')
                            logFile = self.create_new_logfile(logFile, logfile_basename, _monthly_log_directory)
                            _current_day = _telegram_datetime.date()
                        self.write_log(_telegramstr, logFile, received_datetime=_telegram_datetime)
                    except OSError as e:
                        print(f"{e.__class__.__name__}: {e}")

                time.sleep(1)

        except KeyboardInterrupt:
            print("Record terminated")

        finally:
            self.close()

    ##
    # @brief Read irradiance data from SR05
    #
    # @author Masato Kodama <kodama.masato@aist.go.jp>
    #
    @staticmethod
    def _retrieve_irradiance_data(msc):
        """
        modbus通信でデータ取得リクエストを送り、返信データを取得する。
        照度データは32bitのint値を16bitバイナリの配列2つで返される
        マイナス値は[65535, 65534] --> -2 のような値で返ってくるので、バイナリ処理をしている
        modbusの為、センサ側からデータが吐き出されているのではなく、PC側からリクエストを出して
        それに対しての返信が来ているという事を意識する事。
        データは0.01 W/m²単位で取得するので、100で割っている。
        """
        #レジスタ情報2~3(放射照度情報、irradiance)を取得-SR05マニュアルTable6.2.4参照
        result = msc.read_holding_registers(2,2,1)
        if result.isError():
            return -1.0

        #16bit整数値2つを32bitバイナリ値に変換--[65535, 65534]-> 0xFFFFFFFE
        binval = struct.pack(">HH",result.registers[0],result.registers[1])
        #32bitバイナリ値をint32に変換 -- 0xFFFFFFFE-> -2
        irrval = struct.unpack('>i', binval)[0]

        return irrval / 100.0

    ##
    # @brief Read temperature data from SR05
    #
    # @author Masato Kodama <kodama.masato@aist.go.jp>
    #
    @staticmethod
    def _retrieve_temperature_data(msc):
        """
        modbus通信でデータ取得リクエストを送り、返信データを取得する。
        気温データは16bitのint値を16bitバイナリの配列1つで返される
        マイナス値は[65534] --> -2 のような値で返ってくるので、バイナリ処理をしている
        modbusの為、センサ側からデータが吐き出されているのではなく、PC側からリクエストを出して
        それに対しての返信が来ているという事を意識する事。
        データは0.01 ℃単位で取得するので、100で割っている。
        """
        #レジスタ情報6(気温情報)を取得-SR05マニュアルTable6.2.4参照
        result = msc.read_holding_registers(6,1,1)
        if result.isError():
            return -1.0

        #16bit整数値を16bitバイナリ値に変換--[65534]-> 0xFFFFFFFE
        binval = struct.pack(">H",result.registers[0])
        #16bitバイナリ値をint16に変換 -- 0xFFFFFFFE-> -2
        tmpval = struct.unpack('>h', binval)[0]

        return tmpval / 100.0

    ##
    # @brief Load SR05 telegrams from a CSV file and convert them to Pandas DataFrames
    #
    # @param fpath          String, Path of the CSV file
    # @param timezone       String, Pandas timezone
    # @return               the DataFrame
    #
    # Description:  [Date Time]                  irradiance temperature
    # Telegram   : "[2024-05-15 00:00:00.063059] 1.000, 10.000"
    @staticmethod
    def load_csvfile(fpath, timezone='Asia/Tokyo'):
        _l_datetime = []
        _l_val = []
        with open(fpath, encoding='utf8', newline='') as f:
            for _line in f:
                try:
                    _datestr = re.search(r"\[.+?\]", _line).group()
                    #_datetime = pd.to_datetime(_datestr, format='[%Y-%m-%d %H:%M:%S.%f] ' + SR05.DEVICE_ID).tz_localize(timezone)
                    _datetime = pd.to_datetime(_datestr, format='[%Y-%m-%d %H:%M:%S.%f]').tz_localize(timezone)
                    _data = re.search(r"\] \d{2}, ([\d\.-]+), ([\d\.-]+)", _line)
                    _l_data = [float(_data.group(1)), float(_data.group(2))]

                    _l_datetime.append(_datetime)
                    _l_val.append(_l_data)
                except (AttributeError, ValueError) as e:
                    print(f"{e.__class__.__name__}: {e}")
                    _, _, e_trace = sys.exc_info()
                    print(f"   at line {e_trace.tb_lineno} in {e_trace.tb_frame.f_code.co_filename}")

        return pd.DataFrame(_l_val,
                            columns=['Irradiance','Air Temperature'],
                            index=_l_datetime)

    ##
    # @brief Load SR05 telegrams from a CSV file and plot them with Matplotlib.
    #
    @staticmethod
    def plot_csvfile(fpath, timezone='Asia/Tokyo',
                        l_ax=[None, None],
                        l_plot_range=[(0, 1000), (10, 40)],
                        l_titlestr=['Irradiance', 'Air Temperature'],
                        l_rolling=[60, None],
                        l_legendstr=['SR05', 'SR05'],
                        l_color=[None, None],
                        ):
        _df = SR05.load_csvfile(fpath, timezone)
        #print(_df)

        _datestr = _df.index[0].strftime('%Y-%m-%d')
        _stime = pd.to_datetime(_datestr+' 00:00:00').tz_localize(timezone)
        _x_limit = (_stime, _stime + datetime.timedelta(days=1))

        if l_rolling[0] != None:
            _df['Irradiance'] = _df['Irradiance'].rolling(l_rolling[0]).mean()
            #print(_df)

        _titlestr = l_titlestr[0] + ' (' + _datestr + ')'
        _df = _df.rename(columns={'Irradiance': l_legendstr[0]})
        l_ax[0] = _df.plot.line(use_index=True, y=l_legendstr[0],
                            title=_titlestr,
                            xlabel='',
                            legend=(False if l_legendstr[0]==None else True),
                            color=l_color[0],
                            ax=l_ax[0])
        l_ax[0].set_ylim(l_plot_range[0])
        l_ax[0].set_xlim(_x_limit)
        _df = _df.rename(columns={l_legendstr[0] : 'Irradiance'})

        if l_rolling[1] != None:
            _df = _df['Air Temperature'].rolling(l_rolling[1]).mean()
        _titlestr = l_titlestr[1] + ' (' + _datestr + ')'
        _df = _df.rename(columns={'Air Temperature': l_legendstr[1]})
        l_ax[1] = _df.plot.line(use_index=True, y=l_legendstr[1],
                            title=_titlestr,
                            xlabel='',
                            legend=(False if l_legendstr[1]==None else True),
                            color=l_color[1],
                            ax=l_ax[1])
        l_ax[1].set_ylim(l_plot_range[1])
        l_ax[1].set_xlim(_x_limit)

        return l_ax, _df

class SR05_debug(SR05):
    _base_value = 0.0

    def open(self):
        self.is_open = True

    def close(self):
        self.is_open = False

    def receive(self):
        self.irradiance = self._base_value + 10.0
        self.temperature = self._base_value * 10.0
        self._base_value += 1.0

        _datetime = datetime.datetime.today()
        self.telegramstr = self.DEVICE_ID + f", {self.irradiance:.2f}, {self.temperature:.2f}"
        return self.telegramstr, _datetime

# %%
if __name__ == '__main__':

    sr05 = SR05_debug('/dev/ttyUSB1')

    sr05.record()
