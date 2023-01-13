# Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
# File Last Update Date : January 12, 2023

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


# Define a custom class for decoding iPhone data
class DecodeiPhoneData:
    def __init__(self, iphone_data: bytes):
        self.iphone_data = liblzfse.decompress(iphone_data)

    def get_motion_sensor(self):
        gyro = np.array(struct.unpack('ddd', self.iphone_data[self.iphone_data.find(
            b'gyro')+4:self.iphone_data.find(b'accl')]), dtype=np.double)
        accl = np.array(struct.unpack('ddd', self.iphone_data[self.iphone_data.find(
            b'accl')+4:self.iphone_data.find(b'dpth')]), dtype=np.double)
        return np.hstack((gyro, accl))

    def get_depth_data(self):
        w, h = 256, 192
        dpth = np.array(struct.unpack(w*h*'f', self.iphone_data[self.iphone_data.find(
            b'dpth')+4:self.iphone_data.find(b'visl')]), dtype=np.float32)
        return np.rot90(dpth.reshape((h, w)), k=-1)

    def get_image_data(self):
        w, h, c = 256, 192, 3
        visl = np.array(struct.unpack(w*h*c*'B', self.iphone_data[self.iphone_data.find(
            b'visl')+4:self.iphone_data.find(b'camp')]), dtype=np.uint8)
        return np.rot90(visl.reshape((h, w, c)), k=-1)

    def get_camera_intrinsic_matrix(self):
        camp = np.array(struct.unpack(
            'ffff', self.iphone_data[self.iphone_data.find(b'camp')+4:]), dtype=np.float32)
        return np.array([[camp[0], 0, camp[2]], [0, camp[1], camp[3]], [0, 0, 1]])


# Define a custom function for writing pkl file
def write2pkl(filename, file):
    f = open(filename, 'wb')
    pickle.dump(file, f)
    f.close()


# Define a custom function for reading pkl file
def read_pkl(filename):
    f = open(filename, 'rb')
    file = pickle.load(f)
    f.close()
    return file


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
        depth = read_pkl('depth.pkl')

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
        image = read_pkl('image.pkl')

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
def message(iphone_data):
    decoder = DecodeiPhoneData(iphone_data)

    # Decode the received data into RYANotics
    motion = decoder.get_motion_sensor()
    writeCSV.update({'idx': next(idx), 'r_x': motion[0], 'r_y': motion[1],
                    'r_z': motion[2], 'a_x': motion[3], 'a_y': motion[4], 'a_z': motion[5]})

    dpth = decoder.get_depth_data()
    write2pkl('depth.pkl', dpth)

    visl = decoder.get_image_data()
    write2pkl('image.pkl', visl)

    camp = decoder.get_camera_intrinsic_matrix()


@sio.event
def disconnect():
    print('Disconnected from the Server ...')


# Connect to the server and animate real-time plotting
sio.connect('http://0.0.0.0:5000/')
ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
sio.wait()
