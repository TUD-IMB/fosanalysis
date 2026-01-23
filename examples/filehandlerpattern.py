r"""
This script shows how to use the file handler to read ODiSI data files.
For .dat files all channels can be read.
A .tsv file is also supported.

\author Anett Kielreiter
\date 2024
"""

import typing

from fosanalysis.datahandling.filehandler import FileHandler
from fosanalysis.datahandling.filereader import SensorInfo

filepath = "data/demofile.dat" # Path to .dat or .tsv file

handler = FileHandler(filepath)
testname = handler.metadata.get('test name', '')

# Get all data of sensors in the measurement file
for sensor in handler.sensors:
    sensor = typing.cast(SensorInfo, sensor) 
    sensor_name = sensor.name
    serial_number = sensor.serial_number
    gages = sensor.gages
    segments = sensor.segments

    # get all data
    times, data = handler.get_measurements(sensor.channel)
    x_axis = data['All']['x_axis']
    tare = data['All']['tare']
    strain = data['All']['strain']

    # get all data of all gages
    gage_names = list(gages.keys())
    times, data = handler.get_measurements(sensor.channel, 
                                           segments_gages=gage_names)
    for name in gage_names:
        x_axis = data[name]['x_axis']
        tare = data[name]['tare']
        strain = data[name]['strain'] 

# Get all data of known channel
times, data = handler.get_measurements(channel=2)
x_axis = data['All']['x_axis']
tare = data['All']['tare']
strain = data['All']['strain']

# If it is a huge file use the generator
for timestamps, strain in handler.yield_measurements_in_chunks(10000, 
                                                               channel=1):
    # process timestamps and strain, e.g. write to database in chunks
    print(len(timestamps))

handler.close_file()

