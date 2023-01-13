# Original Author       : Ghasem Abdi, ghasem.abdi@yahoo.com
# File Last Update Date : January 12, 2023

from flask import Flask, request
from flask_socketio import SocketIO, send

# Create a Flask instance
app = Flask(__name__)
socketio = SocketIO(app)


# Use the route() decorator to tell Flask what URL should trigger our function
@app.route('/', methods=['POST'])
def get_iphone_data():
    iphone_data = request.get_data()
    send(iphone_data, namespace='/', broadcast=True)
    return iphone_data, 201


# Start the web server
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
