# Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
# File Last Update Date : January 25, 2023


import struct
import liblzfse
import numpy as np
import open3d as o3d
import multiprocessing as mp
from flask import Flask, request


# Define a custom class for decoding iPhone data
class DecodeiPhoneData:
    def __init__(self, iphone_data: bytes):
        self.__w, self.__h, self.__c = 256, 192, 3
        self.iphone_data = liblzfse.decompress(iphone_data)

    def get_motion_sensor(self):
        gyro = np.array(struct.unpack('ddd', self.iphone_data[self.iphone_data.find(b'gyro')+4:self.iphone_data.find(b'accl')]), dtype=np.double)
        accl = np.array(struct.unpack('ddd', self.iphone_data[self.iphone_data.find(b'accl')+4:self.iphone_data.find(b'dpth')]), dtype=np.double)
        return np.hstack((gyro, accl))

    def get_depth_data(self):
        dpth = np.array(struct.unpack(self.__w*self.__h*'f', self.iphone_data[self.iphone_data.find(b'dpth')+4:self.iphone_data.find(b'visl')]), dtype=np.float32)
        dpth = np.rot90(dpth.reshape((self.__h, self.__w)), k=-1)
        return o3d.geometry.Image((np.asarray(dpth, order='C')).astype(np.float32))

    def get_image_data(self):
        visl = np.array(struct.unpack(self.__w*self.__h*self.__c*'B', self.iphone_data[self.iphone_data.find(b'visl')+4:self.iphone_data.find(b'camp')]), dtype=np.uint8)
        visl = np.rot90(visl.reshape((self.__h, self.__w, self.__c)), k=-1)
        return o3d.geometry.Image((np.asarray(visl, order='C')).astype(np.uint8))

    def get_camera_intrinsic_matrix(self):
        camp = np.array(struct.unpack('ffff', self.iphone_data[self.iphone_data.find(b'camp')+4:]), dtype=np.float32)
        return o3d.camera.PinholeCameraIntrinsic(self.__w, self.__h, camp[0], camp[1], camp[2], camp[3])

    def get_colored_point_clouds(self, extrinsic=np.eye(4), depth_trunc=5.0):
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(self.get_image_data(), self.get_depth_data(), depth_scale=1.0, depth_trunc=depth_trunc, convert_rgb_to_intensity=False)
        return o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, self.get_camera_intrinsic_matrix(), extrinsic=extrinsic)


def run_server(q, host='0.0.0.0', port=5000, debug=False):
    # Create a Flask instance
    app = Flask('RYANotics')

    # Use the route() decorator to tell Flask what URL should trigger our function
    @app.route('/', methods=['POST'])
    def get_iphone_data():
        iphone_data = request.get_data()
        q.put(iphone_data)
        return iphone_data, 201
        
    @app.route('/shutdown', methods=['POST'])
    def shutdown_server():
        q.put('quit')
        return '', 201
        
    # Start the web server
    app.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    q = mp.Queue()

    p = mp.Process(target=run_server, args=(q, '0.0.0.0', 5000, False))
    p.start()
    
    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name='RYANotics')
    
    while True:
        iphone_data = q.get()
        
        if iphone_data == 'quit':
            break

        try:
            pcd = DecodeiPhoneData(iphone_data).get_colored_point_clouds()
            pcd.transform([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]])

            vis.clear_geometries()
            vis.add_geometry(pcd)
            vis.poll_events()
            vis.update_renderer()

        except:
            print('RYANotics: DID NOT RECEIVE DATA FROM THE WEB SERVER ...')
    
    vis.destroy_window()
    p.terminate()
    