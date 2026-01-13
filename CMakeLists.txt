cmake_minimum_required(VERSION 3.12)

project(rt_weather)
set(CMAKE_VERBOSE_MAKEFILE 1)
find_package(ament_cmake REQUIRED)
find_package(std_msgs REQUIRED)
find_package(rosidl_default_generators REQUIRED)

set(msg_files
  "msg/Transmittance.msg"
  "msg/SpectralTransmittance.msg"
  "msg/BarometricPressure.msg"
  "msg/SoundNoise.msg"
)

rosidl_generate_interfaces(${PROJECT_NAME}
  ${msg_files}
  DEPENDENCIES std_msgs
)

ament_export_dependencies(rosidl_default_runtime)

ament_package()
