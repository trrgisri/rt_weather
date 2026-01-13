#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file   rt_weather_launch.py
@brief  Launches multiple weather observation nodes.

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2025 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
import os

def generate_launch_description():
    # General
    _hostname = os.uname()[1]
    system_name = LaunchConfiguration('system_name', default=_hostname)
    dirname_weather = LaunchConfiguration('dirname_weather', default='/mnt/monoeyenas0/Public/Weather')
    save_p = LaunchConfiguration('save_p', default='true')
    quiet_p = LaunchConfiguration('quiet_p', default='true')

    ##
    # omron_2jciebu node
    #
    omron_2jciebu_name = LaunchConfiguration('omron_2jciebu_name', default='omron2jcie')
    topic_2jciebu_temperature = ['/', system_name, '/', omron_2jciebu_name, '/air_temperature']
    topic_2jciebu_light = ['/', system_name, '/', omron_2jciebu_name, '/ambient_light']
    topic_2jciebu_pressure = ['/', system_name, '/', omron_2jciebu_name, '/barometric_pressure']
    topic_2jciebu_humidity = ['/', system_name, '/', omron_2jciebu_name, '/relative_humidity']
    topic_2jciebu_noise = ['/', system_name, '/', omron_2jciebu_name, '/sound_noise']

    node_omron_2jciebu = Node(
        package='rt_weather',
        namespace=system_name,
        executable='node_2jciebu',
        output='both',
        respawn=True,
        parameters=[
            {
                'port': LaunchConfiguration('dev_omron_2jciebu'),
                'log_directory' : dirname_weather,
                'log_basename' : LaunchConfiguration('basename_omron_2jciebu'),
                'rate_hz': LaunchConfiguration('fps_omron_2jciebu'),
                #'save_p': save_p, # not supported yet
                'quiet_p': quiet_p,
                #'qos':qos,
            }
        ],
        remappings=[
            ('air_temperature', topic_2jciebu_temperature),
            ('ambient_light', topic_2jciebu_light),
            ('barometric_pressure', topic_2jciebu_pressure),
            ('relative_humidity', topic_2jciebu_humidity),
            ('sound_noise', topic_2jciebu_noise),
        ],
        condition=IfCondition(LaunchConfiguration('exec_omron_2jciebu_p')),
    )

    ##
    # PWD10 node
    #
    pwd10_name = LaunchConfiguration('pwd10_name', default='pwd10')
    topic_pwd10_mor_1min = ['/', system_name, '/', pwd10_name, '/mor_1min']
    topic_pwd10_mor_10min = ['/', system_name, '/', pwd10_name, '/mor_10min']

    node_pwd10 = Node(
        package='rt_weather',
        namespace=system_name,
        executable='node_pwd10',
        output='both',
        respawn=True,
        parameters=[
            {
                'port': LaunchConfiguration('dev_pwd10'),
                'log_directory' : dirname_weather,
                'log_basename' : LaunchConfiguration('basename_pwd10'),
                'rate_hz': LaunchConfiguration('fps_pwd10'),
                'save_p': save_p,
                'quiet_p': quiet_p,
            }
        ],
        remappings=[
            ('mor_1min', topic_pwd10_mor_1min),
            ('mor_10min', topic_pwd10_mor_10min),
        ],
        condition=IfCondition(LaunchConfiguration('exec_pwd10_p')),
    )

    ##
    # WXT356 node
    #
    wxt536_name = LaunchConfiguration('wxt536_name', default='wxt536')
    topic_wxt536_temperature = ['/', system_name, '/', wxt536_name, '/air_temperature']
    topic_wxt536_humidity = ['/', system_name, '/', wxt536_name, '/relative_humidity']
    topic_wxt536_pressure = ['/', system_name, '/', wxt536_name, '/barometric_pressure']
    topic_wxt536_precipitation_rate = ['/', system_name, '/', wxt536_name, '/precipitation_rate']
    topic_wxt536_cumulative_precipitation = ['/', system_name, '/', wxt536_name, '/cumulative_precipitation']
    topic_wxt536_hailfall_rate = ['/', system_name, '/', wxt536_name, '/hailfall_rate']
    topic_wxt536_cumulative_hailfall = ['/', system_name, '/', wxt536_name, '/cumulative_hailfall']
    topic_wxt536_wind = ['/', system_name, '/', wxt536_name, '/wind']
    topic_wxt536_wind_min = ['/', system_name, '/', wxt536_name, '/wind_min']
    topic_wxt536_wind_max = ['/', system_name, '/', wxt536_name, '/wind_max']

    node_wxt536 = Node(
        package='rt_weather',
        namespace=system_name,
        executable='node_wxt536',
        output='both',
        respawn=True,
        parameters=[
            {
                'port': LaunchConfiguration('dev_wxt536'),
                'log_directory' : dirname_weather,
                'log_basename' : LaunchConfiguration('basename_wxt536'),
                'rate_hz': LaunchConfiguration('fps_wxt536'),
                'save_p': save_p,
                'quiet_p': quiet_p,
            }
        ],
        remappings=[
            ('air_temperature', topic_wxt536_temperature),
            ('relative_humidity', topic_wxt536_humidity),
            ('barometric_pressure', topic_wxt536_pressure),
            ('precipitation_rate', topic_wxt536_precipitation_rate),
            ('cumulative_precipitation', topic_wxt536_cumulative_precipitation),
            ('hailfall_rate', topic_wxt536_hailfall_rate),
            ('cumulative_hailfall', topic_wxt536_cumulative_hailfall),
            ('wind', topic_wxt536_wind),
            ('wind_min', topic_wxt536_wind_min),
            ('wind_max', topic_wxt536_wind_max),
        ],
        condition=IfCondition(LaunchConfiguration('exec_wxt536_p'))
    )

    ##
    # Thies LPM node
    #
    thies_lpm_name = LaunchConfiguration('thies_lpm_name', default='thies_lpm')
    topic_thies_lpm_pd_drizzle = ['/', system_name, '/', thies_lpm_name, '/particle_density_drizzle']
    topic_thies_lpm_pd_rain = ['/', system_name, '/', thies_lpm_name, '/particle_density_rain']
    topic_thies_lpm_psvd = ['/', system_name, '/', thies_lpm_name, '/psvd']
    topic_thies_lpm_mor = ['/', system_name, '/', thies_lpm_name, '/mor']
    topic_thies_lpm_precipitation_rate = ['/', system_name, '/', thies_lpm_name, '/precipitation_rate']

    node_thies_lpm = Node(
        package='rt_weather',
        namespace=system_name,
        executable='node_thies_lpm',
        output='both',
        respawn=True,
        parameters=[
            {
                'port': LaunchConfiguration('dev_thies_lpm'),
                'log_directory' : dirname_weather,
                'log_basename' : LaunchConfiguration('basename_thies_lpm'),
                'rate_hz': LaunchConfiguration('fps_thies_lpm'),
                'save_p': save_p,
                'quiet_p': quiet_p,
            }
        ],
        remappings=[
            ('particle_density_drizzle', topic_thies_lpm_pd_drizzle),
            ('particle_density_rain', topic_thies_lpm_pd_rain),
            ('psvd', topic_thies_lpm_psvd),
            ('mor', topic_thies_lpm_mor),
            ('precipitation_rate', topic_thies_lpm_precipitation_rate),
        ],
        condition=IfCondition(LaunchConfiguration('exec_thies_lpm_p'))
    )

    ##
    # SR05 node
    #
    sr05_name = LaunchConfiguration('sr05_name', default='sr05')
    topic_sr05_temperature = ['/', system_name, '/', sr05_name, '/air_temperature']
    topic_sr05_irradiance = ['/', system_name, '/', sr05_name, '/solar_irradiance']

    node_sr05 = Node(
        package='rt_weather',
        namespace=system_name,
        executable='node_sr05',
        output='both',
        respawn=True,
        parameters=[
            {
                'port': LaunchConfiguration('dev_sr05'),
                'log_directory' : dirname_weather,
                'log_basename' : LaunchConfiguration('basename_sr05'),
                'rate_hz': LaunchConfiguration('fps_sr05'),
                'save_p': save_p,
                'quiet_p': quiet_p,
            }
        ],
        remappings=[
            ('air_temperature', topic_sr05_temperature),
            ('solar_irradiance', topic_sr05_irradiance),
        ],
        condition=IfCondition(LaunchConfiguration('exec_sr05_p')),
    )

    return LaunchDescription([
        # General arguments
        DeclareLaunchArgument(
            'system_name', default_value=_hostname,
            description='namespace for the system'
        ),
        DeclareLaunchArgument(
            'dirname_weather',
            default_value='/mnt/monoeyenas0/Public/Weather',
            description='directory path saved weather data files',
        ),
        DeclareLaunchArgument(
            'save_p', default_value='true',
            description='save received telegrams, if true.'
        ),
        DeclareLaunchArgument(
            'quiet_p', default_value='true',
            description='print received telegrams, if not true.'
        ),

        # Omron 2JCIEBU arguments
        DeclareLaunchArgument(
            'omron_2jciebu_name', default_value='omron2jcie',
            description='name of OMRON 2JCIEBU environmental sensor'
        ),
        DeclareLaunchArgument(
            'basename_omron_2jciebu', default_value='2JCIEBU',
            description='log basename of OMRON 2JCIEBU environmental sensor'
        ),
        DeclareLaunchArgument(
            'dev_omron_2jciebu', default_value='/dev/tty2JCIE_0',
            description='device file for OMRON 2JCIEBU'
        ),
        DeclareLaunchArgument(
            'fps_omron_2jciebu', default_value='1.0',
            description='fps of OMRON 2JCIEBU',
        ),
        DeclareLaunchArgument(
            'exec_omron_2jciebu_p', default_value='false',
            description='exec OMRON 2JCIEBU environmental sensor, if true.'
        ),

        # PWD10 arguments
        DeclareLaunchArgument(
            'pwd10_name', default_value='pwd10',
            description='name of PWD10 MOR meter'
        ),
        DeclareLaunchArgument(
            'basename_pwd10', default_value='PWD10',
            description='log basename of PWD10 MOR meter'
        ),
        DeclareLaunchArgument(
            'dev_pwd10', default_value='/dev/ttyFT4232_B',
            description='device file for PWD10'
        ),
        DeclareLaunchArgument(
            'fps_pwd10', default_value='1.0',
            description='fps of PWD10',
        ),
        DeclareLaunchArgument(
            'exec_pwd10_p', default_value='true',
            description='exec PWD10 MOR sensor, if true.'
        ),

        # WXT536 arguments
        DeclareLaunchArgument(
            'wxt536_name', default_value='wxt536',
            description='name of WXT536 weather meter'
        ),
        DeclareLaunchArgument(
            'basename_wxt536', default_value='WXT536',
            description='log basename of WXT536 weather meter'
        ),
        DeclareLaunchArgument(
            'dev_wxt536', default_value='/dev/ttyFT4232_A',
            description='device file for wxt536'
        ),
        DeclareLaunchArgument(
            'fps_wxt536', default_value='1.0',
            description='fps of WXT536',
        ),
        DeclareLaunchArgument(
            'exec_wxt536_p', default_value='true',
            description='exec PWD10 MOR sensor, if true.'
        ),

        # Thies LPM arguments
        DeclareLaunchArgument(
            'thies_lpm_name', default_value='thies_lpm',
            description='name of Thies LPM disdrometer'
        ),
        DeclareLaunchArgument(
            'basename_thies_lpm', default_value='ThiesLPM',
            description='log basename of Thies LPM disdrometer'
        ),
        DeclareLaunchArgument(
            'dev_thies_lpm', default_value='/dev/ttyFT4232_C',
            description='device file for Thies LPM'
        ),
        DeclareLaunchArgument(
            'fps_thies_lpm', default_value='1.0',
            description='fps of Thies LPM',
        ),
        DeclareLaunchArgument(
            'exec_thies_lpm_p', default_value='true',
            description='exec Thies LPM disdrometer, if true.'
        ),

        # SR05 arguments
        DeclareLaunchArgument(
            'sr05_name', default_value='sr05',
            description='name of SR05 solar irradiance meter'
        ),
        DeclareLaunchArgument(
            'basename_sr05', default_value='SR05',
            description='log basename of SR05 solar irradiance meter'
        ),
        DeclareLaunchArgument(
            'dev_sr05', default_value='/dev/ttyATEN485_A',
            description='device file for SR05'
        ),
        DeclareLaunchArgument(
            'fps_sr05', default_value='0.1',
            description='fps of SR05',
        ),
        DeclareLaunchArgument(
            'exec_sr05_p', default_value='true',
            description='exec SR05 solar irradiance meter, if true.'
        ),

        # Actions
        TimerAction(
            period=0.0,
            actions=[
                node_omron_2jciebu,
            ],
        ),
        TimerAction(
            period=1.0,
            actions=[
                node_pwd10,
            ],
        ),
        TimerAction(
            period=2.0,
            actions=[
                node_wxt536,
            ],
        ),
        TimerAction(
            period=3.0,
            actions=[
                node_thies_lpm,
            ],
        ),
        TimerAction(
            period=4.0,
            actions=[
                node_sr05,
            ],
        ),
    ])
