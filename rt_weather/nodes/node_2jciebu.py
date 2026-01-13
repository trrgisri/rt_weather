#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@file  env_sensor.py
@brief

@author Yasushi SUMI <y.sumi@aist.go.jp>

Copyright (C) 2022 AIST
Released under the MIT license
https://opensource.org/licenses/mit-license.php
"""

import rclpy
from rclpy.node import Node

import datetime

from sensor_msgs.msg import Temperature
from sensor_msgs.msg import RelativeHumidity
from sensor_msgs.msg import Illuminance

from rt_weather_msgs.msg import BarometricPressure
from rt_weather_msgs.msg import SoundNoise

from rt_weather.instruments.omron_2jciebu import Omron2jciebu

class EnvSensor(Node):
    # LED display rule. Normal Off.
    _DISPLAY_RULE_NORMALLY_OFF = 0

    # LED display rule. Normal On.
    _DISPLAY_RULE_NORMALLY_ON = 0

    def __init__(self, port="/dev/ttyUSB0", rate_hz=1.0, quiet_p=False):
        super().__init__('node_2jciebu')

        self.declare_parameter('port', port)
        self.declare_parameter('rate_hz', rate_hz)
        self.declare_parameter('quiet_p', quiet_p)

        port = self.get_parameter('port').get_parameter_value().string_value

        self._rate_hz = self.get_parameter('rate_hz').get_parameter_value().double_value
        if(self._rate_hz <= 0):
            self.get_logger().error("invalid rate %f" % self._rate_hz)
            raise ValueError(f'>>> Invalid rate: {self._rate_hz}')

        self._quiet_p = self.get_parameter('quiet_p').get_parameter_value().bool_value

        self.get_logger().info(f"Serial: {port}, Rate(Hz) {self._rate_hz}, Quiet:{self._quiet_p}")

        self._serial_device = Omron2jciebu(port)
        self._serial_device.open()

        self._stamp = self.get_clock().now().to_msg()
        self._frame_id = "world"

        self._prev_data = None

        self._temperature = Temperature()
        self._temperature.header.frame_id = self._frame_id
        self._temperature.variance = 0.0
        self._pub_temperature = self.create_publisher(Temperature, 'air_temperature', 10)

        self._humidity = RelativeHumidity()
        self._humidity.header.frame_id = self._frame_id
        self._humidity.variance = 0.0
        self._pub_humidity = self.create_publisher(RelativeHumidity, 'relative_humidity', 10)

        self._illuminance = Illuminance()
        self._illuminance.header.frame_id = self._frame_id
        self._illuminance.variance = 0.0
        self._pub_illuminance = self.create_publisher(Illuminance, 'ambient_light', 10)

        self._pressure = BarometricPressure()
        self._pressure.header.frame_id = self._frame_id
        self._pressure.variance = 0.0
        self._pub_pressure = self.create_publisher(BarometricPressure, 'barometric_pressure', 10)

        self._sound = SoundNoise()
        self._sound.header.frame_id = self._frame_id
        self._sound.variance = 0.0
        self._pub_sound = self.create_publisher(SoundNoise, 'sound_noise', 10)

        self.timer = self.create_timer(1.0/self._rate_hz, self.publish)

    def led_on(self):
        return self._serial_device.led_on()

    def led_off(self):
        return self._serial_device.led_off()

    def close(self):
        self._serial_device.close()

    def publish(self):
        """
        publish measured latest value.
        """
        if self._serial_device.is_open == False:
            self.get_logger().error("device is not open")
            return False

        try:
            self._serial_device.receive()
        except (ValueError, RuntimeError) as e:
            self.get_logger().error(f"{e}")
        else:
            _now = self.get_clock().now()
            self._stamp = _now.to_msg()
            if not self._quiet_p:
                _dt = datetime.datetime.fromtimestamp(_now.nanoseconds/1e9).strftime('%Y-%m-%d %H:%M:%S')
                self.get_logger().info(f"Time: {_dt} ----------------------")

            self._temperature.header.stamp = self._stamp
            self._temperature.temperature = self._serial_device.temperature
            self._pub_temperature.publish(self._temperature)
            if not self._quiet_p:
                self.get_logger().info(f"Temperature: {self._temperature.temperature:.2f}")

            self._humidity.header.stamp = self._stamp
            self._humidity.relative_humidity = self._serial_device.relative_humidity
            self._pub_humidity.publish(self._humidity)
            if not self._quiet_p:
                self.get_logger().info(f"RelativeHumidity: {self._humidity.relative_humidity:.2f}")

            self._illuminance.header.stamp = self._stamp
            self._illuminance.illuminance = float(self._serial_device.illuminance)
            self._pub_illuminance.publish(self._illuminance)
            if not self._quiet_p:
                self.get_logger().info(f"Illuminance: {self._illuminance.illuminance:.2f}")

            self._pressure.header.stamp = self._stamp
            self._pressure.barometric_pressure = self._serial_device.barometric_pressure
            self._pub_pressure.publish(self._pressure)
            if not self._quiet_p:
                self.get_logger().info(f"BarometricPressure: {self._pressure.barometric_pressure:.2f}")

            self._sound.header.stamp = self._stamp
            self._sound.sound_noise = self._serial_device.sound_noise
            self._pub_sound.publish(self._sound)
            if not self._quiet_p:
                self.get_logger().info(f"SoundNoise: {self._sound.sound_noise:.2f}")

        return True

def main(args=None):
    rclpy.init(args=args)

    env_sensor = EnvSensor()
    env_sensor.led_off()

    try:
        rclpy.spin(env_sensor)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        env_sensor.get_logger().error(">>> Exception: %r" %(e,))
    finally:
        rclpy.try_shutdown()
        env_sensor.close()
        env_sensor.destroy_node()
        #rclpy.shutdown()

if __name__ == '__main__':
    main()

