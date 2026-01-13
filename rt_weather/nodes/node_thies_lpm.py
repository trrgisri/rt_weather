#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file  node_this_lpm.py
@brief

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2025 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import rclpy
from rclpy.node import Node
from rclpy.time import Time

from datetime import datetime, timezone
import pandas as pd
import numpy as np

from rt_weather_msgs.msg import ParticleSizeVelocityDistribution as PSVD
from rt_weather_msgs.msg import MeteorologicalOpticalRange as MOR
from rt_weather_msgs.msg import ParticleDensity, PrecipitationRate

from rt_weather.instruments.thies_lpm import ThiesLPM
#from rt_weather.instruments.thies_lpm import ThiesLPM_debug as ThiesLPM

class NodeThiesLPM(Node):
    def __init__(self, port="/dev/ttyUSB0",
                    log_directory=ThiesLPM.LOG_DIRECTORY, log_basename=ThiesLPM.DEVICE_NAME,
                    rate_hz=1.0, quiet_p=False, save_p=True):
        super().__init__('node_ThiesLPM')

        self.declare_parameter('port', port)
        self.declare_parameter('log_directory', log_directory)
        self.declare_parameter('log_basename', log_basename)
        self.declare_parameter('rate_hz', rate_hz)
        self.declare_parameter('quiet_p', quiet_p)
        self.declare_parameter('save_p', save_p)
        #self.declare_parameter('timezone', timezone)

        port = self.get_parameter('port').get_parameter_value().string_value
        self.log_directory = self.get_parameter('log_directory').get_parameter_value().string_value
        self.log_basename = self.get_parameter('log_basename').get_parameter_value().string_value
        self.rate_hz = self.get_parameter('rate_hz').get_parameter_value().double_value
        self.quiet_p = self.get_parameter('quiet_p').get_parameter_value().bool_value
        self.save_p = self.get_parameter('save_p').get_parameter_value().bool_value
        #self.timezone = self.get_parameter('timezone').get_parameter_value().string_value

        self.get_logger().info(f"ThiesLPM Port: {port}, LOGDIR: {self.log_directory}, LOGBASE: {self.log_basename}, Hz: {self.rate_hz}, Quiet:{self.quiet_p}, Save:{self.save_p}")

        self.serial_device = ThiesLPM(port)
        self.serial_device.open()

        self._frame_id = "world"

        self.psvd = PSVD()
        self.psvd.header.frame_id = self._frame_id
        self.psvd.n_diameters = len(ThiesLPM.RAINDROP_DIAMETERS)
        self.psvd.n_velocities = len(ThiesLPM.RAINDROP_VELOCITIES)
        self.psvd.diameter_edges = ThiesLPM.RAINDROP_DIAMETER_EDGES
        self.psvd.velocity_edges = ThiesLPM.RAINDROP_VELOCITY_EDGES
        self.psvd.counts = [0] * (self.psvd.n_diameters * self.psvd.n_velocities)
        self._pub_psvd = self.create_publisher(PSVD, 'psvd', 10)

        self.mor = MOR()
        self.mor.header.frame_id = self._frame_id
        self.mor.meteorological_optical_range = 0.0
        self.mor.variance = 0.0
        self._pub_mor = self.create_publisher(MOR, 'mor', 10)

        self.precipitation_rate = PrecipitationRate()
        self.precipitation_rate.header.frame_id = self._frame_id
        self.precipitation_rate.precipitation_rate = 0.0
        self.precipitation_rate.variance = 0.0
        self._pub_precipitation_rate = self.create_publisher(PrecipitationRate, 'precipitation_rate', 10)

        self.particle_density_drizzle = ParticleDensity()
        self.particle_density_drizzle.header.frame_id = self._frame_id
        self.particle_density_drizzle.particle_density = 0.0
        self.particle_density_drizzle.variance = 0.0
        self._pub_particle_density_drizzle = self.create_publisher(ParticleDensity, 'particle_density_drizzle', 10)

        self.particle_density_rain = ParticleDensity()
        self.particle_density_rain.header.frame_id = self._frame_id
        self.particle_density_rain.particle_density = 0.0
        self.particle_density_rain.variance = 0.0
        self._pub_particle_density_rain = self.create_publisher(ParticleDensity, 'particle_density_rain', 10)

        if self.save_p:
            if self.log_directory[-1] != '/': self.log_directory += '/'
            self._current_date = datetime.today().date()
            _monthly_log_directory = self.log_directory + self._current_date.strftime('%Y-%m/')
            self._logfile = self.serial_device.create_new_logfile(None, self.log_basename, _monthly_log_directory)

        self.timer = self.create_timer(1.0/self.rate_hz, self.publish)

        return

    def close(self):
        if self.save_p:
            self.serial_device.close_logfile(self._logfile)
        self.serial_device.close()

    # convert datetime.datetime to rclpy.time.Time
    @staticmethod
    def _datetime2rostime(dt: datetime):
        if dt.tzinfo is None:
            dt_utc = dt.replace(tzinfo=timezone.utc)
        else:
            dt_utc = dt.astimezone(timezone.utc)
        sec = int(dt_utc.timestamp())
        nsec = int(dt_utc.microsecond * 1000)
        return Time(seconds=sec, nanoseconds=nsec)

    def _publish_psvd(self, psvd: pd.DataFrame, time_psvd: Time):
        self.psvd.header.stamp = time_psvd.to_msg()
        self.psvd.counts = psvd.to_numpy(dtype=np.uint32, copy=False).ravel(order='C').tolist()
        self._pub_psvd.publish(self.psvd)

    def _publish_particle_density_drizzle(self, pd_drizzle: float, time_pd: Time):
        self.particle_density_drizzle.header.stamp = time_pd.to_msg()
        self.particle_density_drizzle.particle_density = pd_drizzle
        self._pub_particle_density_drizzle.publish(self.particle_density_drizzle)

    def _publish_particle_density_rain(self, pd_rain: float, time_pd: Time):
        self.particle_density_rain.header.stamp = time_pd.to_msg()
        self.particle_density_rain.particle_density = pd_rain
        self._pub_particle_density_rain.publish(self.particle_density_rain)

    def _publish_mor(self, mor: float, time_mor: Time):
        self.mor.header.stamp = time_mor.to_msg()
        self.mor.meteorological_optical_range = mor
        self._pub_mor.publish(self.mor)

    def _publish_precipitation_rate(self, prec: float, time_prec: Time):
        self.precipitation_rate.header.stamp = time_prec.to_msg()
        self.precipitation_rate.precipitation_rate = prec
        self._pub_precipitation_rate.publish(self.precipitation_rate)

    def _print_loginfo(self, telegram_datetime: datetime):
        _dt = telegram_datetime.strftime('%Y-%m-%d %H:%M:%S')
        self.get_logger().info(f"Time: {_dt} ----------------------")
        self.get_logger().info(f"PSVD: {self.psvd.counts}")
        self.get_logger().info(f"MOR: {self.mor.meteorological_optical_range:.2f}")
        self.get_logger().info(f"Precipitation rate: {self.precipitation_rate.precipitation_rate:.2f}")
        self.get_logger().info(f"PD drizzle: {self.particle_density_drizzle.particle_density}")
        self.get_logger().info(f"PD rain: {self.particle_density_rain.particle_density}")

    def publish(self):
        if self.serial_device.is_open == False:
            self.get_logger().error("device is not open")
            return False

        try:
            _telegramstr, _telegram_datetime = self.serial_device.receive()
            #print(_telegramstr)
            if _telegramstr is None:
                return False

            _prec, _psvd, _ser_props = ThiesLPM.retrieve(_telegramstr)
            #_datetime = _pd_datetime.to_pydatetime()
            #print(_datetime, type(_datetime))
        except (ValueError, RuntimeError) as e:
            self.get_logger().error(f"{e}")
        else:
            _rostime = NodeThiesLPM._datetime2rostime(_telegram_datetime)
            self._publish_psvd(_psvd, _rostime)
            self._publish_mor(_ser_props['MOR'], _rostime)
            self._publish_precipitation_rate(_prec, _rostime)
            self._publish_particle_density_drizzle(_ser_props['<1mm'], _rostime)
            self._publish_particle_density_rain(_ser_props['>=1mm'], _rostime)

            if not self.quiet_p:
                self._print_loginfo(_telegram_datetime)

            if self.save_p:
                if  _telegram_datetime.date() > self._current_date:
                    _monthly_log_directory = self.log_directory + _telegram_datetime.strftime('%Y-%m/')
                    self._logfile = self.serial_device.create_new_logfile(self._logfile, self.log_basename, _monthly_log_directory)
                    self.serial_device.write_log(_telegramstr, self._logfile)
                    self._current_date = _telegram_datetime.date()
                else:
                    self.serial_device.write_log(_telegramstr, self._logfile)

        return True

def main(args=None):
    rclpy.init(args=args)

    thies_lpm = NodeThiesLPM()

    try:
        rclpy.spin(thies_lpm)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        thies_lpm.get_logger().error(">>> Exception: %r" %(e,))
    finally:
        rclpy.try_shutdown()
        thies_lpm.close()
        thies_lpm.destroy_node()
        #rclpy.shutdown()

if __name__ == '__main__':
    main()
