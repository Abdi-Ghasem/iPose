# Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
# File Last Update Date : January 25, 2023


import struct
import liblzfse
import argparse
import numpy as np
import open3d as o3d
import multiprocessing as mp
from flask import Flask, request


# Define a custom class for decoding iPhone data
class DecodeiPhoneData:
    """The class DecodeiPhoneData receives iphone_data as bytes and decompresses it followed by some functionalities for extracting motion, depth, visual, and colored point clouds data.
    """

    def __init__(self, iphone_data: bytes):
        """The function DecodeiPhoneData constructor receives iphone_data as bytes and decompresses it.

        Args:
            iphone_data (bytes): The iphone_data as bytes.
        """
        self.__w, self.__h, self.__c = 256, 192, 3
        self.iphone_data = liblzfse.decompress(iphone_data)

    def get_motion_sensor(self):
        """The function get_motion_sensor unpacks motion data from iphone_data bytes.

        Returns:
            motion data, returned as numpy.ndarray.
        """
        gyro = np.array(struct.unpack('ddd', self.iphone_data[self.iphone_data.find(
            b'gyro')+4:self.iphone_data.find(b'accl')]), dtype=np.double)
        accl = np.array(struct.unpack('ddd', self.iphone_data[self.iphone_data.find(
            b'accl')+4:self.iphone_data.find(b'dpth')]), dtype=np.double)
        return np.hstack((gyro, accl))

    def get_depth_data(self):
        """The function get_depth_data unpacks depth data from iphone_data bytes.

        Returns:
            depth data, returned as open3d.geometry.Image.
        """
        dpth = np.array(struct.unpack(self.__w*self.__h*'f', self.iphone_data[self.iphone_data.find(
            b'dpth')+4:self.iphone_data.find(b'visl')]), dtype=np.float32)
        dpth = np.rot90(dpth.reshape((self.__h, self.__w)), k=-1)
        return o3d.geometry.Image((np.asarray(dpth, order='C')).astype(np.float32))

    def get_image_data(self):
        """The function get_image_data unpacks visual data from iphone_data bytes.

        Returns:
            visual data, returned as open3d.geometry.Image.
        """
        visl = np.array(struct.unpack(self.__w*self.__h*self.__c*'B',
                        self.iphone_data[self.iphone_data.find(b'visl')+4:self.iphone_data.find(b'camp')]), dtype=np.uint8)
        visl = np.rot90(visl.reshape((self.__h, self.__w, self.__c)), k=-1)
        return o3d.geometry.Image((np.asarray(visl, order='C')).astype(np.uint8))

    def get_camera_intrinsic_matrix(self):
        """The function get_camera_intrinsic_matrix unpacks camera intrinsic data from iphone_data bytes.

        Returns:
            camera intrinsic matrix, returned as o3d.camera.PinholeCameraIntrinsic.
        """
        camp = np.array(struct.unpack(
            'ffff', self.iphone_data[self.iphone_data.find(b'camp')+4:]), dtype=np.float32)
        return o3d.camera.PinholeCameraIntrinsic(self.__w, self.__h, camp[0], camp[1], camp[2], camp[3])

    def get_colored_point_clouds(self, extrinsic=np.eye(4), depth_trunc=3.0):
        """The function get_colored_point_clouds generates colored point clouds based on iphone_data bytes.

        Args:
            extrinsic (numpy.ndarray, optional): exterior orientation to be applied over colored point clouds. Defaults to np.eye(4).
            depth_trunc (float, optional): depth truncation threshold. Defaults to 5.0.

        Returns:
            colored point clouds: returned as o3d.geometry.PointCloud.
        """
        rgbd = o3d.geometry.RGBDImage.create_from_color_and_depth(self.get_image_data(
        ), self.get_depth_data(), depth_scale=1.0, depth_trunc=depth_trunc, convert_rgb_to_intensity=False)
        return o3d.geometry.PointCloud.create_from_rgbd_image(rgbd, self.get_camera_intrinsic_matrix(), extrinsic=extrinsic)


def run_server(q, host='0.0.0.0', port=5000):
    """The function run_server creates a web server to be posted iphone_data on. 

    Args:
        q (multiprocessing.queues.Queue): queue object.
        host (str, optional): address the development server listens to. Defaults to '0.0.0.0'.
        port (int, optional): network protocol that receives or transmits communication. Defaults to 5000.
    """
    # Create a Flask instance
    app = Flask('RYANotics')

    # Use the route() decorator to tell Flask what URL should trigger our function
    @app.route('/', methods=['POST'])
    def get_iphone_data():
        """The function get_iphone_data receives iphone_data and puts it in a queue.
        """
        iphone_data = request.get_data()
        q.put(iphone_data)
        return iphone_data, 201

    @app.route('/shutdown', methods=['POST'])
    def shutdown_server():
        """The function shutdown_server puts a quit order in the queue.
        """
        q.put('quit')
        return '', 201

    # Start the web server
    app.run(host=host, port=port)


if __name__ == '__main__':
    # Extract command line arguments (or set default values)
    argParser = argparse.ArgumentParser()
    argParser.add_argument('-o', '--host', type=str,
                           help='address the development server listens to.')
    argParser.add_argument('-p', '--port', type=int,
                           help='network protocol that receives or transmits communication.')
    argParser.add_argument('-t', '--threshold', type=float,
                           help='depth truncation threshold.')

    args = argParser.parse_args()
    host = args.host if args.host else '0.0.0.0'
    port = args.port if args.port else 5000
    depth_trunc = args.threshold if args.threshold else 5.0

    # Create a queue object
    q = mp.Queue()

    # Start a web server on a thread
    p = mp.Process(target=run_server, args=(q, host, port))
    p.start()

    # Create a window for plotting colored point clouds
    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name='RYANotics')

    # A loop to receives iphone_data from the queue
    while True:
        # Get iphone_data from the queue
        iphone_data = q.get()

        # Check if needs to break the loop
        if iphone_data == 'quit':
            break

        # Try to decode iphone_data and generates colored point clouds followed by updating the plotting window
        try:
            pcd = DecodeiPhoneData(iphone_data).get_colored_point_clouds(
                depth_trunc=depth_trunc)
            pcd.transform([[1, 0, 0, 0], [0, -1, 0, 0],
                          [0, 0, -1, 0], [0, 0, 0, 1]])

            vis.clear_geometries()
            vis.add_geometry(pcd)
            vis.poll_events()
            vis.update_renderer()

        except:
            print('RYANotics: DID NOT RECEIVE FULL DATA FROM THE WEB SERVER ...')

    # Destroy the plotting window
    vis.destroy_window()

    # terminate the web server process
    p.terminate()
