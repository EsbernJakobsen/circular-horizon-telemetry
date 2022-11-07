import time
import sys
import os
sys.path.append('/home/pi/CH_Telemetry/DFRobot_I2C_Multiplexer/raspberrypi')


# Logs the data to your InfluxDB
def send_to_influxdb(system, location, timestamp, temperature):
    """Function to send measured data to be logged on InfluxDB."""
    payload = [
         {"measurement": system,
             "tags": {
                 "Location": location,
              },
              "time": timestamp,
              "fields": {
                  "Temperature" : temperature
              }
          }
        ]
    client.write_points(payload)



def scan_multiplexer(i2c_multi_addr):
    """Simple function to scan a multiplexer connected to the RPi, and print out what type of sensors are connected and at which ports.
    Input is the multiplexer I2C address. This defaults to 0x70, but is changeable up to 0x77."""

    # Create multiplexer object
    I2CMulti = DFRobot_I2C_Multiplexer.DFRobot_I2C_Multiplexer(i2c_multi_addr)

    # Scan i2c devices of each port.
    for port in range(0, 8):   #Scan i2C devices of each port
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

