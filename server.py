# Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
# File Last Update Date : November 24, 2022

from flask import Flask
from flask_restful import reqparse
from flask_socketio import SocketIO, send

# Create a Flask instance
app = Flask(__name__)
socketio = SocketIO(app)

# Request parsing
iSensors_args = reqparse.RequestParser()
iSensors_args.add_argument('gyroData', type=float, action='append',
                           required=True, help='gyro_data cannot be blank!')
iSensors_args.add_argument('acclData', type=float, action='append',
                           required=True, help='accl_data cannot be blank!')


# Use the route() decorator to tell Flask what URL should trigger our function
@app.route('/', methods=['POST'])
def post():
    iSensors = iSensors_args.parse_args()
    send(iSensors, namespace='/', broadcast=True)
    return iSensors, 201


# Start the web server
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
