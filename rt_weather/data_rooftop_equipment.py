#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file data_rooftop_equipment.py
@brief

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2024 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import sys
import re
import datetime
import pandas as pd
import matplotlib.pyplot as plt

from .instruments.thies_lpm import ThiesLPM
from .instruments.pwd10 import PWD10
from .instruments.wxt536 import WXT536
from .instruments.sr05 import SR05
from .instruments.omron_2jciebu import Omron2jciebu
#from .obstacle_group import ObstacleGroup

# 4+5
# | ---                   | ---                  | ---               | ---                    |
# | Precipitation         | Transmittance        | MOR               | Detection Rate         |
# | 1,5                   | 6,10                 | 11,15             | 16,20                  |
# | ===              | ---             | ---               | ---                 | ---        |
# | Particle Density | Air Temperature | Relative Humidity | Barometric Pressure | Wind       |
# | 21,24            | 25,28           | 29,32             | 33,36               | 37,40      |
# | ---              | ---             | ---               | ---                 | ---        |
#
# 5x2
# | ---              | ---             | ---               | ---                 |                |
# | Precipitation    | Transmittance   | MOR               | Irradiance          | Detection Rate |
# | 1                | 2               | 3                 | 4                   | 5              |
# | ===              | ---             | ---               | ---                 | ---            |
# | Particle Density | Air Temperature | Relative Humidity | Barometric Pressure | Wind           |
# | 6                | 7               | 8                 | 9                   | 10             |
# | ---              | ---             | ---               | ---                 | ---            |
#
# 4,4,2
# | ---              | ---             | ---               | ---                 |
# | Precipitation    | Transmittance   | MOR               | Irradiance          |
# | 1                | 2               | 3                 | 4                   |
# | ===              | ---             | ---               | ---                 |
# | Particle Density | Air Temperature | Relative Humidity | Barometric Pressure |
# | 5                | 6               | 7                 | 8                   |
# | ===              | ---             | ---               | ---                 |
# | Wind             | Detection Rate  |
# | 9                | 10              |
# | ---              | ---             |
#
# 4x3
# | ---              | ---             | ---               | ---                 |
# | Precipitation    | Transmittance   | MOR               | Irradiance          |
# | 1                | 2               | 3                 | 4                   |
# | ===              | ---             | ---               | ---                 |
# | Particle Density | Air Temperature | Relative Humidity | Barometric Pressure |
# | 5                | 6               | 7                 | 8                   |
# | ===              | ---             | ---               | ---                 |
# | Wind             | Detection Rate  | Detection Rate    | Detection Rate      |
# | 9                | 10              | 11                | 12                  |
# | ---              | ---             | ---               | ---                 |
class DataRooftopEquipment(object):
    def __init__(self, window_title='Rooftop Monitor', internal_environment_p=True):
        #self.figure = plt.figure(window_title, figsize=(20,8))
        self.figure = plt.figure(window_title, figsize=(20,12))
        self._set_axes()
        self._internal_environment_p = internal_environment_p

    def _set_axes(self):
        self.ax_precipitation = self.figure.add_subplot(3,4,1)
        self.ax_transmittance5m = self.figure.add_subplot(3,4,2)
        self.ax_mor = self.figure.add_subplot(3,4,3)
        self.ax_irradiance = self.figure.add_subplot(3,4,4)

        self.ax_particle_density = self.figure.add_subplot(3,4,5)
        self.ax_air_temperature = self.figure.add_subplot(3,4,6)
        self.ax_relative_humidity = self.figure.add_subplot(3,4,7)
        self.ax_barometric_pressure = self.figure.add_subplot(3,4,8)
        self.ax_wind = self.figure.add_subplot(3,4,9)

        self.ax_detection_rates = [self.figure.add_subplot(3,4,10), self.figure.add_subplot(3,4,11), self.figure.add_subplot(3,4,12)]

        #print(self.figure.axes)

    # def _set_axes_5x2(self):
    #     self.ax_precipitation = self.figure.add_subplot(2,5,1)
    #     self.ax_transmittance5m = self.figure.add_subplot(2,5,2)
    #     self.ax_mor = self.figure.add_subplot(2,5,3)
    #     self.ax_irradiance = self.figure.add_subplot(2,5,4)
    #     self.ax_obstacle_group = self.figure.add_subplot(2,5,5)

    #     self.ax_particle_density = self.figure.add_subplot(2,5,6)
    #     self.ax_air_temperature = self.figure.add_subplot(2,5,7)
    #     self.ax_relative_humidity = self.figure.add_subplot(2,5,8)
    #     self.ax_barometric_pressure = self.figure.add_subplot(2,5,9)
    #     self.ax_wind = self.figure.add_subplot(2,5,10)

    # def _set_axes_4_5(self):
    #     self.ax_precipitation = self.figure.add_subplot(2,20,(1,5))
    #     self.ax_transmittance5m = self.figure.add_subplot(2,20,(6,10))
    #     self.ax_mor = self.figure.add_subplot(2,20,(11,15))
    #     self.ax_obstacle_group = self.figure.add_subplot(2,20,(16,20))

    #     self.ax_particle_density = self.figure.add_subplot(2,20,(21,24))
    #     self.ax_air_temperature = self.figure.add_subplot(2,20,(25,28))
    #     self.ax_relative_humidity = self.figure.add_subplot(2,20,(29,32))
    #     self.ax_barometric_pressure = self.figure.add_subplot(2,20,(33,36))
    #     self.ax_wind = self.figure.add_subplot(2,20,(37,40))

    def reset(self):
        for _ax in self.figure.axes:
            _ax.clear()

    LINE_COLOR = {'WXT536' : 'tab:green',
                    'PWD10' : 'tab:blue',
                    'LPM' : 'tab:orange',
                    'SR05' : 'tab:olive',
                    'dsrtoutdoor1' : 'tab:purple',
                    'dsrtoutdoor2' : 'tab:pink',
                    'dsrtoutdoor3' : 'tab:red',
                    'dsrtoutdoor5' : 'tab:purple',
                    'dsrtoutdoor1near' : 'orchid',
                    'dsrtoutdoor2near' : 'pink',
                    'dsrtoutdoor3near' : 'tomato',
                    }

    def plot(self, path_data, path_weather, daystr,
                l_sensor_names=['D435'],
                l_system_names=['system0'],
                l_processing_unit_names=['processing_unit_far', 'processing_unit_near'],
                l_path_obstacle_group=None,
                l_path_obstacle_group_prev=None,
                start_time=None,
                duration=None):
        if path_data[-1] != "/": path_data += "/"
        if path_weather[-1] != "/": path_weather += "/"

        monthstr = daystr[:7]
        daystr_prev, monthstr_prev = DataRooftopEquipment.get_previous_daystr(daystr)

        datadir_month = path_data + monthstr + '/'
        weatherdir_month = path_weather + monthstr + '/'

        path_wxt536 = weatherdir_month + 'WXT536_' + daystr + '.txt'
        path_pwd10 = weatherdir_month + 'PWD10_' + daystr + '.txt'
        path_lpm = weatherdir_month + 'ThiesLPM_' + daystr + '.txt'
        path_sr05 = weatherdir_month + 'SR05_' + daystr + '.txt'

        try:
            _color = DataRooftopEquipment.LINE_COLOR.get('WXT536')
            WXT536.plot_csvfile(path_wxt536,
                            l_plot_range=[(0, 30),
                                            (0, 50),
                                            (0, 100),
                                            (950, 1050),
                                            (0, 40)],
                            l_titlestr=['Wind',
                                        'Air Temperature',
                                        'Relative Humidity',
                                        'Barometric Pressure',
                                        'Precipitation'],
                            l_color=[_color, _color, _color, _color, _color],
                            l_ax=[self.ax_wind,
                                    self.ax_air_temperature,
                                    self.ax_relative_humidity,
                                    self.ax_barometric_pressure,
                                    self.ax_precipitation])
        except (OSError, ValueError) as e:
            print(f"{e.__class__.__name__}: {e}")
            _, _, e_trace = sys.exc_info()
            print(f"   at line {e_trace.tb_lineno} in {e_trace.tb_frame.f_code.co_filename}")

        try:
            _color = DataRooftopEquipment.LINE_COLOR.get('PWD10')
            PWD10.plot_csvfile(path_pwd10,
                            l_titlestr=['MOR', 'Spatial Transmittance: 5m'],
                            l_plot_range=[(0,2100), (50,102)],
                            l_color=[_color, _color],
                            l_ax=[self.ax_mor, self.ax_transmittance5m,])
        except (OSError, ValueError) as e:
            print(f"{e.__class__.__name__}: {e}")
            _, _, e_trace = sys.exc_info()
            print(f"   at line {e_trace.tb_lineno} in {e_trace.tb_frame.f_code.co_filename}")

        try:
            _color = DataRooftopEquipment.LINE_COLOR.get('SR05')
            SR05.plot_csvfile(path_sr05,
                            l_titlestr=['Irradiance', 'Air Temperature'],
                            l_plot_range=[(0,1000), (0,50)],
                            l_color=[_color, _color],
                            l_ax=[self.ax_irradiance, self.ax_air_temperature,])
        except (OSError, ValueError) as e:
            print(f"{e.__class__.__name__}: {e}")
            _, _, e_trace = sys.exc_info()
            print(f"   at line {e_trace.tb_lineno} in {e_trace.tb_frame.f_code.co_filename}")

        datadir_month_prev = path_data + monthstr_prev + '/'

        if l_system_names:
            for i, sys_name in enumerate(l_system_names):
                _color = DataRooftopEquipment.LINE_COLOR.get(sys_name)
                _legendstr = re.sub(r'^[a-z]+(\d+)$', r'SYS\1', sys_name)

                if self._internal_environment_p:
                    try:
                        path_env_air_temperature = datadir_month + sys_name +'_air_temperature_' + daystr + '.csv'
                        path_env_air_temperature_prev = datadir_month_prev + sys_name +'_air_temperature_' + daystr_prev + '.csv'
                        #print(path_env_air_temperature)
                        Omron2jciebu.plot_csvfile(path_env_air_temperature,
                                titlestr='Air Temperature',
                                columnstr='temperature',
                                legendstr=_legendstr,
                                color=_color,
                                plot_range=(0,50),
                                previous_day_fpath=path_env_air_temperature_prev,
                                ax=self.ax_air_temperature)
                    except (OSError, ValueError) as e:
                        print(f"{e.__class__.__name__}: {e}")
                        _, _, e_trace = sys.exc_info()
                        print(f"   at line {e_trace.tb_lineno} in {e_trace.tb_frame.f_code.co_filename}")

                    try:
                        path_env_barometric_pressure= datadir_month + sys_name +'_barometric_pressure_' + daystr + '.csv'
                        path_env_barometric_pressure_prev = datadir_month_prev + sys_name +'_barometric_pressure_' + daystr_prev + '.csv'
                        Omron2jciebu.plot_csvfile(path_env_barometric_pressure,
                                titlestr='Barometric Pressure',
                                columnstr='barometric_pressure',
                                legendstr=_legendstr,
                                color=_color,
                                plot_range=(950,1050),
                                previous_day_fpath=path_env_barometric_pressure_prev,
                                ax=self.ax_barometric_pressure)
                    except (OSError, ValueError) as e:
                        print(f"{e.__class__.__name__}: {e}")
                        _, _, e_trace = sys.exc_info()
                        print(f"   at line {e_trace.tb_lineno} in {e_trace.tb_frame.f_code.co_filename}")

                    try:
                        path_env_relative_humidity = datadir_month + sys_name +'_relative_humidity_' + daystr + '.csv'
                        path_env_relative_humidity_prev = datadir_month_prev + sys_name +'_relative_humidity_' + daystr_prev + '.csv'
                        Omron2jciebu.plot_csvfile(path_env_relative_humidity,
                                titlestr='Relative Humidity',
                                columnstr='relative_humidity',
                                legendstr=_legendstr,
                                color=_color,
                                plot_range=(0,100),
                                previous_day_fpath=path_env_relative_humidity_prev,
                                ax=self.ax_relative_humidity)
                    except (OSError, ValueError) as e:
                        print(f"{e.__class__.__name__}: {e}")
                        _, _, e_trace = sys.exc_info()
                        print(f"   at line {e_trace.tb_lineno} in {e_trace.tb_frame.f_code.co_filename}")

                sensor_name = l_sensor_names[i]
                if l_path_obstacle_group is None:
                    _l_path_obstacle_group = [datadir_month + sys_name + '_' + _pun + '_obstacle_group_' + daystr + '.csv' for _pun in l_processing_unit_names]
                else:
                    _l_path_obstacle_group = l_path_obstacle_group

                if l_path_obstacle_group_prev is None:
                    _l_path_obstacle_group_prev = [datadir_month_prev + sys_name + '_' + _pun + '_obstacle_group_' + daystr_prev + '.csv' for _pun in l_processing_unit_names]
                else:
                    _l_path_obstacle_group_prev = l_path_obstacle_group_prev

                _l_legendstr = [_legendstr + _pun.replace('processing_unit','') for _pun in l_processing_unit_names]

                _titlestr = 'Detection Rate: ' + sensor_name

                for _path_og, _path_og_prev, _lstr in zip(_l_path_obstacle_group, _l_path_obstacle_group_prev, _l_legendstr):
                    if 'near' in _lstr:
                        _col = DataRooftopEquipment.LINE_COLOR.get(sys_name +'near')
                    else:
                        _col = _color
                    try:
                        ObstacleGroup.plot_csvfile(_path_og,
                            #titlestr='Detection Rate',
                            titlestr=_titlestr,
                            previous_day_fpath=_path_og_prev,
                            window_for_detection_rate='1h',
                            #window_for_detection_rate=360,
                            #legendstr=sensor_name,
                            #legendstr=_legendstr,
                            legendstr=_lstr,
                            color=_col,
                            plot_range=(0,1.02),
                            ax=self.ax_detection_rates[i],
                            path_image_file=datadir_month + daystr + '/Images/' + sys_name,
                            )
                    except (OSError, ValueError) as e:
                        print(f"{e.__class__.__name__}: {e}")
                        _, _, e_trace = sys.exc_info()
                        print(f"   at line {e_trace.tb_lineno} in {e_trace.tb_frame.f_code.co_filename}")

        try:
            _color = DataRooftopEquipment.LINE_COLOR.get('LPM')
            ThiesLPM.plot_csvfile(path_lpm,
                            l_titlestr=['Particle Density', 'Precipitation', 'MOR', 'Spatial Transmittance: 5m'],
                            l_plot_range=[(0, 20000), (0,40), (0,2100), (50,102)],
                            l_color=[None, _color, _color, _color],
                            l_ax=[self.ax_particle_density,
                                    self.ax_precipitation,
                                    self.ax_mor,
                                    self.ax_transmittance5m])
        except (OSError, ValueError) as e:
            print(f"{e.__class__.__name__}: {e}")
            _, _, e_trace = sys.exc_info()
            print(f"   at line {e_trace.tb_lineno} in {e_trace.tb_frame.f_code.co_filename}")

        if start_time and duration:
            _stime =  pd.to_datetime(start_time, format='%Y-%m-%d-%H-%M-%S').tz_localize('Asia/Tokyo')
            _x_limit = (_stime, _stime + duration)
            for _ax in self.figure.axes:
                _ax.set_xlim(_x_limit)

        for _ax in self.figure.axes:
            _ax.legend(fontsize='x-small')

        plt.tight_layout()

    def show(self):
        plt.show()

    def save(self, path_dst_png):
        self.figure.savefig(path_dst_png)

    @staticmethod
    def get_daystr(day_delta=0,hour_delta=0,minute_delta=0):
        today = datetime.datetime.now() + datetime.timedelta(days=day_delta, hours=hour_delta, minutes=minute_delta)
        return today.strftime('%Y-%m-%d'), today.strftime('%Y-%m')

    @staticmethod
    def get_previous_daystr(daystr):
        date_obj = datetime.datetime.strptime(daystr, '%Y-%m-%d')
        previous_day = date_obj - datetime.timedelta(days=1)
        return previous_day.strftime('%Y-%m-%d'), previous_day.strftime('%Y-%m/')
