#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file weather_instrument.py
@brief Abstract class for weather instruments

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2024 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

from abc import ABC, abstractmethod
import serial
import os
import datetime
import time

class WeatherInstrument(ABC):
    #LOG_DIRECTORY = '/mnt/monoeyenas0/Public/Weather/'
    LOG_DIRECTORY = './Weather/'

    def __init__(self, port='/dev/ttyS0'):
        self._init_serial(port)
        print(self.port, self.baudrate, self.bytesize)

    @abstractmethod
    def _init_serial(self, port='/dev/ttyS0'):
        self.port = port
        self.baudrate = 9600
        self.bytesize = serial.EIGHTBITS
        self.parity = serial.PARITY_NONE
        self.stopbits = serial.STOPBITS_ONE
        self.timeout = 1
        self.is_open = False

    @abstractmethod
    def open(self):
        self._ser = serial.Serial(self.port, self.baudrate, self.bytesize, self.parity, self.stopbits, self.timeout)
        self.is_open = True

    @abstractmethod
    def close(self):
        self._ser.close()
        self.is_open = False

    @staticmethod
    def convert_control_characters(input_str, char_for_conv=' '):
        return ''.join([char_for_conv if ord(c) < 32 or ord(c) > 126 else c for c in input_str])

    ##
    # @brief Receives a one-line telegram from the weather instrument
    #        This method is based on WXT536_logging.py written by kodama.masato@aist.go.jp
    # @return tuple of received one-line telegram string and datetime
    #
    @abstractmethod
    def receive(self):
        _telegram = None
        if self._ser.in_waiting > 0:
            _telegram = self._ser.readline().decode('ascii').strip()
            self._ser.reset_input_buffer()
        _datetime = datetime.datetime.today()
        return _telegram, _datetime

    ##
    # @brief   Retrieves an instrument-dependent one-line telegram string
    # @param telegramstr  string of received one-line telegram
    # @return             values of a received one-line telegram
    #
    #@abstractmethod
    @staticmethod
    def retrieve(telegramstr):
        raise NotImplementedError
        #return val1, val2, val3

    ##
    # @brief Records one-line telegrams from the weather instrument
    #
    # The telegram is recorded in "log_directory/logfile_basename_'%Y-%m-%d'.txt".
    # This method is based on WXT536_logging.py by Masato Kodama <kodama.masato@aist.go.jp>.
    #
    # @param logfile_basename  Basename of the log file
    # @param log_directory     Directory path of the log file
    #
    @abstractmethod
    def record(self, logfile_basename, log_directory):
        self.open()

        if log_directory[-1] != '/': log_directory += '/'

        currentDate = datetime.date.today()
        _monthly_log_directory = log_directory + currentDate.strftime('%Y-%m/')

        logFile = self.create_new_logfile(None, logfile_basename, _monthly_log_directory)

        try:
            while True:
                #nowDay = datetime.date.today()
                try:
                    telegramstr, telegram_datetime = self.receive()
                except ValueError as e:
                    print(f"{e.__class__.__name__}: {e}")
                else:

                    if telegramstr != None:
                        try:
                            if telegram_datetime.date() > currentDate:
                                _monthly_log_directory = log_directory + telegram_datetime.strftime('%Y-%m/')
                                logFile = self.create_new_logfile(logFile, logfile_basename, _monthly_log_directory)
                                currentDate = telegram_datetime.date()
                            self.write_log(telegramstr,logFile, received_datetime=telegram_datetime)
                        except OSError as e:
                            print(f"{e.__class__.__name__}: {e}")

                time.sleep(1)

        except KeyboardInterrupt:
            print("Record terminated")

        finally:
            self.close()

    ##
    # @brief Prepares a new log file
    #
    # @author Masato Kodama <kodama.masato@aist.go.jp>
    #
    @staticmethod
    def create_new_logfile(logfile, logfile_basename, log_directory):
        """
        日付が変わった際に旧ログファイルをクローズ
        新しいファイルを日付を名前として作成してオープンする。
        :return: 新しいファイルオブジェクト
        :rtype:

        """
        #ファイルオブジェクトのチェック
        if logfile != None:
            if not logfile.closed:
                logfile.close()

        # ディレクトリが存在するかどうか確認
        if not os.path.exists(log_directory):
            # 存在しない場合はディレクトリを作成
            try:
                os.makedirs(log_directory)
            except FileExistsError: # can occur rarely (added by y.sumi)
                pass

        dayStr = datetime.date.today().strftime('%Y-%m-%d')
        logfile_name = logfile_basename + '_' + dayStr + '.txt'
        logpath = log_directory + logfile_name
        logfile = open(logpath, "a")

        return logfile

    @staticmethod
    def close_logfile(logfile):
        if logfile != None:
            if not logfile.closed:
                logfile.close()

    ##
    # @brief Writes one-line telegram to the log file
    #
    # @author Masato Kodama <kodama.masato@aist.go.jp>
    #
    @staticmethod
    def write_log(received_data, logfile, received_datetime=None):
        """
        ファイルにログデータを書き込む
        ログデータは行単位で処理する
        データ行の先頭にはPCタイムスタンプを加える
        """
        if received_datetime is None:
            received_datetime = datetime.datetime.now()

        _received_timestr = received_datetime.strftime('[%Y-%m-%d %H:%M:%S.%f]')

        logstring = _received_timestr + ' ' + received_data + '\n'
        logfile.write(logstring)
        #print(logstring)	#受信データ＆文字列確認用
        logfile.flush()

if __name__ == '__main__':

    class ThiesLPM(WeatherInstrument):
        DEVICE_NAME = 'ThiesLPM'

        def _init_serial(self, port):
            super()._init_serial(port)
            self.device_name = self.DEVICE_NAME

        def record(self, logfile_basename=DEVICE_NAME, log_directory=WeatherInstrument.LOG_DIRECTORY):
            super().record(logfile_basename, log_directory)

    class PWD10(WeatherInstrument):
        DEVICE_NAME = 'PWD10'

        def _init_serial(self, port):
            super()._init_serial(port)
            self.bytesize = serial.SEVENBITS
            self.parity = serial.PARITY_EVEN
            self.device_name = self.DEVICE_NAME

        def record(self, logfile_basename=DEVICE_NAME, log_directory=WeatherInstrument.LOG_DIRECTORY):
            super().record(logfile_basename, log_directory)

    class WXT536(WeatherInstrument):
        DEVICE_NAME ="WXT536"

        def _init_serial(self, port):
            super()._init_serial(port)
            self.baudrate = 19200
            self.device_name = self.DEVICE_NAME

        def record(self, logfile_basename=DEVICE_NAME, log_directory=WeatherInstrument.LOG_DIRECTORY):
            super().record(logfile_basename, log_directory)

        def testtest(self, arg=DEVICE_NAME):
            print(arg)

    ThiesLPM('hoge')
    PWD10('fuga')
    wxt = WXT536('piyo')
    print(wxt.LOG_DIRECTORY)
    wxt.testtest()