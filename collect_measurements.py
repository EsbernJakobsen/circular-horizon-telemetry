import sys
import time
import datetime
sys.path.append('/home/pi/CH_Telemetry/DFRobot_I2C_Multiplexer/raspberrypi')
sys.path.append('/home/pi/CH_Telemetry/DFRobot_MAX31855/raspberrypi/python')
sys.path.append('/home/pi/CH_Telemetry/DFRobot_MPX5700/python/raspberrypi')
import DFRobot_I2C_Multiplexer
from DFRobot_MAX31855 import *
from DFROBOT_MPX5700 import *
from mcp9600 import MCP9600
from influxdb import InfluxDBClient


############################################################################################################

# Define Sensor class.

class Sensor:

    def __init__(self, system: str, location: str, multiplexer_port: int, sensor_type: str):
        self.system = system
        self.location = location
        self.multiplexer_port = multiplexer_port
        self.sensor_type = sensor_type

    def select_port(self):
        multiplexer.select_port(self.multiplexer_port)

    def take_measurement(self):
        if self.sensor_type == 'temp_digital':
            return temp_sensor.read_celsius()

        elif self.sensor_type == 'temp_thermocouple':
            return thermocouple.get_hot_junction_temperature()

        elif self.sensor_type == 'pressure_digital':
            pressure_sensor.calibration_kpa(101.3)  # Calibrate pressure sensor to atmospheric pressure
            pressure_sensor.set_mean_sample_size(5)  # Set up sample size
            return pressure_sensor.get_pressure_value_kpa(1)

############################################################################################################

# Define function to log the data to InfluxDB
def send_to_influxdb(system, location, timestamp, measurement):
    """Function to send measured data to be logged on InfluxDB."""
    payload = [
        {"measurement": system,
         "tags": {
             "Location": location,
         },
         "time": timestamp,
         "fields": {
             "Temperature": measurement
         }
         }
    ]
    client.write_points(payload)

############################################################################################################

# Define function to print out sensors connected to the multiplexer. Useful to see if RPi is seeing them or not!
def scan_multiplexer(i2c_multi_addr):
    """Simple function to scan a multiplexer connected to the RPi, and print out what type of sensors are connected and at which ports.
    Input is the multiplexer I2C address. This defaults to 0x70, but is changeable up to 0x77."""

    # Create multiplexer object
    I2CMulti = DFRobot_I2C_Multiplexer.DFRobot_I2C_Multiplexer(i2c_multi_addr)

    # Scan i2c devices of each port.
    for port in range(0, 8):  # Scan i2C devices of each port
        id = I2CMulti.scan(port)

        if id == [16]:
            sensor = 'Digital temperature sensor'
            print(f'Port {port}: {sensor}')
        elif id == [22]:
            sensor = 'Digital pressure sensor'
            print(f'Port {port}: {sensor}')
        elif id == [102]:
            sensor = 'Analogue temperature thermocouple'
            print(f'Port {port}: {sensor}')
        elif not id:
            sensor = 'No sensor'
            print(f'Port {port}: {sensor}')


############################################################################################################

# Set up InfluxDB
host = '192.168.0.166'  # Change this as necessary
port = 8086
username = 'CH_Horizon'  # Change this as necessary
password = 'RaspberryChar'  # Change this as necessary
db = 'CH_Telemetry_Data'  # Change this as necessary

# InfluxDB client to write to
client = InfluxDBClient(host, port, username, password, db)

############################################################################################################

# INITIATE MULTIPLEXER
multiplexer = DFRobot_I2C_Multiplexer.DFRobot_I2C_Multiplexer(0x70)  # Default multiplexer i2c address is 0x70. Changeable up to 0x70.
# scan_multiplexer(0x70)  # Run this to see what sensors are connected

############################################################################################################

# INITIATE SENSOR OBJECTS:
# Amplifier for thermocouple
thermocouple = MCP9600(i2c_addr=0x66)  # Default i2c address of amplifier is 0x66.
thermocouple.set_thermocouple_type('N')  # Set thermocouple type as 'N'
# Digital temperature sensor. All the temperature sensors use the same I2C address, so we just select them individually later in the for loop.
temp_sensor = DFRobot_MAX31855(0x01, 0x10)
# Digital pressure sensor object. Pressure sensor default I2C address is 0x16.
pressure_sensor = DFRobot_MPX5700_I2C(0x01, 0x16)

############################################################################################################

# CREATE OBJECT INSTANCES OF ALL CONNECTED SENSORS (with multiplexer ports included):
# N.B. this is where you can add/remove sensors !!!

connected_sensors = [Sensor('Reactor', 'reactor_bottom', multiplexer_port=0, sensor_type='temp_digital'),
                     Sensor('Reactor', 'reactor_middle', multiplexer_port=1, sensor_type='temp_digital'),
                     Sensor('Reactor', 'reactor_top', multiplexer_port=2, sensor_type='temp_digital'),
                     Sensor('Condenser', 'condenser_exit', multiplexer_port=4, sensor_type='temp_digital'),
                     Sensor('Reactor', 'exhaust', multiplexer_port=6, sensor_type='temp_thermocouple'),
                     Sensor('Cyclone filter', 'cyclone_inlet', multiplexer_port=7, sensor_type='temp_thermocouple')]

############################################################################################################

# Define duration of data collection.
program_duration = float(input('Enter (in minutes) how long you would like to collect data for.'))

# Start data collection.
start_time = time.time()
end_time = time.time()
while True:
    print(f'Collecting sensor information. Elapsed time: {int(end_time - start_time)} seconds.')
    for sensor in connected_sensors:
        sensor.select_port()  # Select multiplexer port to communicate with.
        timestamp = datetime.datetime.utcnow()  # Take timestamp
        measurement = sensor.take_measurement()  # Take measurement
        send_to_influxdb(sensor.system, sensor.location, timestamp, measurement)  # Send to influxdb

    time.sleep(4)  # Change the interval between logging of data points here
    end_time = time.time()

    if ((end_time - start_time) / 60) > program_duration:
        print('Run finished. Ending data collection.')
        break

# For troubleshooting sensor connections, run the below line to see what RPi is seeing.
scan_multiplexer(0x70)