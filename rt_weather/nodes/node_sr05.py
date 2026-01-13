#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file  node_sr05.py
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

from sensor_msgs.msg import Temperature
from rt_weather_msgs.msg import Irradiance

from rt_weather.instruments.sr05 import SR05
#from rt_weather.instruments.sr05 import SR05_debug as SR05

class NodeSR05(Node):
    def __init__(self, port="/dev/ttyUSB0",
                    log_directory=SR05.LOG_DIRECTORY, log_basename=SR05.DEVICE_NAME,
                    rate_hz=1.0, quiet_p=False, save_p=True):
        super().__init__('node_sr05')

        self.declare_parameter('port', port)
        self.declare_parameter('log_directory', log_directory)
        self.declare_parameter('log_basename', log_basename)
        self.declare_parameter('rate_hz', rate_hz)
        self.declare_parameter('quiet_p', quiet_p)
        self.declare_parameter('save_p', save_p)

        port = self.get_parameter('port').get_parameter_value().string_value
        self.log_directory = self.get_parameter('log_directory').get_parameter_value().string_value
        self.log_basename = self.get_parameter('log_basename').get_parameter_value().string_value
        self.rate_hz = self.get_parameter('rate_hz').get_parameter_value().double_value
        self.quiet_p = self.get_parameter('quiet_p').get_parameter_value().bool_value
        self.save_p = self.get_parameter('save_p').get_parameter_value().bool_value

        self.get_logger().info(f"SR05 Port: {port}, LOGDIR: {self.log_directory}, LOGBASE: {self.log_basename}, Hz: {self.rate_hz}, Quiet:{self.quiet_p}, Save:{self.save_p}")

        self.serial_device = SR05(port)
        self.serial_device.open()

        self._stamp = self.get_clock().now().to_msg()
        self._frame_id = "world"

        self.temperature = Temperature()
        self.temperature.header.frame_id = self._frame_id
        self.temperature.temperature = 0.0
        self.temperature.variance = 0.0
        self._pub_temperature = self.create_publisher(Temperature, 'air_temperature', 10)

        self.irradiance = Irradiance()
        self.irradiance.header.frame_id = self._frame_id
        self.irradiance.irradiance = 0.0
        self.irradiance.variance = 0.0
        self._pub_irradiance = self.create_publisher(Irradiance, 'solar_irradiance', 10)

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

    # convert datetime to rclpy.time.Time
    @staticmethod
    def _datetime2ros(dt):
        if dt.tzinfo is None:
            dt_utc = dt.replace(tzinfo=timezone.utc)
        else:
            dt_utc = dt.astimezone(timezone.utc)
        sec = int(dt_utc.timestamp())
        nsec = int(dt_utc.microsecond * 1000)
        return Time(seconds=sec, nanoseconds=nsec)

    def publish(self):
        """
        publish measured latest value.
        """
        if self.serial_device.is_open == False:
            self.get_logger().error("device is not open")
            return False

        try:
            _telegramstr, _telegram_datetime = self.serial_device.receive()
            if _telegramstr is None:
                return False

            _irradiance, _temperature = SR05.retrieve(_telegramstr)
        except (ValueError, RuntimeError) as e:
            self.get_logger().error(f"{e}")
        else:
            #_now = self.get_clock().now()
            _now = self._datetime2ros(_telegram_datetime)
            self._stamp = _now.to_msg()
            if not self.quiet_p:
                #_dt = _telegram_datetime.fromtimestamp(_now.nanoseconds/1e9).strftime('%Y-%m-%d %H:%M:%S')
                _dt = _telegram_datetime.strftime('%Y-%m-%d %H:%M:%S')
                self.get_logger().info(f"Time: {_dt} ----------------------")

            self.temperature.header.stamp = self._stamp
            #self._temperature.temperature = self._serial_device.temperature
            self.temperature.temperature = _temperature
            self._pub_temperature.publish(self.temperature)
            if not self.quiet_p:
                self.get_logger().info(f"Temperature: {self.temperature.temperature:.2f}")

            self.irradiance.header.stamp = self._stamp
            #self._irradiance.irradiance = self._serial_device.irradiance
            self.irradiance.irradiance = _irradiance
            self._pub_irradiance.publish(self.irradiance)
            if not self.quiet_p:
                self.get_logger().info(f"Irradiance: {self.irradiance.irradiance:.2f}")

            if self.save_p:
                #_nowday = self._serial_device.datetime
                if  _telegram_datetime.date() > self._current_date:
                    _monthly_log_directory = self.log_directory + _telegram_datetime.strftime('%Y-%m/')
                    self._logfile = self.serial_device.create_new_logfile(self._logfile, self.log_basename, _monthly_log_directory)
                    self._current_date = _telegram_datetime.date()
                self.serial_device.write_log(_telegramstr, self._logfile, received_datetime=_telegram_datetime)

        return True

def main(args=None):
    rclpy.init(args=args)

    sr05 = NodeSR05()

    try:
        rclpy.spin(sr05)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        sr05.get_logger().error(">>> Exception: %r" %(e,))
    finally:
        rclpy.try_shutdown()
        sr05.close()
        sr05.destroy_node()
        #rclpy.shutdown()

if __name__ == '__main__':
    main()

