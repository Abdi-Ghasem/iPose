# Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
# File Last Update Date : January 07, 2023

# Import dependencies
import os
import csv
import pickle
import struct
import liblzfse
import socketio
import numpy as np
import pandas as pd
from itertools import count
import matplotlib.pyplot as plt
import matplotlib.animation as animation


# Define a custom class for writing motion data in a csv file
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
    with open('motion.csv') as fp:
        for (nrows, _) in enumerate(fp, 1):
            pass

    # Extract motion data
    motion = pd.read_csv('motion.csv', skiprows=list(
        range(1, max((nrows-1)-125, 0))))
    idx = motion['idx']
    r_x, r_y, r_z = motion['r_x'], motion['r_y'], motion['r_z']
    a_x, a_y, a_z = motion['a_x'], motion['a_y'], motion['a_z']

    # Plot raw gyroscope
    axs[0][0].clear()
    axs[0][0].plot(idx, r_x, color='r', label='x')
    axs[0][0].plot(idx, r_y, color='g', label='y')
    axs[0][0].plot(idx, r_z, color='b', label='z')

    axs[0][0].grid()
    axs[0][0].set_xticklabels([])
    axs[0][0].tick_params(left=False)
    axs[0][0].tick_params(bottom=False)
    axs[0][0].set_ylim([-2.5*np.pi, 2.5*np.pi])
    axs[0][0].legend(loc='upper right')
    axs[0][0].set_title('Rotation Rate (rad/s)', loc='left')
    axs[0][0].set_xlim([max((nrows-1)-125, 0), (nrows-1)+125])

    # Plot raw accelerometer
    axs[1][0].clear()
    axs[1][0].plot(idx, a_x, color='r', label='x')
    axs[1][0].plot(idx, a_y, color='g', label='y')
    axs[1][0].plot(idx, a_z, color='b', label='z')

    axs[1][0].grid()
    axs[1][0].set_xticklabels([])
    axs[1][0].tick_params(left=False)
    axs[1][0].tick_params(bottom=False)
    axs[1][0].set_ylim([-np.pi/2.5, np.pi/2.5])
    axs[1][0].legend(loc='upper right')
    axs[1][0].set_title('Acceleration (m/s)', loc='left')
    axs[1][0].set_xlim([max((nrows-1)-125, 0), (nrows-1)+125])

    # Extract and plot depth map
    try:
        f = open('depth.pkl', 'rb')
        depth = pickle.load(f)
        f.close()

        axs[0][1].clear()
        axs[0][1].imshow(depth)
    except:
        pass

    axs[0][1].set_xticklabels([])
    axs[0][1].set_yticklabels([])
    axs[0][1].tick_params(left=False)
    axs[0][1].tick_params(bottom=False)
    axs[0][1].set_title('Depth Map (m)', loc='left')

    # Extract and plot visual image
    try:
        f = open('image.pkl', 'rb')
        image = pickle.load(f)
        f.close()

        axs[1][1].clear()
        axs[1][1].imshow(image)
    except:
        pass

    axs[1][1].set_xticklabels([])
    axs[1][1].set_yticklabels([])
    axs[1][1].tick_params(left=False)
    axs[1][1].tick_params(bottom=False)
    axs[1][1].set_title('Visual Image', loc='left')


# Create a socketio client
idx = count()
sio = socketio.Client()

# Initiate a figure for plotting RYANotics
fig, axs = plt.subplots(2, 2, figsize=(12, 8))
fig.canvas.manager.set_window_title('RYANotics')


# Remove whatever remains from the previous run
if os.path.isfile('motion.csv'):
    os.remove('motion.csv')
if os.path.isfile('depth.pkl'):
    os.remove('depth.pkl')
if os.path.isfile('image.pkl'):
    os.remove('image.pkl')

# Initiate a csv file for writing mottion data
writeCSV = write2csv('motion.csv', header=[
                     'idx', 'r_x', 'r_y', 'r_z', 'a_x', 'a_y', 'a_z'])


# Create socketio events
@sio.event
def connect():
    print('Connected to the Server ...')


@sio.event
def message(data):
    # Decompress data
    decompressed_data = liblzfse.decompress(data)

    # Decode the received data into RYANotics
    gyro = np.array(struct.unpack('ddd', decompressed_data[decompressed_data.find(
        b'gyro')+4:decompressed_data.find(b'accl')]), dtype=np.double)
    accl = np.array(struct.unpack('ddd', decompressed_data[decompressed_data.find(
        b'accl')+4:decompressed_data.find(b'dpth')]), dtype=np.double)
    writeCSV.update({'idx': next(idx), 'r_x': gyro[0], 'r_y': gyro[1],
                    'r_z': gyro[2], 'a_x': accl[0], 'a_y': accl[1], 'a_z': accl[2]})

    dpth = np.array(struct.unpack(49152*'f', decompressed_data[decompressed_data.find(
        b'dpth')+4:decompressed_data.find(b'visl')]), dtype=np.float32)
    dpth = np.rot90(dpth.reshape((192, 256)), k=-1)
    f = open('depth.pkl', 'wb')
    pickle.dump(dpth, f)
    f.close()

    visl = np.array(struct.unpack(49152*3*'B', decompressed_data[decompressed_data.find(
        b'visl')+4:decompressed_data.find(b'camp')]), dtype=np.uint8)
    visl = np.rot90(visl.reshape((192, 256, 3)), k=-1)
    f = open('image.pkl', 'wb')
    pickle.dump(visl, f)
    f.close()

    camp = np.array(struct.unpack('ffff', decompressed_data[decompressed_data.find(
        b'camp')+4:]), dtype=np.float32)


@sio.event
def disconnect():
    print('Disconnected from the Server ...')


# Connect to the server and animate real-time plotting
sio.connect('http://0.0.0.0:5000/')
ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
sio.wait()
