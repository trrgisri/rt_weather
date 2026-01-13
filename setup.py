from setuptools import find_packages, setup
from glob import glob

package_name = 'rt_weather'

launch_files = glob("launch/*.py")
script_files = glob("scripts/*.py")

data_files = [
    ("share/ament_index/resource_index/packages", [f"resource/{package_name}"]),
    (f"share/{package_name}", ["package.xml", "README.md", "LICENSE"]),
    (f"share/{package_name}/launch", launch_files),
]

if script_files:
    data_files.append((f"bin", script_files))

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(include=['rt_weather', 'rt_weather.*']),
    #packages=['rt_weather', 'nodes'],
    data_files=data_files,
    zip_safe=True,
    maintainer='Yasushi Sumi',
    maintainer_email='y.sumi@aist.go.jp',
    description='RT oriented weather observation package',
    license='MIT',
    install_requires=[
        'setuptools',
        'pyserial',
        'seaborn',
        'openpyxl',
        'pymodbus',
    ],
    entry_points={
        'console_scripts': [
            'node_2jciebu = rt_weather.nodes.node_2jciebu:main',
            'node_pwd10 = rt_weather.nodes.node_pwd10:main',
            'node_sr05 = rt_weather.nodes.node_sr05:main',
            'node_thies_lpm = rt_weather.nodes.node_thies_lpm:main',
            'node_wxt536 = rt_weather.nodes.node_wxt536:main',
        ],
    },
    # scripts=[
    #     'scripts/pwd10.py',
    #     'scripts/sr05.py',
    #     'scripts/thies_lpm.py',
    #     'scripts/wxt536.py',
    # ],
)
