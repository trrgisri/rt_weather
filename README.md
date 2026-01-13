# rt_weather

This ROS 2 package provides nodes that acquire meteorological data which may affect the performance of UAV and UGV sensors.
The acquired data are stored locally in files and are also published as ROS topics.

## Features

- Provides dedicated ROS 2 nodes for each meteorological instrument
- Logs observation data to local files and publishes them as ROS topics

## Supported Meteorological Instruments and Sensors

| Instruments/Sensors | Measurements | Node |
|---|---|---|
| Thies CLIMA LPM | PSVD (Particle Size and Velocity Distribution) | `node_thies_lpm` |
| Vaisala PWD10 | MOR (Meteorological Optical Range) | `node_pwd10` |
| Hukseflux SR05 | Solar irradiance | `node_sr05` |
| Vaisala WXT536 | Air temperature, Relative humidity, Air pressure, Precipitation, Wind speed/direction | `node_wxt536` |
| Omron 2JCIE-BU | Air temperature, Relative humidity, Air pressure, Illuminance | `node_2jciebu` |

## Dependencies

### ROS 2

- [`rt_weather_msgs`](https://github.com/trrgisri/rt_weather_msgs.git)
- `rclpy`, `std_msgs`
- `ament_python`, `ament_cmake`
- `rosidl_default_runtime`, `rosidl_default_generators`

### Python

- `pyserial`, `openpyxl`, `pymodbus (==3.7.4)`, `seaborn`

## Installation

```bash
cd <ROS2 WS>/src
git clone https://github.com/trrgisri/rt_weather.git
git clone https://github.com/trrgisri/rt_weather_msgs.git
cd ../
rosdep update
rosdep install --from-paths . --ignore-src -y
colcon build --symlink-install
source install/setup.bash
```

## Usage

### Launch all nodes

```bash
ros2 launch rt_weather rt_weather_launch.py
```

### Launch individual nodes

```bash
ros2 run rt_weather node_xxxxxx
```

## Logging

Each node records a one-line telegram received from its instrument, removing any control characters and adding a timestamp of the reception time at the beginning of the line:

> [YYYY-MM-DD hh:mm:ss.sss] <telegram_text>

## License

MIT license

## Maintainer

Yasushi Sumi (<y.sumi@aist.go.jp>)
