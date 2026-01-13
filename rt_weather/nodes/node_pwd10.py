#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file  node_pwd10.py
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

from rt_weather_msgs.msg import MeteorologicalOpticalRange as MOR

from rt_weather.instruments.pwd10 import PWD10
#from rt_weather.instruments.pwd10 import PWD10_debug as PWD10

class NodePWD10(Node):
    def __init__(self, port="/dev/ttyUSB0",
                    log_directory=PWD10.LOG_DIRECTORY, log_basename=PWD10.DEVICE_NAME,
                    rate_hz=1.0, quiet_p=False, save_p=True):
        super().__init__('node_pwd10')

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

        self.get_logger().info(f"PWD10 Port: {port}, LOGDIR: {self.log_directory}, LOGBASE: {self.log_basename}, Hz: {self.rate_hz}, Quiet:{self.quiet_p}, Save:{self.save_p}")

        self.serial_device = PWD10(port)
        self.serial_device.open()

        #self._stamp = self.get_clock().now().to_msg()
        self._frame_id = "world"

        self.mor_1min = MOR()
        self.mor_1min.header.frame_id = self._frame_id
        self.mor_1min.meteorological_optical_range = 0.0
        self.mor_1min.variance = 0.0
        self._pub_mor_1min = self.create_publisher(MOR, 'mor_1min', 10)

        self.mor_10min = MOR()
        self.mor_10min.header.frame_id = self._frame_id
        self.mor_10min.meteorological_optical_range = 0.0
        self.mor_10min.variance = 0.0
        self._pub_mor_10min = self.create_publisher(MOR, 'mor_10min', 10)

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

    def _publish_mor_1min(self, mor: float, time_mor: Time):
        #self._nowday = dic_wind.index[0]
        #_now = NodePWD10._ts2time(self._nowday)
        #_now = NodePWD10._datetime2rostime(time_mor)
        self.mor_1min.header.stamp = time_mor.to_msg()
        self.mor_1min.meteorological_optical_range = mor
        self._pub_mor_1min.publish(self.mor_1min)


    def _publish_mor_10min(self, mor: float, time_mor: Time):
        self.mor_10min.header.stamp = time_mor.to_msg()
        self.mor_10min.meteorological_optical_range = mor
        self._pub_mor_10min.publish(self.mor_10min)


    def publish(self):
        """
        publish measured latest value.
        """
        if self.serial_device.is_open == False:
            self.get_logger().error("device is not open")
            return False

        try:
            _telegramstr, _telegram_datetime = self.serial_device.receive()
            #print(_telegramstr)
            if _telegramstr is None:
                return False

            _l_mor = PWD10.retrieve(_telegramstr)
        except (ValueError, RuntimeError) as e:
            self.get_logger().error(f"{e}")
        else:
            if _l_mor[0] != 0:
                self.get_logger().error(f"Error code: {_l_mor[0]}")
            else:
                _mor_1min = float(_l_mor[1])
                _mor_10min = float(_l_mor[2])
                _rostime = NodePWD10._datetime2rostime(_telegram_datetime)

                self._publish_mor_1min(_mor_1min, _rostime)
                self._publish_mor_10min(_mor_10min, _rostime)

                if not self.quiet_p:
                    _dt = _telegram_datetime.strftime('%Y-%m-%d %H:%M:%S')
                    self.get_logger().info(f"Time: {_dt} ----------------------")
                    self.get_logger().info(f"MOR [1min]: {_mor_1min:.2f}")
                    self.get_logger().info(f"MOR [10min]: {_mor_10min:.2f}")

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

    pwd10 = NodePWD10()

    try:
        rclpy.spin(pwd10)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        pwd10.get_logger().error(">>> Exception: %r" %(e,))
    finally:
        rclpy.try_shutdown()
        pwd10.close()
        pwd10.destroy_node()
        #rclpy.shutdown()

if __name__ == '__main__':
    main()
