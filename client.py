# Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
# File Last Update Date : December 12, 2022

# Import dependencies
import csv
import struct
import liblzfse
import socketio
import numpy as np
import pandas as pd
from itertools import count
import matplotlib.pyplot as plt
import matplotlib.animation as animation


# Define a custom class for writing iSensors in a csv file
class write2csv():
    def __init__(self, filename, header):
        self.filename = filename
        self.header = header

        # Open a csv file for writing
        with open(self.filename, 'w') as csvFile:
            csvWriter = csv.DictWriter(csvFile, fieldnames=self.header)
            csvWriter.writeheader()

    def update(self, info):
        # Update the csv file
        with open(self.filename, 'a') as csvFile:
            csvWriter = csv.DictWriter(csvFile, fieldnames=self.header)
            csvWriter.writerow(info)


# Define a custom function for real-time plotting
def animate(i):
    # Read the csv file
    iSensors = pd.read_csv('iSensors.csv')

    # Extract iSensors
    idx = iSensors['idx']
    r_x, r_y, r_z = iSensors['r_x'], iSensors['r_y'], iSensors['r_z']
    a_x, a_y, a_z = iSensors['a_x'], iSensors['a_y'], iSensors['a_z']

    # Plot raw gyroscope
    axs[0].clear()
    axs[0].plot(idx, r_x, color='r', label='x')
    axs[0].plot(idx, r_y, color='g', label='y')
    axs[0].plot(idx, r_z, color='b', label='z')

    axs[0].grid()
    axs[0].set_xticklabels([])
    axs[0].set_ylim([-2.5*np.pi, 2.5*np.pi])
    axs[0].legend(loc='upper right')
    axs[0].set_title('Rotation Rate (rad/s)', loc='left')
    axs[0].set_xlim([max(len(idx)-125, 0), len(idx)+125])

    axs[1].clear()
    axs[1].plot(idx, a_x, color='r', label='x')
    axs[1].plot(idx, a_y, color='g', label='y')
    axs[1].plot(idx, a_z, color='b', label='z')

    axs[1].grid()
    axs[1].set_xticklabels([])
    axs[1].set_ylim([-np.pi/2.5, np.pi/2.5])
    axs[1].legend(loc='upper right')
    axs[1].set_title('Acceleration (m/s)', loc='left')
    axs[1].set_xlim([max(len(idx)-125, 0), len(idx)+125])


# Create a socketio client
idx = count()
sio = socketio.Client()

# Initiate a figure for plotting iSensors
fig, axs = plt.subplots(2, 1, figsize=(6, 8))
fig.canvas.manager.set_window_title('iSensors')

# Initiate a csv file for writing iSensors
writeCSV = write2csv('iSensors.csv', header=[
                     'idx', 'r_x', 'r_y', 'r_z', 'a_x', 'a_y', 'a_z'])


# Create socketio events
@sio.event
def connect():
    print('Connected to the Server ...')


@sio.event
def message(data):
    # Decompress data
    decompressed_data = liblzfse.decompress(data)

    # Decode the received data into iSensors
    gyro = np.array(struct.unpack('ddd', decompressed_data[decompressed_data.find(
        b'gyro')+4:decompressed_data.find(b'accl')]), dtype=np.double)
    accl = np.array(struct.unpack(
        'ddd', decompressed_data[decompressed_data.find(b'accl')+4:]), dtype=np.double)
    writeCSV.update({'idx': next(idx), 'r_x': gyro[0], 'r_y': gyro[1],
                    'r_z': gyro[2], 'a_x': accl[0], 'a_y': accl[1], 'a_z': accl[2]})


@sio.event
def disconnect():
    print('Disconnected from the Server ...')


# Connect to the server and animate real-time plotting
sio.connect('http://0.0.0.0:5000/')
ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
sio.wait()
