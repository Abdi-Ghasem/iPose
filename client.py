# Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
# File Last Update Date : June 25, 2022

# Import dependencies
import csv
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
        with open(self.filename,'a') as csvFile:
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
    m_x, m_y, m_z = iSensors['m_x'], iSensors['m_y'], iSensors['m_z']
    
    p_r_x, p_r_y, p_r_z = iSensors['p_r_x'], iSensors['p_r_y'], iSensors['p_r_z']
    p_a_x, p_a_y, p_a_z = iSensors['p_a_x'], iSensors['p_a_y'], iSensors['p_a_z']
    p_m_x, p_m_y, p_m_z = iSensors['p_m_x'], iSensors['p_m_y'], iSensors['p_m_z']
    
    p_r, p_p, p_y = iSensors['p_r'], iSensors['p_p'], iSensors['p_y']
    p_q_x, p_q_y, p_q_z, p_q_w = iSensors['p_q_x'], iSensors['p_q_y'], iSensors['p_q_z'], iSensors['p_q_w']
    p_g_x, p_g_y, p_g_z = iSensors['p_g_x'], iSensors['p_g_y'], iSensors['p_g_z']
    
    # Plot raw gyroscope
    axs[0].clear()
    axs[0].plot(idx, p_r_x, color='r', label='x')
    axs[0].plot(idx, p_r_y, color='g', label='y')
    axs[0].plot(idx, p_r_z, color='b', label='z')
    
    axs[0].grid()
    axs[0].set_xticklabels([])
    axs[0].set_ylim([-2.5*np.pi, 2.5*np.pi])
    axs[0].legend(loc='upper right')
    axs[0].set_title('Rotation Rate (rad/s)', loc='left')
    axs[0].set_xlim([max(len(idx)-125, 0), len(idx)+125])
    
    axs[1].clear()
    axs[1].plot(idx, p_a_x, color='r', label='x')
    axs[1].plot(idx, p_a_y, color='g', label='y')
    axs[1].plot(idx, p_a_z, color='b', label='z')
    
    axs[1].grid()
    axs[1].set_xticklabels([])
    axs[1].set_ylim([-np.pi/2.5, np.pi/2.5])
    axs[1].legend(loc='upper right')
    axs[1].set_title('Acceleration (m/s)', loc='left')
    axs[1].set_xlim([max(len(idx)-125, 0), len(idx)+125])
    
    axs[2].clear()
    axs[2].plot(idx, p_r, color='r', label='x')
    axs[2].plot(idx, p_p, color='g', label='y')
    axs[2].plot(idx, p_y, color='b', label='z')
    
    axs[2].grid()
    axs[2].set_xticklabels([])
    axs[2].set_ylim([-np.pi, np.pi])
    axs[2].legend(loc='upper right')
    axs[2].set_title('Euler Angles (rad)', loc='left')
    axs[2].set_xlim([max(len(idx)-125, 0), len(idx)+125])
    
    axs[3].clear()
    axs[3].plot(idx, p_g_x, color='r', label='x')
    axs[3].plot(idx, p_g_y, color='g', label='y')
    axs[3].plot(idx, p_g_z, color='b', label='z')
    
    axs[3].grid()
    axs[3].set_ylim([-np.pi/2, np.pi/2])
    axs[3].legend(loc='upper right')
    axs[3].set_title('Acceleration_Gravity (m/s2)', loc='left')
    axs[3].set_xlim([max(len(idx)-125, 0), len(idx)+125])
    
# Create a socketio client
idx = count()
sio = socketio.Client()

# Initiate a figure for plotting iSensors
fig, axs = plt.subplots(4, 1, figsize=(5, 7.5))
fig.canvas.manager.set_window_title('iSensors')

# Initiate a csv file for writing iSensors
writeCSV = write2csv('iSensors.csv', 
                     header=['idx', 'r_ts', 'r_x', 'r_y', 'r_z', 'a_ts', 'a_x', 'a_y', 'a_z', 'm_ts', 'm_x', 'm_y', 'm_z',
                             'p_ts', 'p_r_x', 'p_r_y', 'p_r_z', 'p_a_x', 'p_a_y', 'p_a_z', 'p_m_x', 'p_m_y', 'p_m_z',
                             'p_r', 'p_p', 'p_y', 'p_q_x', 'p_q_y', 'p_q_z', 'p_q_w', 'p_g_x', 'p_g_y', 'p_g_z',
                             'ts', 'lat', 'long', 'alt', 'h_acc', 'v_acc'])

# Create socketio events
@sio.event
def connect():
    print('user has connected to server!')

@sio.event
def message(iSensors):
    rawGyro = np.float_(iSensors['rawGyro'][1:-1].split(','))
    rawAccl = np.float_(iSensors['rawAccl'][1:-1].split(','))
    rawMagn = np.float_(iSensors['rawMagn'][1:-1].split(','))
    
    processedGyro = np.float_(iSensors['processedGyro'][1:-1].split(','))
    processedAccl = np.float_(iSensors['processedAccl'][1:-1].split(','))
    processedMagn = np.float_(iSensors['processedMagn'][1:-1].split(','))
    
    attitude = np.float_(iSensors['attitude'][1:-1].split(','))
    quaternion = np.float_(iSensors['quaternion'][1:-1].split(','))
    gravityField = np.float_(iSensors['gravityField'][1:-1].split(','))
    
    location = np.float_(iSensors['location'][1:-1].split(','))
    
    writeCSV.update(
        {
            'idx': next(idx), 
            'r_ts': rawGyro[0], 'r_x': rawGyro[1], 'r_y': rawGyro[2], 'r_z': rawGyro[3], 
            'a_ts': rawAccl[0], 'a_x': rawAccl[1], 'a_y': rawAccl[2], 'a_z': rawAccl[3], 
            'm_ts': rawMagn[0], 'm_x': rawMagn[1], 'm_y': rawMagn[2], 'm_z': rawMagn[3],
            
            'p_ts' : processedGyro[0], 
            'p_r_x': processedGyro[1], 'p_r_y': processedGyro[2], 'p_r_z': processedGyro[3], 
            'p_a_x': processedAccl[1], 'p_a_y': processedAccl[2], 'p_a_z': processedAccl[3], 
            'p_m_x': processedMagn[1], 'p_m_y': processedMagn[2], 'p_m_z': processedMagn[3],
            
            'p_r': attitude[1], 'p_p': attitude[2], 'p_y': attitude[3], 
            'p_q_x': quaternion[1], 'p_q_y': quaternion[2], 'p_q_z': quaternion[3], 'p_q_w': quaternion[4], 
            'p_g_x': gravityField[1], 'p_g_y': gravityField[2], 'p_g_z': gravityField[3],
            
            'ts': location[0], 'lat': location[1], 'long': location[2], 'alt': location[3], 'h_acc': location[4], 'v_acc': location[5]
        }
    )
    
@sio.event
def disconnect():
    print('user has disconnected from server!')

# Connect to the server and animate real-time plotting
sio.connect('http://192.168.1.23:5000/')
ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
sio.wait()