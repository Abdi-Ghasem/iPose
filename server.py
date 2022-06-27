# Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
# File Last Update Date : June 25, 2022

# Import dependencies
from flask import Flask
from flask_restful import reqparse
from flask_socketio import SocketIO, send

# Create a Flask instance
app = Flask(__name__)
socketio = SocketIO(app)

# Request parsing
iSensors_args = reqparse.RequestParser()
iSensors_args.add_argument('rawGyro', type=str, required=True, help='Transferring raw gyroscope data is mandatory!')
iSensors_args.add_argument('rawAccl', type=str, required=True, help='Transferring raw accelerometer data is mandatory!')
iSensors_args.add_argument('rawMagn', type=str, required=False)

iSensors_args.add_argument('processedGyro', type=str, required=False)
iSensors_args.add_argument('processedAccl', type=str, required=False)
iSensors_args.add_argument('processedMagn', type=str, required=False)

iSensors_args.add_argument('attitude', type=str, required=False)
iSensors_args.add_argument('quaternion', type=str, required=False)
iSensors_args.add_argument('gravityField', type=str, required=False)

iSensors_args.add_argument('location', type=str, required=False)

# Use the route() decorator to tell Flask what URL should trigger our function
@app.route('/', methods=['POST'])
def post():
    iSensors = iSensors_args.parse_args()
    send(iSensors, namespace='/', broadcast=True)
    return iSensors, 201

# Start the web server
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)