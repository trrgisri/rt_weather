#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file  node_wxt536.py
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

from sensor_msgs.msg import Temperature, RelativeHumidity
from rt_weather_msgs.msg import BarometricPressure, Wind
from rt_weather_msgs.msg import PrecipitationRate, CumulativePrecipitation
from rt_weather_msgs.msg import HailfallRate, CumulativeHailfall

from rt_weather.instruments.wxt536 import WXT536
#from rt_weather.instruments.wxt536 import WXT536_debug as WXT536

class NodeWXT536(Node):
    def __init__(self, port="/dev/ttyUSB0",
                    log_directory=WXT536.LOG_DIRECTORY, log_basename=WXT536.DEVICE_NAME,
                    rate_hz=1.0, quiet_p=False, save_p=True):
        super().__init__('node_wxt536')

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

        self.get_logger().info(f"WXT536 Port: {port}, LOGDIR: {self.log_directory}, LOGBASE: {self.log_basename}, Hz: {self.rate_hz}, Quiet:{self.quiet_p}, Save:{self.save_p}")

        self.serial_device = WXT536(port)
        self.serial_device.open()

        self._frame_id = "world"

        self.temperature = Temperature()
        self.temperature.header.frame_id = self._frame_id
        self.temperature.temperature = 0.0
        self.temperature.variance = 0.0
        self._pub_temperature = self.create_publisher(Temperature, 'air_temperature', 10)

        self.relative_humidity = RelativeHumidity()
        self.relative_humidity.header.frame_id = self._frame_id
        self.relative_humidity.relative_humidity = 0.0
        self.relative_humidity.variance = 0.0
        self._pub_relative_humidity = self.create_publisher(RelativeHumidity, 'relative_humidity', 10)

        self.barometric_pressure = BarometricPressure()
        self.barometric_pressure.header.frame_id = self._frame_id
        self.barometric_pressure.barometric_pressure = 0.0
        self.barometric_pressure.variance = 0.0
        self._pub_barometric_pressure = self.create_publisher(BarometricPressure, 'barometric_pressure', 10)

        self.precipitation_rate = PrecipitationRate()
        self.precipitation_rate.header.frame_id = self._frame_id
        self.precipitation_rate.precipitation_rate = 0.0
        self.precipitation_rate.variance = 0.0
        self._pub_precipitation_rate = self.create_publisher(PrecipitationRate, 'precipitation_rate', 10)

        self.cumulative_precipitation = CumulativePrecipitation()
        self.cumulative_precipitation.header.frame_id = self._frame_id
        self.cumulative_precipitation.cumulative_precipitation = 0.0
        self.cumulative_precipitation.duration = 0.0
        self.cumulative_precipitation.variance = 0.0
        self._pub_cumulative_precipitation = self.create_publisher(CumulativePrecipitation, 'cumulative_precipitation', 10)

        self.hailfall_rate = HailfallRate()
        self.hailfall_rate.header.frame_id = self._frame_id
        self.hailfall_rate.hailfall_rate = 0.0
        self.hailfall_rate.variance = 0.0
        self._pub_hailfall_rate = self.create_publisher(HailfallRate, 'hailfall_rate', 10)

        self.cumulative_hailfall = CumulativeHailfall()
        self.cumulative_hailfall.header.frame_id = self._frame_id
        self.cumulative_hailfall.cumulative_hailfall = 0.0
        self.cumulative_hailfall.duration = 0.0
        self.cumulative_hailfall.variance = 0.0
        self._pub_cumulative_hailfall = self.create_publisher(CumulativeHailfall, 'cumulative_hailfall', 10)

        self.wind = Wind()
        self.wind.header.frame_id = self._frame_id
        self.wind.wind_direction = 0.0
        self.wind.wind_speed = 0.0
        self.wind.variance_wind_direction = 0.0
        self.wind.variance_wind_speed = 0.0
        self._pub_wind = self.create_publisher(Wind, 'wind', 10)

        self.wind_min = Wind()
        self.wind_min.header.frame_id = self._frame_id
        self.wind_min.wind_direction = 0.0
        self.wind_min.wind_speed = 0.0
        self.wind_min.variance_wind_direction = 0.0
        self.wind_min.variance_wind_speed = 0.0
        self._pub_wind_min = self.create_publisher(Wind, 'wind_min', 10)

        self.wind_max = Wind()
        self.wind_max.header.frame_id = self._frame_id
        self.wind_max.wind_direction = 0.0
        self.wind_max.wind_speed = 0.0
        self.wind_max.variance_wind_direction = 0.0
        self.wind_max.variance_wind_speed = 0.0
        self._pub_wind_max = self.create_publisher(Wind, 'wind_max', 10)

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

    def _publish_wind(self, dic_wind, time_wind: datetime):
        #self._nowday = dic_wind.index[0]
        #_now = NodeWXT536._ts2time(self._nowday)
        _now = NodeWXT536._datetime2rostime(time_wind)

        #self._wind.wind_direction = df_wind.loc[df_wind.index[0],['Dn', 'Dm', 'Dx']].tolist()
        #self._wind.wind_speed = df_wind.loc[df_wind.index[0],['Sn', 'Sm', 'Sx']].tolist()
        #self.wind.wind_direction = [dic_wind[k] for k in ['Dn', 'Dm', 'Dx']]
        #self.wind.wind_speed = [dic_wind[k] for k in ['Sn', 'Sm', 'Sx']]
        self.wind.header.stamp = _now.to_msg()
        self.wind.wind_direction = dic_wind['Dm']
        self.wind.wind_speed = dic_wind['Sm']
        self._pub_wind.publish(self.wind)

        self.wind_min.header.stamp = _now.to_msg()
        self.wind_min.wind_direction = dic_wind['Dn']
        self.wind_min.wind_speed = dic_wind['Sn']
        self._pub_wind_min.publish(self.wind_min)

        self.wind_max.header.stamp = _now.to_msg()
        self.wind_max.wind_direction = dic_wind['Dx']
        self.wind_max.wind_speed = dic_wind['Sx']
        self._pub_wind_max.publish(self.wind_max)

    def _print_loginfo_wind(self, time_wind: datetime):
        if not self.quiet_p:
            _dt = time_wind.strftime('%Y-%m-%d %H:%M:%S')
            self.get_logger().info(f"Time: {_dt} ----------------------")
            self.get_logger().info(f"Wind Speed: {self.wind.wind_speed:.2f}")
            self.get_logger().info(f"Wind Direction: {self.wind.wind_direction:.2f}")

    def _publish_air(self, dic_air, time_air: datetime):
        #self._nowday = df_air.index[0]
        #_now = NodeWXT536._ts2time(self._nowday)
        #self._stamp = _now.to_msg()
        _now = NodeWXT536._datetime2rostime(time_air)
        _now_msg = _now.to_msg()

        self.temperature.header.stamp = _now_msg
        self.temperature.temperature = dic_air['Ta']
        self._pub_temperature.publish(self.temperature)

        self.relative_humidity.header.stamp = _now_msg
        self.relative_humidity.relative_humidity = dic_air['Ua']
        self._pub_relative_humidity.publish(self.relative_humidity)

        self.barometric_pressure.header.stamp = _now_msg
        self.barometric_pressure.barometric_pressure = dic_air['Pa']
        self._pub_barometric_pressure.publish(self.barometric_pressure)

    def _print_loginfo_air(self, time_air: datetime):
        if not self.quiet_p:
            _dt = time_air.strftime('%Y-%m-%d %H:%M:%S')
            self.get_logger().info(f"Time: {_dt} ----------------------")
            self.get_logger().info(f"Air Temperature: {self.temperature.temperature:.2f}")
            self.get_logger().info(f"Relative Humidity: {self.relative_humidity.relative_humidity:.2f}")
            self.get_logger().info(f"Barometric Pressure: {self.barometric_pressure.barometric_pressure:.2f}")

    def _publish_prec(self, dic_prec, time_prec: datetime):
        # self._nowday = df_prec.index[0]
        # _now = NodeWXT536._ts2time(self._nowday)
        # self._stamp = _now.to_msg()

        _now = NodeWXT536._datetime2rostime(time_prec)
        _now_msg = _now.to_msg()

        self.precipitation_rate.header.stamp = _now_msg
        self.precipitation_rate.precipitation_rate = dic_prec['Ri']
        self._pub_precipitation_rate.publish(self.precipitation_rate)

        self.cumulative_precipitation.header.stamp = _now_msg
        self.cumulative_precipitation.cumulative_precipitation = dic_prec['Rc']
        self.cumulative_precipitation.duration = dic_prec['Rd']
        self._pub_cumulative_precipitation.publish(self.cumulative_precipitation)

        self.hailfall_rate.header.stamp = _now_msg
        self.hailfall_rate.hailfall_rate = dic_prec['Hi']
        self._pub_hailfall_rate.publish(self.hailfall_rate)

        self.cumulative_hailfall.header.stamp = _now_msg
        self.cumulative_hailfall.cumulative_hailfall = dic_prec['Hc']
        self.cumulative_hailfall.duration = dic_prec['Hd']
        self._pub_cumulative_hailfall.publish(self.cumulative_hailfall)

    def _print_loginfo_prec(self, time_prec: datetime):
        if not self.quiet_p:
            _dt = time_prec.strftime('%Y-%m-%d %H:%M:%S')
            self.get_logger().info(f"Time: {_dt} ----------------------")
            self.get_logger().info(f"Precipitation rate: {self.precipitation_rate.precipitation_rate:.2f}")
            self.get_logger().info(f"Cumulative precipitation: {self.cumulative_precipitation.cumulative_precipitation:.2f}")
            self.get_logger().info(f"Hailfall rate: {self.hailfall_rate.hailfall_rate:.2f}")
            self.get_logger().info(f"Cumulative hailfall: {self.cumulative_hailfall.cumulative_hailfall:.2f}")

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

            _dic = WXT536.retrieve(_telegramstr)
        except (ValueError, RuntimeError) as e:
            self.get_logger().error(f"{e}")
        else:
            # _now = self.get_clock().now()
            # self._stamp = _now.to_msg()
            # if not self._quiet_p:
            #     _dt = datetime.datetime.fromtimestamp(_now.nanoseconds/1e9).strftime('%Y-%m-%d %H:%M:%S')
            #     self.get_logger().info(f"Time: {_dt} ----------------------")
            if 'ID' in _dic:
                try:
                    _is_received = True
                    if _dic['ID'] == '0R1':
                        self._publish_wind(_dic, _telegram_datetime)
                        self._print_loginfo_wind(_telegram_datetime)
                    elif _dic['ID'] == '0R2':
                        self._publish_air(_dic, _telegram_datetime)
                        self._print_loginfo_air(_telegram_datetime)
                    elif _dic['ID'] == '0R3':
                        self._publish_prec(_dic, _telegram_datetime)
                        self._print_loginfo_prec(_telegram_datetime)
                    else:
                        _is_received = False
                except KeyError as e:
                    self.get_logger().error(f"{e}")
                else:
                    if self.save_p and _is_received:
                        #_nowday = self._nowday.to_pydatetime().replace(tzinfo=None)
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

    wxt536 = NodeWXT536()

    try:
        rclpy.spin(wxt536)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        wxt536.get_logger().error(">>> Exception: %r" %(e,))
    finally:
        rclpy.try_shutdown()
        wxt536.close()
        wxt536.destroy_node()
        #rclpy.shutdown()

if __name__ == '__main__':
    main()