#'camera_name' : 'D455',
# %%
if __name__ == '__main__':

    #path_data = '/media/dsrt/LaCie/Data/'
    #path_data = '/mnt/monoeyenas0/Public/Data2/'
    path_data = './Data/'
    #paths_obstacle_group = ['./Data/dsrtoutdoor2_obstacle_group_2025-01-07-00-25-15.csv']
    paths_obstacle_group = ['/home/dsrt/ros2_ws/src/emulated_srs/launch/dsrtoutdoor1_obstacle_group_2025-02-16-00-22-36.csv']
    #path_weather = '/media/dsrt/LaCie/Weather/'
    #path_weather = '/mnt/monoeyenas0/Public/Weather/'
    path_weather = './Weather/'
    #datestr = '2024-11-17'
    datestr = '2025-02-16'
    #sensor_names=['D456', 'D456', 'Helios2']
    #sensor_names=['D456']
    sensor_names=['Helios2']
    #system_names=['dsrtoutdoor2', 'dsrtoutdoor3', 'dsrtoutdoor1']
    #system_names=['dsrtoutdoor2']
    system_names=['dsrtoutdoor1']

    #fbase = os.path.splitext(os.path.basename(fpath))[0]

    roof = DataRooftopEquipment(internal_environment_p=False)

    try:
        while True:
            roof.reset()
            roof.plot(path_data, path_weather, datestr, l_sensor_names=sensor_names, l_system_names=system_names,
                      l_path_obstacle_group=paths_obstacle_group,
                      start_time='2025-02-16-00-22-00', 
                      duration=datetime.timedelta(hours=1))
            roof.show()
            plt.pause(10)
            #roof.save('graph.png')
            #print(datetime.datetime.now())
            #roof.save('graph.png', wpath, ppath, tpath, opath, path_env_relative_humidity=orpath)
    except KeyboardInterrupt:
        pass
